'use strict';

const { createHash } = require('crypto');

const {
  readRecentNetworkEntries,
  sessionNetworkDurationKey,
  sessionNetworkEndpointCountsKey,
  sessionNetworkEndpointMembersKey,
  sessionNetworkEndpointMetaKey,
  sessionNetworkFieldIndexKey,
  sessionNetworkRecentKey,
  sessionNetworkRecordsKey,
  sessionNetworkStatsKey,
  sessionNetworkSummariesKey,
  withRedis,
} = require('./datasets');

function safeParseUrl(rawUrl) {
  try {
    return new URL(String(rawUrl || '').trim());
  } catch {
    return null;
  }
}

function normalizeMimeType(value) {
  return String(value || '')
    .split(';', 1)[0]
    .trim()
    .toLowerCase();
}

function stringifyBody(value) {
  if (value == null)
    return '';
  if (typeof value === 'string')
    return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function summarizeText(text, maxLength = 240) {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim();
  if (normalized.length <= maxLength)
    return normalized;
  return `${normalized.slice(0, maxLength)}...`;
}

function normalizePathPattern(pathname) {
  const segments = String(pathname || '')
    .split('/')
    .filter(Boolean)
    .map(segment => {
      if (/^\d+$/.test(segment))
        return ':id';
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(segment))
        return ':uuid';
      if (/^[0-9a-f]{16,}$/i.test(segment))
        return ':hex';
      if (/^[A-Za-z0-9_-]{24,}$/.test(segment))
        return ':token';
      return segment;
    });
  return `/${segments.join('/')}`;
}

function collectObjectKeys(value, collector, prefix) {
  if (!value || typeof value !== 'object')
    return;
  if (Array.isArray(value)) {
    for (const item of value)
      collectObjectKeys(item, collector, prefix);
    return;
  }
  for (const [key, nested] of Object.entries(value)) {
    const current = prefix ? `${prefix}.${key}` : key;
    collector.add(current);
    collectObjectKeys(nested, collector, current);
  }
}

function normalizeUniqueLower(values) {
  return Array.from(new Set(
    Array.from(values || [])
      .map(value => String(value || '').trim().toLowerCase())
      .filter(Boolean),
  )).sort();
}

function bodyKeySet(bodyText, contentType) {
  const keys = new Set();
  const text = String(bodyText || '').trim();
  if (!text)
    return [];

  const lowerContentType = String(contentType || '').toLowerCase();
  if (lowerContentType.includes('application/json') || text.startsWith('{') || text.startsWith('[')) {
    try {
      const parsed = JSON.parse(text);
      collectObjectKeys(parsed, keys, '');
      return normalizeUniqueLower(keys);
    } catch {
      return [];
    }
  }

  if (lowerContentType.includes('application/x-www-form-urlencoded')) {
    const params = new URLSearchParams(text);
    return normalizeUniqueLower(params.keys());
  }

  return [];
}

function tokenizeValue(value) {
  return String(value || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function parseJsonValue(value, fallback) {
  if (!value)
    return fallback;
  try {
    const parsed = JSON.parse(value);
    return parsed == null ? fallback : parsed;
  } catch {
    return fallback;
  }
}

function toFrequencyMapFromHash(hash, limit = 20, valueParser = value => Number(value) || 0) {
  return Object.entries(hash || {})
    .map(([value, count]) => ({ value, count: valueParser(count) }))
    .sort((left, right) => right.count - left.count || left.value.localeCompare(right.value))
    .slice(0, limit);
}

function hashText(value) {
  const text = String(value || '');
  if (!text)
    return '';
  return createHash('sha1').update(text).digest('hex');
}

function hashKeyList(values) {
  const normalized = normalizeUniqueLower(values);
  if (!normalized.length)
    return '';
  return hashText(normalized.join('\n'));
}

function collectMatchedSignals(values, patterns) {
  const matched = new Set();
  const normalizedValues = Array.from(values || [])
    .map(value => String(value || '').trim().toLowerCase())
    .filter(Boolean);

  for (const value of normalizedValues) {
    const tokens = new Set(tokenizeValue(value));
    for (const pattern of patterns || []) {
      const normalizedPattern = String(pattern || '').trim().toLowerCase();
      if (!normalizedPattern)
        continue;
      if (value.includes(normalizedPattern) || tokens.has(normalizedPattern))
        matched.add(normalizedPattern);
    }
  }

  return Array.from(matched).sort();
}

function buildAuthSignals(input) {
  return collectMatchedSignals(
    [
      ...(input.headerKeys || []),
      ...(input.queryKeys || []),
      ...(input.requestBodyKeys || []),
      ...(input.responseBodyKeys || []),
      input.url,
      input.path,
    ],
    ['authorization', 'cookie', 'set-cookie', 'token', 'nonce', 'sign', 'signature', 'timestamp', 'session', 'jwt', 'bearer'],
  );
}

function buildInteractionSignals(input) {
  const matched = collectMatchedSignals(
    [
      input.method,
      input.url,
      input.path,
      ...(input.requestBodyKeys || []),
      ...(input.responseBodyKeys || []),
    ],
    ['login', 'auth', 'checkout', 'order', 'submit', 'create', 'update', 'donate', 'payment', 'confirm', 'graphql', 'mutation'],
  );
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(input.method || '').toUpperCase()))
    matched.unshift('write_method');
  return Array.from(new Set(matched)).sort();
}

function buildErrorSignals(input) {
  const matched = new Set();
  const status = Number(input.status || 0);
  if (status === 401)
    matched.add('unauthorized');
  if (status === 403)
    matched.add('forbidden');
  if (status === 419)
    matched.add('csrf_or_session');
  if (status === 422)
    matched.add('validation');
  if (status >= 500)
    matched.add('server_error');
  for (const item of collectMatchedSignals(
    [...(input.responseBodyKeys || []), input.responseBodyPreview],
    ['error', 'errors', 'message', 'exception', 'declined', 'invalid', 'failed'],
  )) {
    matched.add(item);
  }
  return Array.from(matched).sort();
}

