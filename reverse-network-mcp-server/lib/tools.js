'use strict';

const z = require('zod');

const {
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
} = require('./analysis');
const { listDatasets, loadDatasetContext } = require('./datasets');

function toTextResult(payload) {
  const text = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
  return {
    content: [
      {
        type: 'text',
        text,
      },
    ],
  };
}

function toErrorResult(error) {
  const text = error instanceof Error ? error.message : String(error);
  return {
    isError: true,
    content: [
      {
        type: 'text',
        text,
      },
    ],
  };
}

const datasetIdShape = {
  dataset_id: z.string().describe('数据集标识，格式为 redis:<session_id>。'),
};

function withDatasetContext(fn) {
  return async args => {
    const context = await loadDatasetContext(args.dataset_id);
    return fn(context, args || {});
  };
}

function buildToolDefinitions() {
  return [
    {
      name: 'list_datasets',
      description: '列出当前可分析的 Redis 会话数据集。',
      inputShape: {
        limit: z.number().int().min(1).max(200).default(50).describe('返回数量上限。'),
      },
      handler: async args => toTextResult(await listDatasets(args || {})),
    },
    {
      name: 'get_dataset_overview',
      description: '获取某个数据集的轻量概览信息，包括请求规模、最近时间、过滤状态以及基于写入侧索引维护的 host / 方法 / 状态码 / mime 分布。',
      inputShape: datasetIdShape,
      handler: withDatasetContext(async context => toTextResult(await getDatasetOverview(context))),
    },
    {
      name: 'search_requests',
      description: '在指定数据集中按 URL、host、method、状态码以及 query/body/header 的字段名关键词搜索请求，底层走结构化索引，不会全量读取整个 session network。',
      inputShape: {
        ...datasetIdShape,
        url_contains: z.string().optional().describe('URL 中包含的关键词。'),
        host: z.string().optional().describe('精确匹配的 host。'),
        path_contains: z.string().optional().describe('path 中包含的关键词。'),
        method: z.string().optional().describe('HTTP 方法，例如 GET、POST。'),
        status_code: z.number().int().optional().describe('HTTP 状态码。'),
        mime_type_contains: z.string().optional().describe('mime type 中包含的关键词。'),
        query_key_search: z.string().optional().describe('query 参数字段名中包含的关键词。'),
        request_body_search: z.string().optional().describe('请求体字段名中包含的关键词。'),
        response_body_search: z.string().optional().describe('响应体字段名中包含的关键词。'),
        header_search: z.string().optional().describe('请求头或响应头字段名中包含的关键词。'),
        limit: z.number().int().min(1).max(200).default(20).describe('返回数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await searchRequests(context, args))),
    },
    {
      name: 'get_request_details',
      description: '按 request_id 获取指定请求的详情。默认只返回 schema 级信息；需要时可升级到 preview 或 full。',
      inputShape: {
        ...datasetIdShape,
        request_id: z.string().describe('请求唯一标识。'),
        detail_level: z.enum(['schema', 'preview', 'full']).default('schema').describe('详情粒度，默认 schema。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getRequestDetails(context, args))),
    },
    {
      name: 'get_recent_requests',
      description: '按时间倒序返回最近的请求摘要，优先使用 recent 索引，旧会话则回退到最近窗口读取。',
      inputShape: {
        ...datasetIdShape,
        limit: z.number().int().min(1).max(200).default(20).describe('返回数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getRecentRequests(context, args))),
    },
    {
      name: 'get_statistics',
      description: '获取过滤后请求的统计信息，包括总量、唯一 host、方法分布、状态码分布、mime 分布和 top endpoints。',
      inputShape: datasetIdShape,
      handler: withDatasetContext(async context => toTextResult(await getStatistics(context))),
    },
    {
      name: 'compare_requests',
      description: '比较两个请求在 method、URL、query、请求体、响应体、状态码和耗时上的差异。',
      inputShape: {
        ...datasetIdShape,
        request_id_a: z.string().describe('第一个请求 ID。'),
        request_id_b: z.string().describe('第二个请求 ID。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await compareRequests(context, args))),
    },
    {
      name: 'find_similar_requests',
      description: '查找与目标请求相似的请求，相似度基于 method、host、归一化路径、query key 集合和请求体 key 集合。',
      inputShape: {
        ...datasetIdShape,
        request_id: z.string().describe('目标请求 ID。'),
        limit: z.number().int().min(1).max(100).default(10).describe('返回数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await findSimilarRequests(context, args))),
    },
    {
      name: 'extract_api_endpoints',
      description: '提取疑似 API 端点，按 method + host + normalized path 聚合，并附带样例请求 ID 与轻量信号。',
      inputShape: {
        ...datasetIdShape,
        limit: z.number().int().min(1).max(200).default(100).describe('返回端点数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await extractApiEndpoints(context, args))),
    },
    {
      name: 'get_endpoint_group_summary',
      description: '获取某个 endpoint group 的聚合摘要，包括状态分布、常见字段、鉴权信号与代表请求。',
      inputShape: {
        ...datasetIdShape,
        endpoint: z.string().describe('endpoint 标识，格式通常为 METHOD host/normalized_path。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getEndpointGroupSummary(context, args))),
    },
    {
      name: 'get_endpoint_group_samples',
      description: '为某个 endpoint group 提取少量代表样本，支持 latest、diverse、error 三种策略。',
      inputShape: {
        ...datasetIdShape,
        endpoint: z.string().describe('endpoint 标识。'),
        strategy: z.enum(['latest', 'diverse', 'error']).default('diverse').describe('样本选择策略。'),
        limit: z.number().int().min(1).max(20).default(3).describe('返回样本数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getEndpointGroupSamples(context, args))),
    },
    {
      name: 'get_request_sequence_window',
      description: '围绕某个请求或 endpoint 返回时间邻近的请求摘要窗口，用于判断前后触发关系。',
      inputShape: {
        ...datasetIdShape,
        request_id: z.string().optional().describe('锚点请求 ID。'),
        endpoint: z.string().optional().describe('若未提供 request_id，则用该 endpoint 的最近请求作为锚点。'),
        before: z.number().int().min(0).max(20).default(3).describe('锚点前的请求数量。'),
        after: z.number().int().min(0).max(20).default(3).describe('锚点后的请求数量。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getRequestSequenceWindow(context, args))),
    },
    {
      name: 'rank_candidate_requests',
      description: '按逆向价值对候选请求做启发式排序，优先返回写操作、鉴权信号与高价值业务请求。',
      inputShape: {
        ...datasetIdShape,
        limit: z.number().int().min(1).max(30).default(10).describe('返回候选数量上限。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await rankCandidateRequests(context, args))),
    },
    {
      name: 'generate_code',
      description: '根据指定请求生成复现代码，支持 javascript、python 和 curl 三种格式。',
      inputShape: {
        ...datasetIdShape,
        request_id: z.string().describe('请求唯一标识。'),
        format: z.enum(['javascript', 'python', 'curl']).default('javascript').describe('代码格式。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await generateCode(context, args))),
    },
    {
      name: 'get_curl',
      description: '根据指定请求直接生成 cURL 命令。',
      inputShape: {
        ...datasetIdShape,
        request_id: z.string().describe('请求唯一标识。'),
      },
      handler: withDatasetContext(async (context, args) => toTextResult(await getCurl(context, args))),
    },
  ];
}

module.exports = {
  buildToolDefinitions,
  toErrorResult,
};
