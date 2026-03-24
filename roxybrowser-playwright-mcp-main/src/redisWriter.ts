/**
 * Redis writer for browser session data (session logs, network logs).
 * Reads REDIS_URL and REDIS_SESSION_PREFIX from environment variables.
 */

import { createHash } from 'crypto';
import { Redis } from 'ioredis';

export type SessionLogPayload = {
  ordinal: number;
  toolCall?: {
    toolName: string;
    toolArgs: Record<string, unknown>;
    result: string;
    isError?: boolean;
  };
  userAction?: Record<string, unknown>;
  code: string;
  snapshot?: string;
};

export type NetworkLogPayload = {
  id: string;
  timestamp: string;
  request: Record<string, unknown>;
  response: Record<string, unknown>;
  timing: Record<string, unknown>;
};

type NetworkIndexSummary = {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  host: string;
  path: string;
  normalized_path: string;
  query_keys: string[];
  status: number;
  status_text: string;
  mime_type: string;
  duration: number;
  request_header_keys: string[];
  response_header_keys: string[];
  header_keys: string[];
  request_body_keys: string[];
  response_body_keys: string[];
  request_body_size: number;
  response_body_size: number;
  request_body_hash: string;
  response_body_hash: string;
  request_schema_hash: string;
  response_schema_hash: string;
  auth_signal_flags: string[];
  interaction_signal_flags: string[];
  error_signal_flags: string[];
  request_body_preview: string;
  response_body_preview: string;
  request_body_truncated: boolean;
  response_body_truncated: boolean;
};

const _prefix = process.env.REDIS_SESSION_PREFIX ?? 'browser';
const NETWORK_INDEX_VERSION = 'v1';

let _client: InstanceType<typeof Redis> | null = null;

function getClient(): InstanceType<typeof Redis> {
  if (!_client) {
    const url = process.env.REDIS_URL ?? 'redis://localhost:6379';
    _client = new Redis(url);
    _client.on('error', (err: Error) => {
      // eslint-disable-next-line no-console
      console.error(`[RedisWriter] connection error: ${err.message}`);
    });
  }
  return _client;
}

function sessionMetaKey(sessionId: string): string {
  return `${_prefix}:session:${sessionId}:meta`;
}

function sessionLogKey(sessionId: string): string {
  return `${_prefix}:session:${sessionId}:log`;
}

function sessionNetworkKey(sessionId: string): string {
  return `${_prefix}:session:${sessionId}:network`;
}

function sessionNetworkIndexBaseKey(sessionId: string): string {
  return `${_prefix}:session:${sessionId}:network:index`;
}

function sessionNetworkRecordsKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:records`;
}

function sessionNetworkSummariesKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:summaries`;
}

function sessionNetworkRecentKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:recent`;
}

function sessionNetworkFieldIndexKey(sessionId: string, kind: string, value: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:z:${kind}:${encodeIndexPart(value)}`;
}

function sessionNetworkStatsKey(sessionId: string, kind: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:stats:${kind}`;
}

function sessionNetworkEndpointCountsKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint-counts`;
}

function sessionNetworkEndpointMetaKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint-meta`;
}

function sessionNetworkEndpointMembersKey(sessionId: string, endpointId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint:${encodeIndexPart(endpointId)}`;
}

function sessionNetworkDurationKey(sessionId: string): string {
  return `${sessionNetworkIndexBaseKey(sessionId)}:durations`;
}

function encodeIndexPart(value: string): string {
  return Buffer.from(String(value || '').trim()).toString('base64url');
}

function safeParseUrl(rawUrl: unknown): URL | null {
  try {
    return new URL(String(rawUrl || '').trim());
  } catch {
    return null;
  }
}

function normalizeMimeType(value: unknown): string {
  return String(value || '')
    .split(';', 1)[0]
    .trim()
    .toLowerCase();
}