function topFrequencyFromItems(items, limit = 10) {
  const counts = new Map();
  for (const item of items || []) {
    const normalized = String(item || '').trim();
    if (!normalized)
      continue;
    counts.set(normalized, Number(counts.get(normalized) || 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((left, right) => right.count - left.count || left.value.localeCompare(right.value))
    .slice(0, limit);
}

function pickHeaderValues(headers = {}) {
  const whitelist = ['content-type', 'accept', 'origin', 'referer', 'x-requested-with', 'x-csrf-token'];
  const picked = {};
  for (const key of whitelist) {
    const value = headers[key];
    if (value == null || value === '')
      continue;
    picked[key] = value;
  }
  return picked;
}

function enrichEntry(entry) {
  const request = entry?.request || {};
  const response = entry?.response || {};
  const requestUrl = String(request.url || '').trim();
  const parsedUrl = safeParseUrl(requestUrl);
  const mimeType = normalizeMimeType(response.mimeType || response.headers?.['content-type']);
  const requestBody = stringifyBody(request.body);
  const responseBody = stringifyBody(response.body);
  const requestHeaders = request.headers || {};
  const responseHeaders = response.headers || {};
  const requestContentType = normalizeMimeType(requestHeaders['content-type']);
  const requestBodyPreview = summarizeText(requestBody, 120);
  const responseBodyPreview = summarizeText(responseBody, 120);
  const requestBodyKeys = bodyKeySet(requestBody, requestContentType);
  const responseBodyKeys = bodyKeySet(responseBody, mimeType);
  const requestHeaderKeys = normalizeUniqueLower(Object.keys(requestHeaders));
  const responseHeaderKeys = normalizeUniqueLower(Object.keys(responseHeaders));
  const headerKeys = normalizeUniqueLower([...Object.keys(requestHeaders), ...Object.keys(responseHeaders)]);
  const requestBodySize = Number(request.bodySize || Buffer.byteLength(requestBody, 'utf8') || 0);
  const responseBodySize = Number(response.bodySize || Buffer.byteLength(responseBody, 'utf8') || 0);

  return {
    id: String(entry?.id || '').trim(),
    timestamp: String(entry?.timestamp || '').trim(),
    method: String(request.method || '').toUpperCase(),
    url: requestUrl,
    host: parsedUrl ? parsedUrl.hostname.toLowerCase() : '',
    path: parsedUrl ? parsedUrl.pathname : '',
    normalized_path: normalizePathPattern(parsedUrl ? parsedUrl.pathname : ''),
    query: parsedUrl ? parsedUrl.search : '',
    query_keys: parsedUrl ? normalizeUniqueLower(parsedUrl.searchParams.keys()) : [],
    status: Number(response.status || 0),
    status_text: String(response.statusText || ''),
    mime_type: mimeType,
    duration: Number(entry?.timing?.duration || 0),
    request_headers: requestHeaders,
    response_headers: responseHeaders,
    request_body: requestBody,
    response_body: responseBody,
    request_body_truncated: Boolean(request.bodyTruncated),
    response_body_truncated: Boolean(response.bodyTruncated),
    request_header_keys: requestHeaderKeys,
    response_header_keys: responseHeaderKeys,
    header_keys: headerKeys,
    request_body_keys: requestBodyKeys,
    response_body_keys: responseBodyKeys,
    request_body_size: requestBodySize,
    response_body_size: responseBodySize,
    request_body_hash: hashText(requestBody),
    response_body_hash: hashText(responseBody),
    request_schema_hash: hashKeyList(requestBodyKeys),
    response_schema_hash: hashKeyList(responseBodyKeys),
    auth_signal_flags: buildAuthSignals({
      headerKeys,
      queryKeys: parsedUrl ? normalizeUniqueLower(parsedUrl.searchParams.keys()) : [],
      requestBodyKeys,
      responseBodyKeys,
      url: requestUrl,
      path: parsedUrl ? parsedUrl.pathname : '',
    }),
    interaction_signal_flags: buildInteractionSignals({
      method: String(request.method || '').toUpperCase(),
      url: requestUrl,
      path: parsedUrl ? parsedUrl.pathname : '',
      requestBodyKeys,
      responseBodyKeys,
    }),
    error_signal_flags: buildErrorSignals({
      status: Number(response.status || 0),
      responseBodyKeys,
      responseBodyPreview,
    }),
    request_body_preview: requestBodyPreview,
    response_body_preview: responseBodyPreview,
  };
}

function summarizeEntry(entry) {
  const normalized = normalizeSummary(entry);
  return {
    id: normalized.id,
    timestamp: normalized.timestamp,
    method: normalized.method,
    url: normalized.url,
    host: normalized.host,
    path: normalized.path,
    status: normalized.status,
    mime_type: normalized.mime_type,
    duration: normalized.duration,
    request_body_size: normalized.request_body_size,
    response_body_size: normalized.response_body_size,
    request_schema_hash: normalized.request_schema_hash,
    response_schema_hash: normalized.response_schema_hash,
    auth_signal_flags: normalized.auth_signal_flags,
    interaction_signal_flags: normalized.interaction_signal_flags,
    error_signal_flags: normalized.error_signal_flags,
    request_body_preview: normalized.request_body_preview || summarizeText(normalized.request_body, 120),
    response_body_preview: normalized.response_body_preview || summarizeText(normalized.response_body, 120),
  };
}

function normalizeSummary(summary = {}) {
  return {
    ...summary,
    query_keys: normalizeUniqueLower(summary.query_keys || []),
    request_header_keys: normalizeUniqueLower(summary.request_header_keys || []),
    response_header_keys: normalizeUniqueLower(summary.response_header_keys || []),
    header_keys: normalizeUniqueLower(summary.header_keys || []),
    request_body_keys: normalizeUniqueLower(summary.request_body_keys || []),
    response_body_keys: normalizeUniqueLower(summary.response_body_keys || []),
    request_body_size: Number(summary.request_body_size || 0),
    response_body_size: Number(summary.response_body_size || 0),
    request_body_hash: String(summary.request_body_hash || ''),
    response_body_hash: String(summary.response_body_hash || ''),
    request_schema_hash: String(summary.request_schema_hash || hashKeyList(summary.request_body_keys || [])),
    response_schema_hash: String(summary.response_schema_hash || hashKeyList(summary.response_body_keys || [])),
    auth_signal_flags: normalizeUniqueLower(summary.auth_signal_flags || []),
    interaction_signal_flags: normalizeUniqueLower(summary.interaction_signal_flags || []),
    error_signal_flags: normalizeUniqueLower(summary.error_signal_flags || []),
  };
}

function normalizeSearchString(value) {
  return String(value || '').trim().toLowerCase();
}

function matchesFieldSearch(keys, searchText) {
  const query = normalizeSearchString(searchText);
  if (!query)
    return true;

  const normalizedKeys = normalizeUniqueLower(keys || []);
  if (normalizedKeys.some(key => key.includes(query)))
    return true;

  const searchTokens = tokenizeValue(query);
  if (!searchTokens.length)
    return false;

  return normalizedKeys.some(key => {
    const tokenSet = new Set(tokenizeValue(key));
    return searchTokens.every(token => tokenSet.has(token) || key.includes(token));
  });
}

function matchesSummaryFilters(summary, params = {}) {
  const urlContains = normalizeSearchString(params.url_contains);
  const host = normalizeSearchString(params.host);
  const pathContains = normalizeSearchString(params.path_contains);
  const method = normalizeSearchString(params.method).toUpperCase();
  const mimeTypeContains = normalizeSearchString(params.mime_type_contains);
  const requestBodySearch = normalizeSearchString(params.request_body_search);
  const responseBodySearch = normalizeSearchString(params.response_body_search);
  const headerSearch = normalizeSearchString(params.header_search);
  const queryKeySearch = normalizeSearchString(params.query_key_search);
  const statusCode = params.status_code == null ? null : Number(params.status_code);

  if (urlContains && !String(summary.url || '').toLowerCase().includes(urlContains))
    return false;
  if (host && String(summary.host || '').toLowerCase() !== host)
    return false;
  if (pathContains && !String(summary.path || '').toLowerCase().includes(pathContains))
    return false;
  if (method && String(summary.method || '').toUpperCase() !== method)
    return false;
  if (Number.isFinite(statusCode) && Number(summary.status || 0) !== statusCode)
    return false;
  if (mimeTypeContains && !String(summary.mime_type || '').toLowerCase().includes(mimeTypeContains))
    return false;
  if (!matchesFieldSearch(summary.query_keys, queryKeySearch))
    return false;
  if (!matchesFieldSearch(summary.request_body_keys, requestBodySearch))
    return false;
  if (!matchesFieldSearch(summary.response_body_keys, responseBodySearch))
    return false;
  if (!matchesFieldSearch(summary.header_keys, headerSearch))
    return false;
  return true;
}

function isLikelyApiRequest(entry) {
  const lowerPath = String(entry.path || '').toLowerCase();
  const lowerMimeType = String(entry.mime_type || '').toLowerCase();
  const lowerUrl = String(entry.url || '').toLowerCase();

  return (
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(entry.method || '').toUpperCase())
    || lowerMimeType.includes('json')
    || lowerPath.includes('/api')
    || lowerPath.includes('/graphql')
    || lowerPath.includes('/ajax')
    || lowerPath.includes('/rest')
    || lowerUrl.includes('admin-ajax')
  );
}

function endpointIdFromSummary(summary) {
  return `${summary.method} ${summary.host}${summary.normalized_path}`;
}

function normalizeDetailLevel(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (['schema', 'preview', 'full'].includes(normalized))
    return normalized;
  return 'schema';
}

function reduceEntryByDetailLevel(entry, detailLevel) {
  const normalized = normalizeSummary(entry);
  const schemaPayload = {
    id: normalized.id,
    timestamp: normalized.timestamp,
    method: normalized.method,
    url: normalized.url,
    host: normalized.host,
    path: normalized.path,
    normalized_path: normalized.normalized_path,
    query_keys: normalized.query_keys,
    status: normalized.status,
    status_text: normalized.status_text,
    mime_type: normalized.mime_type,
    duration: normalized.duration,
    request_header_keys: normalized.request_header_keys,
    response_header_keys: normalized.response_header_keys,
    header_keys: normalized.header_keys,
    request_body_keys: normalized.request_body_keys,
    response_body_keys: normalized.response_body_keys,
    request_body_size: normalized.request_body_size,
    response_body_size: normalized.response_body_size,
    request_body_hash: normalized.request_body_hash,
    response_body_hash: normalized.response_body_hash,
    request_schema_hash: normalized.request_schema_hash,
    response_schema_hash: normalized.response_schema_hash,
    auth_signal_flags: normalized.auth_signal_flags,
    interaction_signal_flags: normalized.interaction_signal_flags,
    error_signal_flags: normalized.error_signal_flags,
    request_body_truncated: Boolean(normalized.request_body_truncated),
    response_body_truncated: Boolean(normalized.response_body_truncated),
  };

  if (detailLevel === 'schema')
    return schemaPayload;

  const previewPayload = {
    ...schemaPayload,
    request_header_values: pickHeaderValues(normalized.request_headers || {}),
    response_header_values: pickHeaderValues(normalized.response_headers || {}),
    request_body_preview: normalized.request_body_preview,
    response_body_preview: normalized.response_body_preview,
  };
  if (detailLevel === 'preview')
    return previewPayload;

  return {
    ...previewPayload,
    request_headers: normalized.request_headers || {},
    response_headers: normalized.response_headers || {},
    request_body: normalized.request_body || '',
    response_body: normalized.response_body || '',
  };
}

function summarizeEndpointGroup(endpointId, summaries = []) {
  const normalized = summaries.map(normalizeSummary);
  const sample = normalized[0] || {};
  const allQueryKeys = normalized.flatMap(item => item.query_keys || []);
  const allRequestKeys = normalized.flatMap(item => item.request_body_keys || []);
  const allResponseKeys = normalized.flatMap(item => item.response_body_keys || []);
  const allHeaderKeys = normalized.flatMap(item => item.header_keys || []);
  const authSignals = normalized.flatMap(item => item.auth_signal_flags || []);
  const interactionSignals = normalized.flatMap(item => item.interaction_signal_flags || []);
  const errorSignals = normalized.flatMap(item => item.error_signal_flags || []);

  return {
    endpoint: endpointId,
    method: sample.method || '',
    host: sample.host || '',
    normalized_path: sample.normalized_path || '',
    total_samples: normalized.length,
    time_range: {
      newest: normalized[0]?.timestamp || '',
      oldest: normalized[normalized.length - 1]?.timestamp || '',
    },
    status_codes: topFrequencyFromItems(normalized.map(item => String(item.status || 0)).filter(Boolean)),
    mime_types: topFrequencyFromItems(normalized.map(item => item.mime_type)),
    common_query_keys: topFrequencyFromItems(allQueryKeys),
    common_request_body_keys: topFrequencyFromItems(allRequestKeys),
    common_response_body_keys: topFrequencyFromItems(allResponseKeys),
    common_header_keys: topFrequencyFromItems(allHeaderKeys),
    auth_signal_flags: topFrequencyFromItems(authSignals),
    interaction_signal_flags: topFrequencyFromItems(interactionSignals),
    error_signal_flags: topFrequencyFromItems(errorSignals),
    representative_request_ids: normalized.slice(0, 5).map(item => item.id).filter(Boolean),
    recent_request_ids: normalized.slice(0, 5).map(item => item.id).filter(Boolean),
  };
}

function pickSampleSummaries(summaries = [], strategy = 'diverse', limit = 3) {
  const normalized = summaries.map(normalizeSummary);
  const sampleLimit = Math.max(1, Math.min(20, Number(limit) || 3));
  const mode = String(strategy || 'diverse').trim().toLowerCase();
  if (mode === 'latest')
    return normalized.slice(0, sampleLimit);

  if (mode === 'error') {
    const errored = normalized.filter(item => (item.error_signal_flags || []).length || Number(item.status || 0) >= 400);
    return (errored.length ? errored : normalized).slice(0, sampleLimit);
  }

  const selected = [];
  const seen = new Set();
  for (const item of normalized) {
    const fingerprint = [
      String(item.status || 0),
      item.request_schema_hash || '',
      item.response_schema_hash || '',
    ].join('|');
    if (seen.has(fingerprint))
      continue;
    seen.add(fingerprint);
    selected.push(item);
    if (selected.length >= sampleLimit)
      return selected;
  }
  return normalized.slice(0, sampleLimit);
}

function scoreCandidateSummary(summary, endpointWeight = 0) {
  const normalized = normalizeSummary(summary);
  let score = 0;
  const reasons = [];

  if ((normalized.interaction_signal_flags || []).includes('write_method')) {
    score += 5;
    reasons.push('write_method');
  }
  score += (normalized.auth_signal_flags || []).length * 3;
  if ((normalized.auth_signal_flags || []).length)
    reasons.push('auth_signals');
  score += (normalized.interaction_signal_flags || []).filter(item => item !== 'write_method').length * 2;
  if (String(normalized.mime_type || '').includes('json')) {
    score += 2;
    reasons.push('json');
  }
  if (Number(normalized.status || 0) >= 400) {
    score += 1;
    reasons.push('non_2xx');
  }
  if ((normalized.error_signal_flags || []).length) {
    score += 2;
    reasons.push('error_signals');
  }
  score += Math.min(endpointWeight, 5);
  if (endpointWeight > 0)
    reasons.push('hot_endpoint');

  return {
    score,
    reasons: Array.from(new Set(reasons)),
  };
}

async function loadSummary(client, sessionId, requestId) {
  const value = await client.hget(sessionNetworkSummariesKey(sessionId), requestId);
  return normalizeSummary(parseJsonValue(value, null) || {});
}

async function loadSummaries(client, sessionId, requestIds) {
  const ids = Array.from(new Set((requestIds || []).map(item => String(item || '').trim()).filter(Boolean)));
  if (!ids.length)
    return [];
  const values = await client.hmget(sessionNetworkSummariesKey(sessionId), ...ids);
  return values
    .map(item => parseJsonValue(item, null))
    .filter(Boolean)
    .map(item => normalizeSummary(item));
}

async function loadRecord(client, sessionId, requestId) {
  const value = await client.hget(sessionNetworkRecordsKey(sessionId), requestId);
  return parseJsonValue(value, null);
}

async function loadRecentSummariesFromIndex(client, sessionId, limit) {
  const count = Math.max(1, Math.min(200, Number(limit) || 20));
  const ids = await client.zrevrange(sessionNetworkRecentKey(sessionId), 0, count - 1);
  return loadSummaries(client, sessionId, ids);
}

async function loadRecentSummariesFromStream(client, sessionId, limit) {
  const result = await readRecentNetworkEntries(client, sessionId, limit);
  return result.entries.map(item => enrichEntry(item.payload));
}

function buildIndexKeys(context, params = {}) {
  const keys = [];
  const pushTokenKeys = (kind, value) => {
    for (const token of tokenizeValue(value))
      keys.push(sessionNetworkFieldIndexKey(context.session_id, kind, token));
  };

  const host = normalizeSearchString(params.host);
  if (host)
    keys.push(sessionNetworkFieldIndexKey(context.session_id, 'host', host));

  const method = normalizeSearchString(params.method).toUpperCase();
  if (method)
    keys.push(sessionNetworkFieldIndexKey(context.session_id, 'method', method));

  if (params.status_code != null && Number.isFinite(Number(params.status_code)))
    keys.push(sessionNetworkFieldIndexKey(context.session_id, 'status', String(Number(params.status_code))));

  pushTokenKeys('mime_token', params.mime_type_contains);
  pushTokenKeys('url_token', params.url_contains);
  pushTokenKeys('path_token', params.path_contains);
  pushTokenKeys('query_key_token', params.query_key_search);
  pushTokenKeys('request_body_key_token', params.request_body_search);
  pushTokenKeys('response_body_key_token', params.response_body_search);
  pushTokenKeys('header_key_token', params.header_search);

  return keys;
}

async function withCandidateSource(client, context, params, operation) {
  const keys = buildIndexKeys(context, params);
  if (!keys.length) {
    const key = sessionNetworkRecentKey(context.session_id);
    const candidateCount = context.index_available ? Number(await client.zcard(key)) : 0;
    return operation({
      source_key: key,
      candidate_count: candidateCount,
      cleanup: async () => {},
    });
  }

  if (keys.length === 1) {
    const key = keys[0];
    const candidateCount = Number(await client.zcard(key));
    return operation({
      source_key: key,
      candidate_count: candidateCount,
      cleanup: async () => {},
    });
  }

  const tempKey = `${sessionNetworkRecentKey(context.session_id)}:tmp:${process.pid}:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`;
  await client.call('ZINTERSTORE', tempKey, String(keys.length), ...keys, 'AGGREGATE', 'MAX');
  await client.expire(tempKey, 10);

  try {
    const candidateCount = Number(await client.zcard(tempKey));
    return await operation({
      source_key: tempKey,
      candidate_count: candidateCount,
      cleanup: async () => {
        await client.del(tempKey);
      },
    });
  } finally {
    await client.del(tempKey).catch(() => {});
  }
}

async function collectMatchingSummaries(client, context, params, sourceKey, candidateCount) {
  const limit = Math.max(1, Math.min(200, Number(params.limit) || 20));
  const batchSize = Math.max(limit * 5, 50);
  let offset = 0;
  let totalMatches = 0;
  const returned = [];

  while (offset < candidateCount) {
    const ids = await client.zrevrange(sourceKey, offset, offset + batchSize - 1);
    if (!ids.length)
      break;
    const summaries = await loadSummaries(client, context.session_id, ids);
    for (const summary of summaries) {
      if (!matchesSummaryFilters(summary, params))
        continue;
      totalMatches += 1;
      if (returned.length < limit)
        returned.push(summarizeEntry(summary));
    }
    offset += ids.length;
  }

  return {
    total_matches: totalMatches,
    returned,
    candidate_count: candidateCount,
  };
}

async function getDatasetOverview(context) {
  return withRedis(async client => {
    const [hosts, methods, statusCodes, mimeTypes, newestIds, oldestIds] = await Promise.all([
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'hosts')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'methods')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'status_codes')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'mime_types')),
      context.index_available ? client.zrevrange(sessionNetworkRecentKey(context.session_id), 0, 0) : Promise.resolve([]),
      context.index_available ? client.zrange(sessionNetworkRecentKey(context.session_id), 0, 0) : Promise.resolve([]),
    ]);

    const [newest] = await loadSummaries(client, context.session_id, newestIds || []);
    const [oldest] = await loadSummaries(client, context.session_id, oldestIds || []);

    return {
      dataset_id: context.dataset_id,
      source_type: context.source_type,
      display_name: context.display_name,
      session_id: context.session_id,
      page_url: context.page_url,
      first_party_hosts: context.first_party_hosts,
      is_prefiltered: context.is_prefiltered,
      raw_available: false,
      index_available: context.index_available,
      index_version: context.index_version,
      raw_request_count: context.network_count,
      filtered_request_count: context.network_count,
      removed_request_count: 0,
      time_range: {
        newest: newest?.timestamp || context.latest_timestamp || '',
        oldest: oldest?.timestamp || '',
      },
      top_hosts: toFrequencyMapFromHash(hosts),
      methods: toFrequencyMapFromHash(methods),
      status_codes: toFrequencyMapFromHash(statusCodes),
      mime_types: toFrequencyMapFromHash(mimeTypes),
    };
  });
}

