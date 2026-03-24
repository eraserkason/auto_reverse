'use strict';

const Redis = require('ioredis');

const {
  inferFirstPartyHosts,
} = require('../../main_project_backend/network/session_network_filter.js');

const {
  REDIS_SESSION_PREFIX,
  REDIS_URL,
} = require('./config');

async function withRedis(operation) {
  const client = new Redis(REDIS_URL, {
    lazyConnect: true,
    maxRetriesPerRequest: 1,
    retryStrategy: () => null,
    enableOfflineQueue: false,
    connectTimeout: 1500,
  });
  client.on('error', () => {});

  try {
    await client.connect();
    return await operation(client);
  } finally {
    client.disconnect();
  }
}

function redisDatasetId(sessionId) {
  return `redis:${String(sessionId || '').trim()}`;
}

function parseDatasetId(datasetId) {
  const normalized = String(datasetId || '').trim();
  if (!normalized)
    throw new Error('dataset_id 不能为空');

  if (!normalized.startsWith('redis:'))
    throw new Error(`仅支持 redis 数据集: ${normalized}`);

  const sessionId = normalized.slice(6).trim();
  if (!sessionId)
    throw new Error('redis dataset_id 缺少 session_id');

  return {
    kind: 'redis',
    value: sessionId,
  };
}

function sessionMetaKey(sessionId) {
  return `${REDIS_SESSION_PREFIX}:session:${sessionId}:meta`;
}

function sessionNetworkKey(sessionId) {
  return `${REDIS_SESSION_PREFIX}:session:${sessionId}:network`;
}

function sessionsSetKey() {
  return `${REDIS_SESSION_PREFIX}:sessions`;
}

function sessionNetworkIndexBaseKey(sessionId) {
  return `${REDIS_SESSION_PREFIX}:session:${sessionId}:network:index`;
}

function sessionNetworkRecordsKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:records`;
}

function sessionNetworkSummariesKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:summaries`;
}

function sessionNetworkRecentKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:recent`;
}

function sessionNetworkFieldIndexKey(sessionId, kind, value) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:z:${kind}:${encodeIndexPart(value)}`;
}

function sessionNetworkStatsKey(sessionId, kind) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:stats:${kind}`;
}

function sessionNetworkEndpointCountsKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint-counts`;
}

function sessionNetworkEndpointMetaKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint-meta`;
}

function sessionNetworkEndpointMembersKey(sessionId, endpointId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:endpoint:${encodeIndexPart(endpointId)}`;
}

function sessionNetworkDurationKey(sessionId) {
  return `${sessionNetworkIndexBaseKey(sessionId)}:durations`;
}

function encodeIndexPart(value) {
  return Buffer.from(String(value || '').trim()).toString('base64url');
}

function sortByNewest(items, selector) {
  return [...items].sort((left, right) => {
    const leftTime = Date.parse(selector(left) || '') || 0;
    const rightTime = Date.parse(selector(right) || '') || 0;
    return rightTime - leftTime;
  });
}

function inferPageUrlFromMeta(meta) {
  return [
    meta.url,
    meta.start_url,
    meta.startUrl,
    meta.current_url,
    meta.currentUrl,
    meta.page_url,
    meta.pageUrl,
  ]
    .map(item => String(item || '').trim())
    .find(Boolean) || '';
}

function isWriteFilteredRedisMeta(meta) {
  const marker = String(
    meta?.networkFilterMode
      || meta?.network_filter_mode
      || meta?.networkFilterSource
      || meta?.network_filter_source
      || '',
  ).trim().toLowerCase();
  return marker.includes('write_filtered') || marker.includes('session_network_filter');
}

async function collectRedisSessionIds(client) {
  const ids = new Set();
  const members = await client.smembers(sessionsSetKey());
  for (const sessionId of members || [])
    ids.add(String(sessionId));

  const keys = await client.keys(`${REDIS_SESSION_PREFIX}:session:*:network`);
  for (const key of keys || []) {
    const match = String(key).match(new RegExp(`^${REDIS_SESSION_PREFIX}:session:(.+):network$`));
    if (match?.[1])
      ids.add(match[1]);
  }

  return Array.from(ids).filter(Boolean);
}