function normalizePathPattern(pathname: string): string {
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

function stringifyBody(value: unknown): string {
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

function summarizeText(text: string, maxLength = 120): string {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim();
  if (normalized.length <= maxLength)
    return normalized;
  return `${normalized.slice(0, maxLength)}...`;
}

function collectObjectKeys(value: unknown, collector: Set<string>, prefix = ''): void {
  if (!value || typeof value !== 'object')
    return;
  if (Array.isArray(value)) {
    for (const item of value)
      collectObjectKeys(item, collector, prefix);
    return;
  }
  for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
    const current = prefix ? `${prefix}.${key}` : key;
    collector.add(current);
    collectObjectKeys(nested, collector, current);
  }
}

function normalizeUniqueLower(values: Iterable<string>): string[] {
  return Array.from(
    new Set(
      Array.from(values)
        .map(value => String(value || '').trim().toLowerCase())
        .filter(Boolean),
    ),
  ).sort();
}

function bodyKeySet(bodyText: string, contentType: string): string[] {
  const keys = new Set<string>();
  const text = String(bodyText || '').trim();
  if (!text)
    return [];

  const lowerContentType = String(contentType || '').toLowerCase();
  if (lowerContentType.includes('application/json') || text.startsWith('{') || text.startsWith('[')) {
    try {
      const parsed = JSON.parse(text);
      collectObjectKeys(parsed, keys);
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

function tokenizeValue(value: string): string[] {
  return String(value || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function flattenKeyTokens(keys: string[]): string[] {
  const tokens = new Set<string>();
  for (const key of keys) {
    const normalized = String(key || '').trim().toLowerCase();
    if (!normalized)
      continue;
    tokens.add(normalized);
    for (const token of tokenizeValue(normalized))
      tokens.add(token);
  }
  return Array.from(tokens);
}

function hashText(value: string): string {
  const text = String(value || '');
  if (!text)
    return '';
  return createHash('sha1').update(text).digest('hex');
}

function hashKeyList(values: string[]): string {
  const normalized = normalizeUniqueLower(values);
  if (!normalized.length)
    return '';
  return hashText(normalized.join('\n'));
}

function collectMatchedSignals(values: Iterable<string>, patterns: string[]): string[] {
  const matched = new Set<string>();
  const normalizedValues = Array.from(values)
    .map(value => String(value || '').trim().toLowerCase())
    .filter(Boolean);

  for (const value of normalizedValues) {
    const tokens = new Set(tokenizeValue(value));
    for (const pattern of patterns) {
      const normalizedPattern = String(pattern || '').trim().toLowerCase();
      if (!normalizedPattern)
        continue;
      if (value.includes(normalizedPattern) || tokens.has(normalizedPattern))
        matched.add(normalizedPattern);
    }
  }

  return Array.from(matched).sort();
}

function buildAuthSignals(input: {
  headerKeys: string[];
  queryKeys: string[];
  requestBodyKeys: string[];
  responseBodyKeys: string[];
  url: string;
  path: string;
}): string[] {
  return collectMatchedSignals(
    [
      ...input.headerKeys,
      ...input.queryKeys,
      ...input.requestBodyKeys,
      ...input.responseBodyKeys,
      input.url,
      input.path,
    ],
    ['authorization', 'cookie', 'set-cookie', 'token', 'nonce', 'sign', 'signature', 'timestamp', 'session', 'jwt', 'bearer'],
  );
}

function buildInteractionSignals(input: {
  method: string;
  url: string;
  path: string;
  requestBodyKeys: string[];
  responseBodyKeys: string[];
}): string[] {
  const matched = collectMatchedSignals(
    [
      input.method,
      input.url,
      input.path,
      ...input.requestBodyKeys,
      ...input.responseBodyKeys,
    ],
    ['login', 'auth', 'checkout', 'order', 'submit', 'create', 'update', 'donate', 'payment', 'confirm', 'graphql', 'mutation'],
  );
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(input.method || '').toUpperCase()))
    matched.unshift('write_method');
  return Array.from(new Set(matched)).sort();
}

function buildErrorSignals(input: {
  status: number;
  responseBodyKeys: string[];
  responseBodyPreview: string;
}): string[] {
  const matched = new Set<string>();
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
    [...input.responseBodyKeys, input.responseBodyPreview],
    ['error', 'errors', 'message', 'exception', 'declined', 'invalid', 'failed'],
  )) {
    matched.add(item);
  }
  return Array.from(matched).sort();
}

function endpointIdFromSummary(summary: NetworkIndexSummary): string {
  return `${summary.method} ${summary.host}${summary.normalized_path}`;
}

function buildIndexSummary(payload: NetworkLogPayload): NetworkIndexSummary {
  const request = payload.request || {};
  const response = payload.response || {};
  const requestUrl = String(request.url || '').trim();
  const parsedUrl = safeParseUrl(requestUrl);
  const requestHeaders = (request.headers || {}) as Record<string, unknown>;
  const responseHeaders = (response.headers || {}) as Record<string, unknown>;
  const mimeType = normalizeMimeType(response.mimeType || responseHeaders['content-type']);
  const requestBody = stringifyBody(request.body);
  const responseBody = stringifyBody(response.body);
  const requestContentType = normalizeMimeType(requestHeaders['content-type']);

  const queryKeys = parsedUrl ? normalizeUniqueLower(parsedUrl.searchParams.keys()) : [];
  const requestHeaderKeys = normalizeUniqueLower(Object.keys(requestHeaders));
  const responseHeaderKeys = normalizeUniqueLower(Object.keys(responseHeaders));
  const headerKeys = normalizeUniqueLower([...requestHeaderKeys, ...responseHeaderKeys]);
  const requestBodyKeys = bodyKeySet(requestBody, requestContentType);
  const responseBodyKeys = bodyKeySet(responseBody, mimeType);
  const requestBodyPreview = summarizeText(requestBody);
  const responseBodyPreview = summarizeText(responseBody);
  const requestBodySize = Number(request.bodySize || Buffer.byteLength(requestBody, 'utf8') || 0);
  const responseBodySize = Number(response.bodySize || Buffer.byteLength(responseBody, 'utf8') || 0);
  const authSignals = buildAuthSignals({
    headerKeys,
    queryKeys,
    requestBodyKeys,
    responseBodyKeys,
    url: requestUrl,
    path: parsedUrl ? parsedUrl.pathname : '',
  });
  const interactionSignals = buildInteractionSignals({
    method: String(request.method || '').trim().toUpperCase(),
    url: requestUrl,
    path: parsedUrl ? parsedUrl.pathname : '',
    requestBodyKeys,
    responseBodyKeys,
  });
  const errorSignals = buildErrorSignals({
    status: Number(response.status || 0),
    responseBodyKeys,
    responseBodyPreview,
  });

  return {
    id: String(payload.id || '').trim(),
    timestamp: String(payload.timestamp || '').trim(),
    method: String(request.method || '').trim().toUpperCase(),
    url: requestUrl,
    host: parsedUrl ? parsedUrl.hostname.toLowerCase() : '',
    path: parsedUrl ? parsedUrl.pathname : '',
    normalized_path: normalizePathPattern(parsedUrl ? parsedUrl.pathname : ''),
    query_keys: queryKeys,
    status: Number(response.status || 0),
    status_text: String(response.statusText || ''),
    mime_type: mimeType,
    duration: Number(payload.timing?.duration || 0),
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
    auth_signal_flags: authSignals,
    interaction_signal_flags: interactionSignals,
    error_signal_flags: errorSignals,
    request_body_preview: requestBodyPreview,
    response_body_preview: responseBodyPreview,
    request_body_truncated: Boolean(request.bodyTruncated),
    response_body_truncated: Boolean(response.bodyTruncated),
  };
}

function zaddIndexValues(
  multi: ReturnType<InstanceType<typeof Redis>['multi']>,
  keyBuilder: (value: string) => string,
  values: Iterable<string>,
  score: number,
  requestId: string,
) {
  for (const value of new Set(Array.from(values).map(item => String(item || '').trim()).filter(Boolean)))
    multi.zadd(keyBuilder(value), score, requestId);
}

export async function registerSession(sessionId: string, meta: Record<string, string> = {}): Promise<void> {
  const client = getClient();
  const normalizedMeta = {
    status: 'collecting',
    ...meta,
  };
  const ops: Promise<unknown>[] = [
    client.sadd(`${_prefix}:sessions`, sessionId),
  ];
  if (Object.keys(normalizedMeta).length)
    ops.push(client.hset(sessionMetaKey(sessionId), normalizedMeta));
  await Promise.all(ops);
}

export async function updateSessionMeta(sessionId: string, meta: Record<string, string>): Promise<void> {
  if (!Object.keys(meta).length)
    return;
  await getClient().hset(sessionMetaKey(sessionId), meta);
}

export async function writeSessionEntry(sessionId: string, payload: SessionLogPayload): Promise<void> {
  const key = sessionLogKey(sessionId);
  await getClient().xadd(key, '*', 'ordinal', String(payload.ordinal), 'data', JSON.stringify(payload));
}

export async function writeNetworkEntry(sessionId: string, payload: NetworkLogPayload): Promise<void> {
  const summary = buildIndexSummary(payload);
  const timestampScore = Date.parse(summary.timestamp) || Date.now();
  const endpointId = endpointIdFromSummary(summary);
  const queryKeyTokens = flattenKeyTokens(summary.query_keys);
  const requestBodyKeyTokens = flattenKeyTokens(summary.request_body_keys);
  const responseBodyKeyTokens = flattenKeyTokens(summary.response_body_keys);
  const headerKeyTokens = flattenKeyTokens(summary.header_keys);
  const pathTokens = Array.from(new Set([
    ...tokenizeValue(summary.path),
    ...tokenizeValue(summary.normalized_path),
  ]));
  const urlTokens = Array.from(new Set([
    ...tokenizeValue(summary.url),
    ...tokenizeValue(summary.host),
    ...pathTokens,
  ]));
  const mimeTokens = tokenizeValue(summary.mime_type);
  const payloadJson = JSON.stringify(payload);
  const summaryJson = JSON.stringify(summary);

  const key = sessionNetworkKey(sessionId);
  const client = getClient();
  const multi = client.multi();

  multi.xadd(key, '*', 'id', payload.id, 'data', payloadJson);
  multi.hset(sessionNetworkRecordsKey(sessionId), payload.id, payloadJson);
  multi.hset(sessionNetworkSummariesKey(sessionId), payload.id, summaryJson);
  multi.zadd(sessionNetworkRecentKey(sessionId), timestampScore, payload.id);

  if (summary.duration > 0) {
    multi.hincrbyfloat(sessionNetworkStatsKey(sessionId, 'timing'), 'total_duration_ms', summary.duration);
    multi.zadd(sessionNetworkDurationKey(sessionId), summary.duration, payload.id);
  }

  if (summary.host) {
    multi.hincrby(sessionNetworkStatsKey(sessionId, 'hosts'), summary.host, 1);
    multi.zadd(sessionNetworkFieldIndexKey(sessionId, 'host', summary.host), timestampScore, payload.id);
  }
  if (summary.method) {
    multi.hincrby(sessionNetworkStatsKey(sessionId, 'methods'), summary.method, 1);
    multi.zadd(sessionNetworkFieldIndexKey(sessionId, 'method', summary.method), timestampScore, payload.id);
  }
  if (summary.status) {
    multi.hincrby(sessionNetworkStatsKey(sessionId, 'status_codes'), String(summary.status), 1);
    multi.zadd(sessionNetworkFieldIndexKey(sessionId, 'status', String(summary.status)), timestampScore, payload.id);
  }
  if (summary.mime_type) {
    multi.hincrby(sessionNetworkStatsKey(sessionId, 'mime_types'), summary.mime_type, 1);
    multi.zadd(sessionNetworkFieldIndexKey(sessionId, 'mime', summary.mime_type), timestampScore, payload.id);
  }

  if (endpointId.trim()) {
    multi.zadd(sessionNetworkEndpointMembersKey(sessionId, endpointId), timestampScore, payload.id);
    multi.zincrby(sessionNetworkEndpointCountsKey(sessionId), 1, endpointId);
    multi.hset(sessionNetworkEndpointMetaKey(sessionId), endpointId, JSON.stringify({
      endpoint: endpointId,
      method: summary.method,
      host: summary.host,
      normalized_path: summary.normalized_path,
      sample_url: summary.url,
    }));
  }

  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'path_token', value), pathTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'url_token', value), urlTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'mime_token', value), mimeTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'query_key_token', value), queryKeyTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'request_body_key_token', value), requestBodyKeyTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'response_body_key_token', value), responseBodyKeyTokens, timestampScore, payload.id);
  zaddIndexValues(multi, value => sessionNetworkFieldIndexKey(sessionId, 'header_key_token', value), headerKeyTokens, timestampScore, payload.id);

  await multi.exec();
}

async function readStreamStats(key: string): Promise<{ count: number; lastStreamId: string }> {
  const client = getClient();
  const count = await client.xlen(key);
  if (!count)
    return { count: 0, lastStreamId: '' };
  const latest = await client.xrevrange(key, '+', '-', 'COUNT', 1);
  return {
    count,
    lastStreamId: latest[0]?.[0] ?? '',
  };
}

export async function sealSession(
  sessionId: string,
  meta: Record<string, string> = {},
): Promise<void> {
  const [logStats, networkStats] = await Promise.all([
    readStreamStats(sessionLogKey(sessionId)),
    readStreamStats(sessionNetworkKey(sessionId)),
  ]);

  await updateSessionMeta(sessionId, {
    status: 'sealed',
    logCount: String(logStats.count),
    networkCount: String(networkStats.count),
    lastLogStreamId: logStats.lastStreamId,
    lastNetworkStreamId: networkStats.lastStreamId,
    networkIndexVersion: NETWORK_INDEX_VERSION,
    finalizedAt: new Date().toISOString(),
    ...meta,
  });
}

export async function closeRedisClient(): Promise<void> {
  if (_client) {
    await _client.quit();
    _client = null;
  }
}