async function searchRequests(context, params = {}) {
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 search_requests。请重新采集该会话后再搜索。`);
  }

  return withRedis(async client => {
    return withCandidateSource(client, context, params, async source => {
      const result = await collectMatchingSummaries(client, context, params, source.source_key, source.candidate_count);
      await source.cleanup();
      return {
        dataset_id: context.dataset_id,
        total_matches: result.total_matches,
        candidate_count: result.candidate_count,
        returned: result.returned,
      };
    });
  });
}

async function getRecentRequests(context, params = {}) {
  const limit = Math.max(1, Math.min(200, Number(params.limit) || 20));
  return withRedis(async client => {
    const entries = context.index_available
      ? await loadRecentSummariesFromIndex(client, context.session_id, limit)
      : await loadRecentSummariesFromStream(client, context.session_id, limit);
    return {
      dataset_id: context.dataset_id,
      total_requests: context.network_count,
      returned: entries.map(summarizeEntry),
    };
  });
}

async function getRequestDetails(context, params = {}) {
  const requestId = String(params.request_id || '').trim();
  const detailLevel = normalizeDetailLevel(params.detail_level);
  if (!requestId)
    throw new Error('request_id 不能为空');
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持按 request_id 直查详情。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const rawEntry = await loadRecord(client, context.session_id, requestId);
    if (!rawEntry)
      throw new Error(`未找到请求: ${requestId}`);
    const entry = enrichEntry(rawEntry);
    return {
      dataset_id: context.dataset_id,
      detail_level: detailLevel,
      include_raw: false,
      filtered_out: false,
      request: reduceEntryByDetailLevel(entry, detailLevel),
    };
  });
}

async function getStatistics(context) {
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 get_statistics。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const [hosts, methods, statusCodes, mimeTypes, timingHash, endpointTop, uniquePaths, uniqueHosts, durationTop] = await Promise.all([
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'hosts')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'methods')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'status_codes')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'mime_types')),
      client.hgetall(sessionNetworkStatsKey(context.session_id, 'timing')),
      client.zrevrange(sessionNetworkEndpointCountsKey(context.session_id), 0, 29, 'WITHSCORES'),
      client.zcard(sessionNetworkEndpointCountsKey(context.session_id)),
      client.hlen(sessionNetworkStatsKey(context.session_id, 'hosts')),
      client.zrevrange(sessionNetworkDurationKey(context.session_id), 0, 0, 'WITHSCORES'),
    ]);

    const totalDuration = Number(timingHash.total_duration_ms || 0);
    const maxDuration = durationTop.length >= 2 ? Number(durationTop[1]) || 0 : 0;
    const topEndpoints = [];

    for (let index = 0; index < endpointTop.length; index += 2) {
      const endpoint = endpointTop[index];
      const count = Number(endpointTop[index + 1] || 0);
      topEndpoints.push({ value: endpoint, count });
    }

    return {
      dataset_id: context.dataset_id,
      total_requests: context.network_count,
      unique_hosts: Number(uniqueHosts || 0),
      unique_paths: Number(uniquePaths || 0),
      avg_duration_ms: context.network_count ? Number((totalDuration / context.network_count).toFixed(2)) : 0,
      max_duration_ms: maxDuration,
      methods: toFrequencyMapFromHash(methods),
      status_codes: toFrequencyMapFromHash(statusCodes),
      hosts: toFrequencyMapFromHash(hosts),
      mime_types: toFrequencyMapFromHash(mimeTypes),
      top_endpoints: topEndpoints.slice(0, 30),
    };
  });
}

async function collectEndpointMembers(client, sessionId, endpointId, limit = 200) {
  const count = Math.max(1, Math.min(500, Number(limit) || 200));
  const requestIds = await client.zrevrange(sessionNetworkEndpointMembersKey(sessionId, endpointId), 0, count - 1);
  const summaries = await loadSummaries(client, sessionId, requestIds);
  return {
    request_ids: requestIds,
    summaries,
  };
}

async function getEndpointGroupSummary(context, params = {}) {
  const endpointId = String(params.endpoint || '').trim();
  if (!endpointId)
    throw new Error('endpoint 不能为空');
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 get_endpoint_group_summary。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const meta = parseJsonValue(await client.hget(sessionNetworkEndpointMetaKey(context.session_id), endpointId), null);
    if (!meta)
      throw new Error(`未找到 endpoint: ${endpointId}`);
    const { summaries } = await collectEndpointMembers(client, context.session_id, endpointId, 200);
    return {
      dataset_id: context.dataset_id,
      endpoint: endpointId,
      summary: {
        ...summarizeEndpointGroup(endpointId, summaries),
        sample_url: meta.sample_url || '',
      },
    };
  });
}

async function getEndpointGroupSamples(context, params = {}) {
  const endpointId = String(params.endpoint || '').trim();
  const strategy = String(params.strategy || 'diverse').trim().toLowerCase();
  const limit = Math.max(1, Math.min(20, Number(params.limit) || 3));
  if (!endpointId)
    throw new Error('endpoint 不能为空');
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 get_endpoint_group_samples。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const { summaries } = await collectEndpointMembers(client, context.session_id, endpointId, 200);
    if (!summaries.length)
      throw new Error(`endpoint 没有可用样本: ${endpointId}`);
    const samples = pickSampleSummaries(summaries, strategy, limit);
    return {
      dataset_id: context.dataset_id,
      endpoint: endpointId,
      strategy,
      total_available: summaries.length,
      samples: samples.map(item => summarizeEntry(item)),
    };
  });
}

async function getRequestSequenceWindow(context, params = {}) {
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 get_request_sequence_window。请重新采集后再试。`);
  }

  return withRedis(async client => {
    let anchorRequestId = String(params.request_id || '').trim();
    if (!anchorRequestId) {
      const endpointId = String(params.endpoint || '').trim();
      if (!endpointId)
        throw new Error('request_id 或 endpoint 至少需要一个');
      const ids = await client.zrevrange(sessionNetworkEndpointMembersKey(context.session_id, endpointId), 0, 0);
      anchorRequestId = String(ids[0] || '').trim();
    }
    if (!anchorRequestId)
      throw new Error('未找到 anchor request');

    const before = Math.max(0, Math.min(20, Number(params.before) || 3));
    const after = Math.max(0, Math.min(20, Number(params.after) || 3));
    const rank = await client.zrank(sessionNetworkRecentKey(context.session_id), anchorRequestId);
    if (rank == null)
      throw new Error(`未找到请求序列位置: ${anchorRequestId}`);

    const start = Math.max(Number(rank) - before, 0);
    const end = Number(rank) + after;
    const ids = await client.zrange(sessionNetworkRecentKey(context.session_id), start, end);
    const summaries = await loadSummaries(client, context.session_id, ids);

    return {
      dataset_id: context.dataset_id,
      anchor_request_id: anchorRequestId,
      returned: summaries.map(item => ({
        ...summarizeEntry(item),
        is_anchor: item.id === anchorRequestId,
      })),
    };
  });
}