function parseStreamPayload(rawPayload) {
  if (!rawPayload)
    return null;
  try {
    const parsed = JSON.parse(rawPayload);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

function streamFieldsToMap(fields) {
  if (fields instanceof Map)
    return fields;

  if (Array.isArray(fields)) {
    if (!fields.length)
      return new Map();

    const first = fields[0];
    if (Array.isArray(first)) {
      return new Map(
        fields
          .filter(item => Array.isArray(item) && item.length >= 2)
          .map(item => [String(item[0] || ''), item[1]]),
      );
    }

    const normalized = new Map();
    for (let index = 0; index < fields.length; index += 2) {
      const key = fields[index];
      if (key == null)
        continue;
      normalized.set(String(key), index + 1 < fields.length ? fields[index + 1] : '');
    }
    return normalized;
  }

  if (fields && typeof fields === 'object')
    return new Map(Object.entries(fields));

  return new Map();
}

async function readRecentNetworkEntries(client, sessionId, limit, beforeStreamId) {
  const count = Math.max(1, Math.min(200, Number(limit) || 20));
  const args = [sessionNetworkKey(sessionId), beforeStreamId ? `(${beforeStreamId}` : '+', '-', 'COUNT', String(count)];
  const rows = await client.call('XREVRANGE', ...args);
  const items = Array.isArray(rows) ? rows : [];
  const entries = [];

  for (const row of items) {
    const streamId = Array.isArray(row) ? row[0] : '';
    const fields = Array.isArray(row) ? row[1] : [];
    const fieldMap = streamFieldsToMap(fields);
    const payload = parseStreamPayload(fieldMap.get('data'));
    if (!payload)
      continue;
    entries.push({
      stream_id: String(streamId || ''),
      payload,
    });
  }

  return {
    entries,
    next_cursor: entries.length ? entries[entries.length - 1].stream_id : null,
  };
}

async function listRedisDatasets(limit) {
  try {
    return await withRedis(async client => {
      const sessionIds = await collectRedisSessionIds(client);
      const items = [];

      for (const sessionId of sessionIds) {
        const [meta, count] = await Promise.all([
          client.hgetall(sessionMetaKey(sessionId)),
          client.xlen(sessionNetworkKey(sessionId)),
        ]);
        if (!count)
          continue;
        items.push({
          dataset_id: redisDatasetId(sessionId),
          source_type: 'redis',
          display_name: sessionId,
          session_id: sessionId,
          page_url: inferPageUrlFromMeta(meta || {}),
          exported_at: String(meta.updated_at || meta.updatedAt || meta.created_at || meta.createdAt || ''),
          raw_network_count: count,
          is_prefiltered: isWriteFilteredRedisMeta(meta || {}),
          index_available: Boolean(String(meta.networkIndexVersion || '').trim()),
          network_index_version: String(meta.networkIndexVersion || '').trim() || null,
        });
      }

      return sortByNewest(items, item => item.exported_at || item.session_id).slice(0, limit);
    });
  } catch {
    return [];
  }
}

async function loadRedisDataset(sessionId) {
  let payload;
  try {
    payload = await withRedis(async client => {
      const [meta, networkCount, latest] = await Promise.all([
        client.hgetall(sessionMetaKey(sessionId)),
        client.xlen(sessionNetworkKey(sessionId)),
        client.xrevrange(sessionNetworkKey(sessionId), '+', '-', 'COUNT', 1),
      ]);
      return { meta, networkCount, latest };
    });
  } catch {
    throw new Error(
      `无法连接 Redis 或读取会话 ${sessionId}。`
      + `请确认 REDIS_URL=${REDIS_URL} 可访问。`,
    );
  }

  const { meta, networkCount, latest } = payload;
  if (!networkCount)
    throw new Error(`Redis 数据集中没有网络记录: ${sessionId}`);

  const pageUrl = inferPageUrlFromMeta(meta || {});
  const latestRow = Array.isArray(latest) && latest.length ? latest[0] : null;
  const latestFields = latestRow ? streamFieldsToMap(latestRow[1]) : new Map();
  const latestPayload = parseStreamPayload(latestFields.get('data'));

  return {
    dataset_id: redisDatasetId(sessionId),
    source_type: 'redis',
    display_name: sessionId,
    session_id: sessionId,
    metadata: {
      dataset_id: redisDatasetId(sessionId),
      source_type: 'redis',
      display_name: sessionId,
      session_id: sessionId,
      page_url: pageUrl,
      exported_at: String(meta.updated_at || meta.updatedAt || meta.created_at || meta.createdAt || ''),
      raw_network_count: networkCount,
      is_prefiltered: isWriteFilteredRedisMeta(meta || {}),
      network_index_version: String(meta.networkIndexVersion || '').trim() || null,
      index_available: Boolean(String(meta.networkIndexVersion || '').trim()),
    },
    page_url: pageUrl,
    first_party_hosts: inferFirstPartyHosts({ pageUrl }),
    network_count: Number(networkCount || 0),
    is_prefiltered: isWriteFilteredRedisMeta(meta || {}),
    raw_available: false,
    index_available: Boolean(String(meta.networkIndexVersion || '').trim()),
    index_version: String(meta.networkIndexVersion || '').trim() || null,
    last_stream_id: latestRow ? String(latestRow[0] || '') : '',
    latest_timestamp: latestPayload ? String(latestPayload.timestamp || '') : '',
  };
}

async function listDatasets(options = {}) {
  const limit = Math.max(1, Math.min(200, Number(options.limit) || 50));
  return listRedisDatasets(limit);
}

async function loadDatasetContext(datasetId) {
  const parsed = parseDatasetId(datasetId);
  return loadRedisDataset(parsed.value);
}

module.exports = {
  encodeIndexPart,
  listDatasets,
  loadDatasetContext,
  parseDatasetId,
  readRecentNetworkEntries,
  redisDatasetId,
  sessionMetaKey,
  sessionNetworkDurationKey,
  sessionNetworkEndpointCountsKey,
  sessionNetworkEndpointMembersKey,
  sessionNetworkEndpointMetaKey,
  sessionNetworkFieldIndexKey,
  sessionNetworkKey,
  sessionNetworkRecordsKey,
  sessionNetworkRecentKey,
  sessionNetworkStatsKey,
  sessionNetworkSummariesKey,
  streamFieldsToMap,
  withRedis,
};