async function rankCandidateRequests(context, params = {}) {
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 rank_candidate_requests。请重新采集后再试。`);
  }

  const limit = Math.max(1, Math.min(30, Number(params.limit) || 10));
  return withRedis(async client => {
    const rawTop = await client.zrevrange(sessionNetworkEndpointCountsKey(context.session_id), 0, 29, 'WITHSCORES');
    const scored = [];

    for (let index = 0; index < rawTop.length; index += 2) {
      const endpointId = rawTop[index];
      const endpointCount = Number(rawTop[index + 1] || 0);
      const { summaries } = await collectEndpointMembers(client, context.session_id, endpointId, 8);
      for (const summary of summaries) {
        const scoredSummary = scoreCandidateSummary(summary, Math.ceil(endpointCount / 3));
        scored.push({
          endpoint: endpointId,
          score: scoredSummary.score,
          reasons: scoredSummary.reasons,
          request: summarizeEntry(summary),
        });
      }
    }

    const deduped = new Map();
    for (const item of scored) {
      const requestId = String(item.request?.id || '').trim();
      if (!requestId)
        continue;
      const existing = deduped.get(requestId);
      if (!existing || item.score > existing.score)
        deduped.set(requestId, item);
    }

    const ranked = Array.from(deduped.values())
      .sort((left, right) => right.score - left.score || String(right.request.timestamp || '').localeCompare(String(left.request.timestamp || '')))
      .slice(0, limit);

    return {
      dataset_id: context.dataset_id,
      total_ranked: ranked.length,
      ranked_requests: ranked,
    };
  });
}

async function compareRequests(context, params = {}) {
  const leftId = String(params.request_id_a || '').trim();
  const rightId = String(params.request_id_b || '').trim();
  if (!leftId || !rightId)
    throw new Error('request_id_a 和 request_id_b 不能为空');

  const [left, right] = await Promise.all([
    getRequestDetails(context, { request_id: leftId, detail_level: 'full' }),
    getRequestDetails(context, { request_id: rightId, detail_level: 'full' }),
  ]);
  const requestLeft = left.request;
  const requestRight = right.request;

  return {
    dataset_id: context.dataset_id,
    request_id_a: requestLeft.id,
    request_id_b: requestRight.id,
    request: {
      method_equal: requestLeft.method === requestRight.method,
      host_equal: requestLeft.host === requestRight.host,
      normalized_path_equal: requestLeft.normalized_path === requestRight.normalized_path,
      url_a: requestLeft.url,
      url_b: requestRight.url,
      query_keys_a: requestLeft.query_keys,
      query_keys_b: requestRight.query_keys,
      request_body_equal: requestLeft.request_body === requestRight.request_body,
      request_body_keys_a: requestLeft.request_body_keys,
      request_body_keys_b: requestRight.request_body_keys,
    },
    response: {
      status_a: requestLeft.status,
      status_b: requestRight.status,
      mime_type_a: requestLeft.mime_type,
      mime_type_b: requestRight.mime_type,
      response_body_equal: requestLeft.response_body === requestRight.response_body,
      response_body_preview_a: summarizeText(requestLeft.response_body, 180),
      response_body_preview_b: summarizeText(requestRight.response_body, 180),
    },
    timing: {
      duration_a: requestLeft.duration,
      duration_b: requestRight.duration,
      delta_ms: requestLeft.duration - requestRight.duration,
    },
  };
}

function similarityScore(target, candidate) {
  let score = 0;
  const matchedOn = [];

  if (target.method === candidate.method) {
    score += 3;
    matchedOn.push('method');
  }
  if (target.host === candidate.host) {
    score += 2;
    matchedOn.push('host');
  }
  if (target.normalized_path === candidate.normalized_path) {
    score += 4;
    matchedOn.push('normalized_path');
  }
  if (target.query_keys.join(',') === candidate.query_keys.join(',') && target.query_keys.length) {
    score += 2;
    matchedOn.push('query_keys');
  }
  if (
    target.request_body_keys.join(',') === candidate.request_body_keys.join(',')
    && target.request_body_keys.length
  ) {
    score += 2;
    matchedOn.push('request_body_keys');
  }

  return { score, matchedOn };
}

async function findSimilarRequests(context, params = {}) {
  const limit = Math.max(1, Math.min(100, Number(params.limit) || 10));
  const requestId = String(params.request_id || '').trim();
  if (!requestId)
    throw new Error('request_id 不能为空');
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 find_similar_requests。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const target = await loadSummary(client, context.session_id, requestId);
    if (!target || !target.id)
      throw new Error(`未找到请求: ${requestId}`);

    const endpointId = endpointIdFromSummary(target);
    const [endpointIds, hostIds] = await Promise.all([
      client.zrevrange(sessionNetworkEndpointMembersKey(context.session_id, endpointId), 0, 199),
      target.host ? client.zrevrange(sessionNetworkFieldIndexKey(context.session_id, 'host', target.host), 0, 199) : Promise.resolve([]),
    ]);

    const candidateIds = Array.from(new Set([...endpointIds, ...hostIds])).filter(id => id !== target.id);
    const candidates = await loadSummaries(client, context.session_id, candidateIds);

    const matched = candidates
      .map(entry => {
        const result = similarityScore(target, entry);
        return {
          entry,
          score: result.score,
          matched_on: result.matchedOn,
        };
      })
      .filter(item => item.score > 0)
      .sort((left, right) => right.score - left.score || String(right.entry.timestamp).localeCompare(String(left.entry.timestamp)))
      .slice(0, limit)
      .map(item => ({
        score: item.score,
        matched_on: item.matched_on,
        request: summarizeEntry(item.entry),
      }));

    return {
      dataset_id: context.dataset_id,
      target_request_id: target.id,
      target_request: summarizeEntry(target),
      similar_requests: matched,
    };
  });
}

async function extractApiEndpoints(context, params = {}) {
  const limit = Math.max(1, Math.min(200, Number(params.limit) || 100));
  if (!context.index_available) {
    throw new Error(`会话 ${context.session_id} 尚未建立结构化索引，当前不支持 extract_api_endpoints。请重新采集后再试。`);
  }

  return withRedis(async client => {
    const rawTop = await client.zrevrange(sessionNetworkEndpointCountsKey(context.session_id), 0, Math.max(limit * 3, 50) - 1, 'WITHSCORES');
    const endpoints = [];

    for (let index = 0; index < rawTop.length; index += 2) {
      const endpointId = rawTop[index];
      const count = Number(rawTop[index + 1] || 0);
      const meta = parseJsonValue(await client.hget(sessionNetworkEndpointMetaKey(context.session_id), endpointId), null);
      if (!meta)
        continue;

      const sampleRequestIds = await client.zrevrange(sessionNetworkEndpointMembersKey(context.session_id, endpointId), 0, 4);
      const sampleSummaries = await loadSummaries(client, context.session_id, sampleRequestIds);
      const sample = sampleSummaries[0] || meta;
      if (!isLikelyApiRequest(sample))
        continue;

      endpoints.push({
        endpoint: endpointId,
        method: meta.method,
        host: meta.host,
        normalized_path: meta.normalized_path,
        sample_url: meta.sample_url,
        count,
        sample_request_ids: sampleRequestIds,
        schema_variants: Array.from(new Set(sampleSummaries.map(item => `${item.request_schema_hash || ''}|${item.response_schema_hash || ''}`))).filter(Boolean).length,
        auth_signal_flags: topFrequencyFromItems(sampleSummaries.flatMap(item => item.auth_signal_flags || []), 5),
        interaction_signal_flags: topFrequencyFromItems(sampleSummaries.flatMap(item => item.interaction_signal_flags || []), 5),
        status_codes: Array.from(new Set(sampleSummaries.map(item => Number(item.status || 0)).filter(Boolean))).sort((left, right) => left - right),
        mime_types: Array.from(new Set(sampleSummaries.map(item => String(item.mime_type || '')).filter(Boolean))).sort(),
      });

      if (endpoints.length >= limit)
        break;
    }

    return {
      dataset_id: context.dataset_id,
      total_groups: endpoints.length,
      endpoints,
    };
  });
}

function shellEscapeSingleQuotes(value) {
  return String(value).replace(/'/g, `'\"'\"'`);
}

function buildCurl(entry) {
  const lines = [`curl --request ${entry.method || 'GET'} '${shellEscapeSingleQuotes(entry.url)}'`];
  for (const [key, value] of Object.entries(entry.request_headers || {}))
    lines.push(`  --header '${shellEscapeSingleQuotes(`${key}: ${value}`)}'`);

  if (entry.request_body) {
    const payload = entry.request_body_truncated
      ? '<request body omitted: truncated>'
      : entry.request_body;
    lines.push(`  --data-raw '${shellEscapeSingleQuotes(payload)}'`);
  }

  return lines.join(' \\\n');
}

function buildJsFetch(entry) {
  const payload = entry.request_body_truncated
    ? '<request body omitted: truncated>'
    : entry.request_body;
  const config = {
    method: entry.method || 'GET',
    headers: entry.request_headers || {},
  };
  if (payload)
    config.body = payload;

  return [
    `const response = await fetch(${JSON.stringify(entry.url)}, ${JSON.stringify(config, null, 2)});`,
    'const text = await response.text();',
    'console.log(response.status, response.headers);',
    'console.log(text);',
  ].join('\n');
}

function buildPythonRequests(entry) {
  const payload = entry.request_body_truncated
    ? '<request body omitted: truncated>'
    : entry.request_body;
  const lines = [
    'import requests',
    '',
    'response = requests.request(',
    `    method=${JSON.stringify(entry.method || 'GET')},`,
    `    url=${JSON.stringify(entry.url)},`,
    `    headers=${JSON.stringify(entry.request_headers || {}, null, 4)},`,
  ];
  if (payload)
    lines.push(`    data=${JSON.stringify(payload)},`);
  lines.push(')');
  lines.push('print(response.status_code)');
  lines.push('print(dict(response.headers))');
  lines.push('print(response.text)');
  return lines.join('\n');
}

async function generateCode(context, params = {}) {
  const format = String(params.format || 'javascript').toLowerCase();
  const detail = await getRequestDetails(context, {
    request_id: params.request_id,
    detail_level: 'full',
  });
  const entry = detail.request;

  if (format === 'curl')
    return { dataset_id: context.dataset_id, request_id: entry.id, format: 'curl', code: buildCurl(entry) };
  if (format === 'python')
    return { dataset_id: context.dataset_id, request_id: entry.id, format: 'python', code: buildPythonRequests(entry) };
  if (format === 'javascript' || format === 'js')
    return { dataset_id: context.dataset_id, request_id: entry.id, format: 'javascript', code: buildJsFetch(entry) };

  throw new Error(`不支持的 format: ${format}`);
}

async function getCurl(context, params = {}) {
  const result = await generateCode(context, {
    request_id: params.request_id,
    format: 'curl',
  });
  return {
    dataset_id: result.dataset_id,
    request_id: result.request_id,
    curl: result.code,
  };
}

module.exports = {
  compareRequests,
  extractApiEndpoints,
  findSimilarRequests,
  generateCode,
  getCurl,
  getDatasetOverview,
  getEndpointGroupSamples,
  getEndpointGroupSummary,
  getRecentRequests,
  getRequestDetails,
  getRequestSequenceWindow,
  getStatistics,
  rankCandidateRequests,
  searchRequests,
};
