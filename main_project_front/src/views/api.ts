import { getAuthSession } from '@/utils/auth';

export type AgentTag = 'browser_agent' | 'analyse_agent';
export type BrowserMode = 'roxy' | 'standalone';
export type LocalBrowserName = 'chrome' | 'chromium' | 'msedge' | 'firefox' | 'webkit';

export interface TaskStepSummary {
  key: 'browser_agent' | 'analyse_agent' | 'finish' | string;
  status: string;
  total: number;
  pending: number;
  queued: number;
  running: number;
  success: number;
  failed: number;
  skipped?: number;
}

export interface TaskExecutionStage {
  status: string;
  message?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface TaskExecutionToolItem {
  name: string;
  status: string;
  count: number;
}

export interface TaskExecutionItem {
  url: string;
  urlIndex: number;
  sessionId: string | null;
  browserStage: TaskExecutionStage;
  analyseStage: TaskExecutionStage;
  finalStatus: string;
  error: string | null;
  reportText: string;
  browserTools: TaskExecutionToolItem[];
  analyseTools: TaskExecutionToolItem[];
  createdAt: string;
  updatedAt: string;
}

export interface DashboardStats {
  health: string;
  requestTotal: number;
  processing: number;
  queued: number;
  completed: number;
  failed: number;
  snapshotAt?: string | null;
}

export interface DashboardTrendItem {
  timestamp: string;
  requestTotal: number;
  processing: number;
  queued: number;
  completed: number;
  failed: number;
}

export interface AutoReverseTaskItem {
  taskId: string;
  url: string;
  status: string;
  agentTag: AgentTag | string;
  createdAt: string;
  updatedAt: string;
}

export interface DashboardPayload {
  stats: DashboardStats;
  trend: DashboardTrendItem[];
  tasks: AutoReverseTaskItem[];
}

export interface AutoReverseTaskDeleteResult {
  taskId: string;
  deleted: boolean;
}

export interface RecentTaskClearResult {
  requested: number;
  deleted: number;
  skipped: number;
  deletedTaskIds: string[];
  skippedTaskIds: string[];
  deletedSessionCount: number;
  deletedSessionIds: string[];
}

export const FRONTEND_DEFAULT_ANALYSE_PROMPT = `你现在做逆向分析，只分析 reverse-network-mcp-server 提供的 redis:{session_id} 数据集。目标是在尽量小的上下文开销下，成功找出并还原最关键的业务请求。

规则：
- 禁止全量读取 network 数据
- 不要调用 legacy 的 read_network_log 工具，也不要输出整份 {session_id} 数据流
- 先用轻量工具快速缩小范围，再按需查看 endpoint、sample、detail、sequence 等更细信息
- 搜索优先用 host、path、method、status、query/body/header 字段名关键词
- 只有当你确认值得深挖时，才调用更重的详情工具
- 只有需要确认前后触发关系时才调用 get_request_sequence_window，只有需要解释页面动作与请求关系时才调用 get_session_log_window
- 忽略图片、样式、字体、静态资源、埋点和明显噪音请求
- 不要复述大段原始日志，只输出结论

重点关注：
- API、XHR、fetch、graphql、ajax
- 登录、鉴权、查询、提交、下单、分页、签名、token、nonce、session 相关请求

每个关键请求重点提炼：
- method
- host
- path
- 关键 query/body/header
- 关键响应字段
- 鉴权方式
- cookie、token、签名、时间戳、nonce、session、分页依赖

输出只给：
- 关键接口清单
- 鉴权与关键参数结论
- 最值得复现的请求
- 简短复现建议
- 一句话总结

如果首轮候选不足以完成逆向，继续缩小范围并补充详情分析，直到结论可靠。`;

export interface AutoReverseOptions {
  browserMode: BrowserMode;
  browserModes: BrowserMode[];
  debugModeIsolationEnabled: boolean;
  mcpTools: string[];
  lockedMcpTools: string[];
  lockedMcpToolsByMode: Record<string, string[]>;
  skills: string[];
  skillsEnabled: boolean;
  modelPool: ModelPoolEntry[];
  modelProfiles: ModelProfileOption[];
}

export type ModelProvider = 'deepseek' | 'chatgpt' | 'newapi' | 'claude' | 'gemini';

export interface ModelPoolEntry {
  provider: ModelProvider;
  label?: string;
  baseUrl: string;
  apiKey: string;
  apiKeyMasked: string;
  hasApiKey: boolean;
  availableModels: string[];
  defaultModel?: string;
  syncStatus: string;
  syncMessage?: string;
  enabled: boolean;
  locked: boolean;
}

export interface ModelProfileOption {
  key: string;
  label: string;
  provider: ModelProvider;
  model: string;
  baseUrl?: string;
  enabled: boolean;
}

export interface ModelProfileConfig extends ModelProfileOption {
  baseUrl: string;
  apiKey: string;
  apiKeyMasked: string;
  hasApiKey: boolean;
  locked: boolean;
}

export interface McpEntry {
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  status: string;
  locked: boolean;
}

export interface LocalBrowserScanResult {
  browser: LocalBrowserName | string;
  label: string;
  location: string;
  executablePath: string;
  source: string;
  available: boolean;
}

export interface SkillEntry {
  name: string;
  description: string;
  instructions: string;
  path: string;
  files: Record<string, string>;
  fileCount: number;
  depth: number;
  parentPath: string;
  locked: boolean;
  renderedSkillMd: string;
}

export interface SkillGeneratorConfig {
  enabled: boolean;
  modelProfileKey: string;
  referenceSkillNames: string[];
  systemPrompt: string;
  userPromptTemplate: string;
  temperature: number;
  outputMode: string;
  saveTarget: string;
  lastTargetName: string;
  lastPrompt: string;
  lastDraftId: string;
  lastGeneratedSkills: SkillEntry[];
}

export interface UsedModelSummary {
  provider: ModelProvider | string;
  model: string;
  profileKey: string;
}

export interface SkillGenerationResult {
  draftId: string;
  rootPath: string;
  generatedSkills: SkillEntry[];
  saved: boolean;
  usedModel: UsedModelSummary;
  warnings: string[];
}

export interface SkillDraftSummary {
  draftId: string;
  rootPath: string;
  skillCount: number;
  createdAt: string;
  source: string;
}

export interface SkillsCatalogPayload {
  currentVersion: string;
  updatedAt: string;
  entries: SkillEntry[];
  drafts: SkillDraftSummary[];
}

export interface AutoReverseConfigPayload {
  browserMode: BrowserMode;
  browserModes: BrowserMode[];
  debugModeIsolationEnabled: boolean;
  standaloneBrowser: string;
  standaloneExecutablePath: string;
  skills: string[];
  mcpTools: string[];
  lockedMcpTools: string[];
  lockedMcpToolsByMode: Record<string, string[]>;
  skillsEnabled: boolean;
  browserAgentSystemPrompt: string;
  standaloneBrowserAgentSystemPrompt: string;
  browserPrompt: string;
  standaloneBrowserPrompt: string;
  analysePrompt: string;
  mcpEntries: McpEntry[];
  modelPool: ModelPoolEntry[];
  modelProfiles: ModelProfileConfig[];
  skillGenerator: SkillGeneratorConfig;
}

export function buildAutoReverseOptionsFromConfigPayload(payload: AutoReverseConfigPayload): AutoReverseOptions {
  return {
    browserMode: payload.browserMode,
    browserModes: [...payload.browserModes],
    debugModeIsolationEnabled: payload.debugModeIsolationEnabled,
    mcpTools: [...payload.mcpTools],
    lockedMcpTools: [...payload.lockedMcpTools],
    lockedMcpToolsByMode: Object.fromEntries(
      Object.entries(payload.lockedMcpToolsByMode).map(([mode, tools]) => [mode, [...tools]]),
    ),
    skills: [...payload.skills],
    skillsEnabled: payload.skillsEnabled,
    modelPool: payload.modelPool.map((item) => ({
      ...item,
      availableModels: [...item.availableModels],
    })),
    modelProfiles: payload.modelProfiles.map((item) => ({
      key: item.key,
      label: item.label,
      provider: item.provider,
      model: item.model,
      baseUrl: item.baseUrl,
      enabled: item.enabled,
    })),
  };
}

export interface AgentResourceSelection {
  browserMode?: BrowserMode;
  mcpTools: string[];
  skills: string[];
  modelProvider?: string;
  modelName?: string;
  modelProfileKey: string;
}

export interface AutoReverseTaskStatus {
  taskId: string;
  status: string;
  urls: string[];
  steps: TaskStepSummary[];
  items: TaskExecutionItem[];
  stages: Array<{
    agentTag: AgentTag | string;
    status: string;
    message?: string;
    startedAt?: string;
    completedAt?: string;
  }>;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisResultItem {
  url: string;
  sessionId: string | null;
  success: boolean;
  reportText: string;
  error: string | null;
  createdAt: string;
}

export interface SuccessResultArchiveItem {
  id: number;
  taskId: string;
  url: string;
  sessionId: string | null;
  reportText: string;
  createdAt: string;
}

export interface SettingAccount {
  id: number;
  username: string;
  createdAt: string;
}

export interface LoginResult {
  accessToken: string;
  user: {
    id: number;
    username: string;
    createdAt: string;
  };
}

export interface BrowserTaskBootstrapPayload {
  skills: string[];
  skillsEnabled: boolean;
  modelProfiles: ModelProfileOption[];
  runtimeMode: string;
  persistenceMode: string;
  mcpSelectorHidden: boolean;
  systemPromptSource: string;
}

export interface BrowserTaskSessionState {
  sessionId: string;
  status: string;
  startUrl: string;
  currentUrl: string;
  pageTitle: string;
  tabCount: number;
  lastToolName: string;
  lastToolSummary: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface BrowserTaskMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | string;
  content: string;
  status: string;
  createdAt: string;
}

export interface BrowserTaskSessionCreatePayload {
  skills: string[];
  modelProfileKey: string;
}

export interface BrowserTaskSessionCreateResult {
  sessionId: string;
  bootstrapStarted: boolean;
  sessionState: BrowserTaskSessionState;
}

export interface BrowserTaskSendMessageResult {
  sessionId: string;
  messageId: string;
  accepted: boolean;
}

export interface BrowserTaskStopResult {
  sessionId: string;
  stopped: boolean;
  sessionState: BrowserTaskSessionState;
}

export interface BrowserTaskStreamEvent {
  type: string;
  payload: Record<string, unknown>;
}

export interface BrowserTaskStreamController {
  abort: () => void;
  done: Promise<void>;
}

function normalizeBaseUrl(value: string | null | undefined): string {
  return (value ?? '').trim().replace(/\/$/, '');
}

function isPrivateOrLocalAddress(hostname: string): boolean {
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
    return true;
  }
  const ipv4Parts = hostname.split('.');
  if (ipv4Parts.length !== 4 || ipv4Parts.some((part) => !/^\d+$/.test(part))) {
    return false;
  }
  const [a, b] = ipv4Parts.map((part) => Number(part));
  return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
}

function detectApiBase(): string {
  if (typeof window === 'undefined') {
    return '';
  }

  const localStorageBase = normalizeBaseUrl(window.localStorage.getItem('api-base-url'));
  if (localStorageBase) {
    return localStorageBase;
  }

  const envBase = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
  if (envBase) {
    return envBase;
  }

  const { protocol, hostname, port } = window.location;
  const apiPort = import.meta.env.VITE_API_FALLBACK_PORT ?? '8000';

  // 本机 IP / 局域网 IP 默认走同主机 8000 端口。
  if (isPrivateOrLocalAddress(hostname) || port === '5173') {
    return `${protocol}//${hostname}:${apiPort}`;
  }

  // 域名默认走同域名（通常由网关或反向代理转发 /api）。
  return `${protocol}//${hostname}`;
}

const API_BASE = detectApiBase();
const DASHBOARD_PAYLOAD_MAX_AGE = 1200;
const DEFAULT_LOCKED_MCP_TOOLS_BY_MODE: Record<BrowserMode, string[]> = {
  roxy: ['roxybrowser-mcp-server', 'roxybrowser-playwright-mcp-main'],
  standalone: ['roxybrowser-playwright-mcp-main'],
};

function normalizeBrowserMode(value: string | null | undefined): BrowserMode {
  return value === 'standalone' ? 'standalone' : 'roxy';
}

function normalizeLocalBrowserName(value: string | null | undefined): LocalBrowserName | string {
  const normalized = (value ?? '').trim().toLowerCase();
  if (normalized === 'chrome' || normalized === 'chromium' || normalized === 'msedge' || normalized === 'firefox' || normalized === 'webkit') {
    return normalized;
  }
  return value ?? '';
}

function normalizeLockedMcpToolsByMode(
  value: Record<string, string[] | null | undefined> | null | undefined,
): Record<string, string[]> {
  const normalized: Record<string, string[]> = {
    roxy: [...DEFAULT_LOCKED_MCP_TOOLS_BY_MODE.roxy],
    standalone: [...DEFAULT_LOCKED_MCP_TOOLS_BY_MODE.standalone],
  };
  for (const [mode, items] of Object.entries(value ?? {})) {
    normalized[mode] = Array.isArray(items) ? Array.from(new Set(items.map((item) => String(item).trim()).filter(Boolean))) : [];
  }
  return normalized;
}

let dashboardPayloadCache: DashboardPayload | null = null;
let dashboardPayloadCachedAt = 0;
let dashboardPayloadPending: Promise<DashboardPayload> | null = null;
let dashboardPayloadRequestVersion = 0;

function buildUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return API_BASE ? `${API_BASE}${normalized}` : normalized;
}

function buildAuthHeaders(init?: HeadersInit): Headers {
  const session = getAuthSession();
  const headers = new Headers(init ?? {});
  if (session?.token) {
    headers.set('Authorization', `Bearer ${session.token}`);
  }
  return headers;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = buildAuthHeaders(init?.headers);

  if (!headers.has('Content-Type') && init?.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(buildUrl(path), { ...init, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}${text ? `: ${text}` : ''}`);
  }
  return (await response.json()) as T;
}

export function invalidateDashboardPayloadCache(): void {
  dashboardPayloadCache = null;
  dashboardPayloadCachedAt = 0;
  dashboardPayloadPending = null;
  dashboardPayloadRequestVersion += 1;
}

export async function loginByApi(username: string, password: string): Promise<LoginResult> {
  const token = await requestJson<{ access_token: string }>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  const me = await requestJson<{ id: number; username: string; created_at: string }>('/api/v1/auth/me', {
    headers: { Authorization: `Bearer ${token.access_token}` },
  });
  return {
    accessToken: token.access_token,
    user: {
      id: me.id,
      username: me.username,
      createdAt: me.created_at,
    },
  };
}

export async function fetchDashboardPayload(options?: { force?: boolean; maxAge?: number }): Promise<DashboardPayload> {
  const maxAge = options?.maxAge ?? DASHBOARD_PAYLOAD_MAX_AGE;
  const force = options?.force ?? false;
  const now = Date.now();

  if (dashboardPayloadPending && !force) {
    return dashboardPayloadPending;
  }

  if (!force && dashboardPayloadCache && now - dashboardPayloadCachedAt < maxAge) {
    return dashboardPayloadCache;
  }

  const requestVersion = ++dashboardPayloadRequestVersion;
  const pendingPromise = (async () => {
    const payloadResponse = await requestJson<{
      stats: {
        health: string;
        request_total: number;
        processing: number;
        queued?: number;
        completed: number;
        failed?: number;
        snapshot_at?: string | null;
      };
      trend: Array<{ timestamp: string; request_total: number; processing: number; queued?: number; completed: number; failed?: number }>;
      tasks: Array<{ task_id: string; url: string; status: string; agent_tag: string; created_at: string; updated_at: string }>;
    }>('/api/v1/dashboard/payload');

    const payload: DashboardPayload = {
      stats: {
        health: payloadResponse.stats.health,
        requestTotal: payloadResponse.stats.request_total,
        processing: payloadResponse.stats.processing,
        queued: payloadResponse.stats.queued ?? 0,
        completed: payloadResponse.stats.completed,
        failed: payloadResponse.stats.failed ?? 0,
        snapshotAt: payloadResponse.stats.snapshot_at ?? null,
      },
      trend: payloadResponse.trend.map((item) => ({
        timestamp: item.timestamp,
        requestTotal: item.request_total,
        processing: item.processing,
        queued: item.queued ?? 0,
        completed: item.completed,
        failed: item.failed ?? 0,
      })),
      tasks: payloadResponse.tasks.map((item) => ({
        taskId: item.task_id,
        url: item.url,
        status: item.status,
        agentTag: item.agent_tag,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
      })),
    };

    if (requestVersion === dashboardPayloadRequestVersion) {
      dashboardPayloadCache = payload;
      dashboardPayloadCachedAt = Date.now();
    }
    return payload;
  })();
  dashboardPayloadPending = pendingPromise;

  try {
    return await pendingPromise;
  } finally {
    if (dashboardPayloadPending === pendingPromise) {
      dashboardPayloadPending = null;
    }
  }
}

export async function deleteAutoReverseTaskByApi(taskId: string): Promise<AutoReverseTaskDeleteResult> {
  const response = await requestJson<{ task_id: string; deleted: boolean }>(
    `/api/v1/auto-reverse/tasks/${encodeURIComponent(taskId)}`,
    {
      method: 'DELETE',
    },
  );
  invalidateDashboardPayloadCache();
  return {
    taskId: response.task_id,
    deleted: response.deleted,
  };
}

export async function clearRecentAutoReverseTasksByApi(limit: number): Promise<RecentTaskClearResult> {
  const response = await requestJson<{
    requested: number;
    deleted: number;
    skipped: number;
    deleted_task_ids: string[];
    skipped_task_ids: string[];
    deleted_session_count?: number;
    deleted_session_ids?: string[];
  }>(`/api/v1/auto-reverse/tasks/clear-recent?limit=${encodeURIComponent(String(limit))}`, {
    method: 'DELETE',
  });
  invalidateDashboardPayloadCache();
  return {
    requested: response.requested,
    deleted: response.deleted,
    skipped: response.skipped,
    deletedTaskIds: response.deleted_task_ids ?? [],
    skippedTaskIds: response.skipped_task_ids ?? [],
    deletedSessionCount: response.deleted_session_count ?? 0,
    deletedSessionIds: response.deleted_session_ids ?? [],
  };
}

export async function clearFailedAutoReverseTasksByApi(): Promise<RecentTaskClearResult> {
  const response = await requestJson<{
    requested: number;
    deleted: number;
    skipped: number;
    deleted_task_ids: string[];
    skipped_task_ids: string[];
    deleted_session_count?: number;
    deleted_session_ids?: string[];
  }>('/api/v1/auto-reverse/tasks/clear-failed', {
    method: 'DELETE',
  });
  invalidateDashboardPayloadCache();
  return {
    requested: response.requested,
    deleted: response.deleted,
    skipped: response.skipped,
    deletedTaskIds: response.deleted_task_ids ?? [],
    skippedTaskIds: response.skipped_task_ids ?? [],
    deletedSessionCount: response.deleted_session_count ?? 0,
    deletedSessionIds: response.deleted_session_ids ?? [],
  };
}

export async function clearAllAutoReverseTasksByApi(): Promise<RecentTaskClearResult> {
  const response = await requestJson<{
    requested: number;
    deleted: number;
    skipped: number;
    deleted_task_ids: string[];
    skipped_task_ids: string[];
    deleted_session_count?: number;
    deleted_session_ids?: string[];
  }>('/api/v1/auto-reverse/tasks/clear-all', {
    method: 'DELETE',
  });
  invalidateDashboardPayloadCache();
  return {
    requested: response.requested,
    deleted: response.deleted,
    skipped: response.skipped,
    deletedTaskIds: response.deleted_task_ids ?? [],
    skippedTaskIds: response.skipped_task_ids ?? [],
    deletedSessionCount: response.deleted_session_count ?? 0,
    deletedSessionIds: response.deleted_session_ids ?? [],
  };
}

const MODEL_PROVIDER_LABELS: Record<ModelProvider, string> = {
  deepseek: 'DeepSeek',
  chatgpt: 'ChatGPT',
  newapi: 'NewAPI',
  claude: 'Claude',
  gemini: 'Gemini',
};

function toModelPoolEntry(item: {
  provider: ModelProvider;
  label?: string | null;
  base_url?: string | null;
  api_key?: string | null;
  api_key_masked?: string | null;
  has_api_key?: boolean;
  available_models?: string[] | null;
  default_model?: string | null;
  sync_status?: string | null;
  sync_message?: string | null;
  enabled?: boolean;
  locked?: boolean;
}): ModelPoolEntry {
  return {
    provider: item.provider,
    label: item.label ?? MODEL_PROVIDER_LABELS[item.provider],
    baseUrl: item.base_url ?? '',
    apiKey: item.api_key ?? '',
    apiKeyMasked: item.api_key_masked ?? '',
    hasApiKey: item.has_api_key ?? false,
    availableModels: item.available_models ?? [],
    defaultModel: item.default_model ?? '',
    syncStatus: item.sync_status ?? 'idle',
    syncMessage: item.sync_message ?? '',
    enabled: item.enabled ?? true,
    locked: item.locked ?? false,
  };
}

function toModelProfileOption(
  item: {
    key?: string | null;
    label?: string | null;
    provider?: ModelProvider | null;
    model?: string | null;
    base_url?: string | null;
    baseUrl?: string;
    enabled?: boolean;
  },
): ModelProfileOption | null {
  const key = item.key?.trim() ?? '';
  const label = item.label?.trim() ?? '';
  const provider = item.provider ?? undefined;
  const model = item.model?.trim() ?? '';
  if (!key || !label || !provider || !model) {
    return null;
  }
  return {
    key,
    label,
    provider,
    model,
    baseUrl: (item.base_url ?? item.baseUrl ?? '').trim(),
    enabled: item.enabled ?? true,
  };
}

function toModelProfileConfig(
  item: {
    key?: string | null;
    label?: string | null;
    provider?: ModelProvider | null;
    model?: string | null;
    base_url?: string | null;
    api_key_masked?: string | null;
    has_api_key?: boolean;
    enabled?: boolean;
    locked?: boolean;
  },
): ModelProfileConfig | null {
  const option = toModelProfileOption(item);
  if (!option) {
    return null;
  }
  return {
    ...option,
    baseUrl: option.baseUrl ?? '',
    apiKey: '',
    apiKeyMasked: item.api_key_masked ?? '',
    hasApiKey: item.has_api_key ?? false,
    enabled: item.enabled ?? true,
    locked: item.locked ?? false,
  };
}

function profilesToModelPool(profiles: ModelProfileConfig[], existingPool: ModelPoolEntry[] = []): ModelPoolEntry[] {
  const merged = new Map<ModelProvider, ModelPoolEntry>();
  for (const item of existingPool) {
    merged.set(item.provider, { ...item, availableModels: [...item.availableModels] });
  }
  for (const profile of profiles) {
    const current = merged.get(profile.provider) ?? {
      provider: profile.provider,
      label: MODEL_PROVIDER_LABELS[profile.provider],
      baseUrl: '',
      apiKey: '',
      apiKeyMasked: '',
      hasApiKey: false,
      availableModels: [],
      defaultModel: '',
      syncStatus: 'idle',
      syncMessage: '',
      enabled: true,
      locked: false,
    };
    if (profile.baseUrl) current.baseUrl = profile.baseUrl;
    if (profile.apiKey) current.apiKey = profile.apiKey;
    if (profile.apiKeyMasked) current.apiKeyMasked = profile.apiKeyMasked;
    current.hasApiKey = current.hasApiKey || profile.hasApiKey || Boolean(profile.apiKey || profile.apiKeyMasked);
    current.enabled = profile.enabled;
    current.locked = profile.locked;
    if (profile.model && !current.availableModels.includes(profile.model)) {
      current.availableModels.push(profile.model);
    }
    if (!current.defaultModel && profile.model) {
      current.defaultModel = profile.model;
    }
    merged.set(profile.provider, current);
  }
  return Array.from(merged.values());
}

function splitModelProfileKey(modelProfileKey: string): { provider?: string; modelName?: string } {
  const raw = modelProfileKey.trim();
  if (!raw || !raw.includes(':')) {
    return {};
  }
  const [provider, ...rest] = raw.split(':');
  return {
    provider: provider.trim(),
    modelName: rest.join(':').trim(),
  };
}

const SKILL_NAME_PATTERN = /^[a-z](?:[a-z0-9]|-(?!-)){0,62}[a-z0-9]$|^[a-z]$/;

export function isValidSkillName(value: string): boolean {
  return SKILL_NAME_PATTERN.test(value.trim());
}

type SkillMarkdownParts = {
  name: string;
  description: string;
  instructions: string;
};

function escapeFrontmatterValue(value: string): string {
  return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

function parseSkillMarkdown(markdown: string): Partial<SkillMarkdownParts> {
  const text = markdown.trim();
  if (!text.startsWith('---')) {
    return { instructions: text };
  }

  const parts = text.split('---');
  if (parts.length < 3) {
    return { instructions: text };
  }

  const metadataText = parts[1] ?? '';
  const instructions = parts.slice(2).join('---').trim();
  const metadata: Record<string, string> = {};
  for (const line of metadataText.split('\n')) {
    const separatorIndex = line.indexOf(':');
    if (separatorIndex === -1) {
      continue;
    }
    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim().replace(/^['"]|['"]$/g, '');
    if (key) {
      metadata[key] = value;
    }
  }

  return {
    name: metadata.name ?? '',
    description: metadata.description ?? '',
    instructions,
  };
}

export function renderSkillMarkdown(entry: Pick<SkillEntry, 'name' | 'description' | 'instructions'>): string {
  const name = entry.name.trim();
  const description = entry.description.trim();
  const instructions = entry.instructions.trim();
  return [
    '---',
    `name: ${escapeFrontmatterValue(name)}`,
    `description: ${escapeFrontmatterValue(description)}`,
    '---',
    '',
    instructions,
    '',
  ].join('\n');
}

function getSkillPathLeaf(path: string): string {
  const normalized = String(path ?? '').trim().replace(/^\/+|\/+$/g, '');
  if (!normalized) {
    return '';
  }
  const segments = normalized.split('/').filter(Boolean);
  return segments[segments.length - 1] ?? '';
}

function toSkillEntry(item: {
  name?: string | null;
  description?: string | null;
  instructions?: string | null;
  skill_path?: string | null;
  path?: string | null;
  content?: string | null;
  files?: Record<string, string> | null;
  file_count?: number | null;
  depth?: number | null;
  parent_path?: string | null;
  rendered_skill_md?: string | null;
  locked?: boolean | null;
}): SkillEntry {
  const rawMarkdown = String(item.rendered_skill_md ?? item.content ?? item.files?.['SKILL.md'] ?? '').trim();
  const parsed = parseSkillMarkdown(rawMarkdown);
  const path = String(item.skill_path ?? item.path ?? item.name ?? '').trim().replace(/^\/+|\/+$/g, '');
  const name = String(item.name ?? parsed.name ?? getSkillPathLeaf(path) ?? '').trim();
  const description = String(item.description ?? parsed.description ?? '').trim();
  const instructions = String(item.instructions ?? parsed.instructions ?? '').trim();
  const renderedSkillMd = rawMarkdown || renderSkillMarkdown({ name, description, instructions });
  const files = item.files && Object.keys(item.files).length > 0 ? item.files : { 'SKILL.md': renderedSkillMd };
  return {
    name,
    description,
    instructions,
    path,
    files,
    fileCount: item.file_count ?? Object.keys(files).length,
    depth: Number.isFinite(item.depth) ? Number(item.depth) : path.split('/').filter(Boolean).length,
    parentPath: String(item.parent_path ?? path.split('/').slice(0, -1).join('/')).trim(),
    locked: item.locked === true,
    renderedSkillMd,
  };
}

export function buildSkillEntryFromMarkdown(payload: {
  name?: string;
  path?: string;
  markdown: string;
  files?: Record<string, string>;
  fileCount?: number;
  locked?: boolean;
}): SkillEntry {
  return toSkillEntry({
    name: payload.name,
    skill_path: payload.path,
    path: payload.path,
    content: payload.markdown,
    files: payload.files,
    file_count: payload.fileCount,
    locked: payload.locked,
  });
}

function toSkillGeneratorConfig(
  payload?: {
    enabled?: boolean | null;
    model_profile_key?: string | null;
    reference_skill_names?: string[] | null;
    reference_skill_paths?: string[] | null;
    system_prompt?: string | null;
    user_prompt_template?: string | null;
    temperature?: number | null;
    output_mode?: string | null;
    save_target?: string | null;
    last_target_name?: string | null;
    last_prompt?: string | null;
    last_draft_id?: string | null;
    last_generated_skills?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked?: boolean | null;
    }> | null;
  } | null,
): SkillGeneratorConfig {
  return {
    enabled: payload?.enabled !== false,
    modelProfileKey: String(payload?.model_profile_key ?? '').trim(),
    referenceSkillNames: (payload?.reference_skill_names ?? payload?.reference_skill_paths ?? []).map((item) => String(item).trim()).filter(Boolean),
    systemPrompt: String(payload?.system_prompt ?? '').trim(),
    userPromptTemplate: String(payload?.user_prompt_template ?? '').trim(),
    temperature: Number.isFinite(payload?.temperature) ? Number(payload?.temperature) : 0.2,
    outputMode: String(payload?.output_mode ?? 'skill_files').trim() || 'skill_files',
    saveTarget: String(payload?.save_target ?? 'backend').trim() || 'backend',
    lastTargetName: String(payload?.last_target_name ?? '').trim(),
    lastPrompt: String(payload?.last_prompt ?? ''),
    lastDraftId: String(payload?.last_draft_id ?? '').trim(),
    lastGeneratedSkills: (payload?.last_generated_skills ?? []).map((item) => toSkillEntry(item)),
  };
}

function toSkillsCatalogPayload(payload: {
  current_version?: string | null;
  updated_at?: string | null;
  entries?: Array<{
    name?: string | null;
    description?: string | null;
    instructions?: string | null;
    skill_path?: string | null;
    path?: string | null;
    content?: string | null;
    files?: Record<string, string> | null;
    file_count?: number | null;
    depth?: number | null;
    parent_path?: string | null;
    rendered_skill_md?: string | null;
    locked?: boolean | null;
  }> | null;
  drafts?: Array<{
    draft_id?: string | null;
    root_path?: string | null;
    skill_count?: number | null;
    entry_count?: number | null;
    created_at?: string | null;
    source?: string | null;
  }> | null;
}): SkillsCatalogPayload {
  return {
    currentVersion: String(payload.current_version ?? '').trim(),
    updatedAt: String(payload.updated_at ?? '').trim(),
    entries: (payload.entries ?? []).map((item) => toSkillEntry(item)),
    drafts: (payload.drafts ?? []).map((item) => ({
      draftId: String(item.draft_id ?? '').trim(),
      rootPath: String(item.root_path ?? '').trim(),
      skillCount: Number(item.skill_count ?? item.entry_count ?? 0),
      createdAt: String(item.created_at ?? '').trim(),
      source: String(item.source ?? 'generator').trim() || 'generator',
    })),
  };
}

export async function fetchAutoReverseOptions(): Promise<AutoReverseOptions> {
  const payload = await requestJson<{
    browser_mode?: string | null;
    browser_modes?: string[] | null;
    debug_mode_isolation_enabled?: boolean | null;
    mcp_tools: string[];
    locked_mcp_tools: string[];
    locked_mcp_tools_by_mode?: Record<string, string[] | null> | null;
    skills: string[];
    skills_enabled: boolean;
    model_pool?: Array<{
      provider: ModelProvider;
      label?: string | null;
      base_url?: string | null;
      api_key?: string | null;
      api_key_masked?: string | null;
      has_api_key?: boolean;
      available_models?: string[] | null;
      default_model?: string | null;
      sync_status?: string | null;
      sync_message?: string | null;
      enabled?: boolean;
      locked?: boolean;
    }>;
    model_profiles?: Array<{
      key: string;
      label: string;
      provider: ModelProvider;
      model: string;
      base_url?: string | null;
      enabled: boolean;
    }>;
  }>('/api/v1/auto-reverse/options');

  const modelPool = (payload.model_pool ?? []).map(toModelPoolEntry);
  const fallbackProfiles = modelPool.flatMap((entry) =>
    (entry.availableModels ?? []).map((model) => ({
      key: `${entry.provider}:${model}`,
      label: `${entry.label ?? MODEL_PROVIDER_LABELS[entry.provider]} / ${model}`,
      provider: entry.provider,
      model,
      baseUrl: entry.baseUrl,
      enabled: entry.enabled,
    })),
  );
  const parsedModelProfiles = (payload.model_profiles ?? []).map((item) => toModelProfileOption(item)).filter((item): item is ModelProfileOption => Boolean(item));

  return {
    browserMode: normalizeBrowserMode(payload.browser_mode),
    browserModes: (payload.browser_modes ?? []).map((item) => normalizeBrowserMode(item)).filter((item, index, list) => list.indexOf(item) === index),
    debugModeIsolationEnabled: payload.debug_mode_isolation_enabled ?? true,
    mcpTools: payload.mcp_tools,
    lockedMcpTools: payload.locked_mcp_tools,
    lockedMcpToolsByMode: normalizeLockedMcpToolsByMode(payload.locked_mcp_tools_by_mode),
    skills: payload.skills,
    skillsEnabled: payload.skills_enabled,
    modelPool,
    modelProfiles: parsedModelProfiles.length > 0 ? parsedModelProfiles : fallbackProfiles,
  };
}

export async function fetchAutoReverseConfig(): Promise<AutoReverseConfigPayload> {
  const payload = await requestJson<{
    browser_mode?: string | null;
    browser_modes?: string[] | null;
    debug_mode_isolation_enabled?: boolean | null;
    standalone_browser?: string | null;
    standalone_executable_path?: string | null;
    skills: string[] | null;
    mcp_tools: string[] | null;
    locked_mcp_tools: string[] | null;
    locked_mcp_tools_by_mode?: Record<string, string[] | null> | null;
    skills_enabled: boolean | null;
    browser_agent_system_prompt: string | null;
    standalone_browser_agent_system_prompt?: string | null;
    browser_prompt: string | null;
    standalone_browser_prompt?: string | null;
    analyse_prompt: string | null;
    mcp_entries: Array<{ name: string; command: string; args: string[]; env: Record<string, string>; status?: string; locked: boolean }> | null;
    skill_generator?: {
      enabled?: boolean | null;
      model_profile_key?: string | null;
      reference_skill_names?: string[] | null;
      reference_skill_paths?: string[] | null;
      system_prompt?: string | null;
      user_prompt_template?: string | null;
      temperature?: number | null;
      output_mode?: string | null;
      save_target?: string | null;
      last_target_name?: string | null;
      last_prompt?: string | null;
      last_draft_id?: string | null;
      last_generated_skills?: Array<{
        name?: string | null;
        description?: string | null;
        instructions?: string | null;
        skill_path?: string | null;
        path?: string | null;
        content?: string | null;
        files?: Record<string, string> | null;
        file_count?: number | null;
        depth?: number | null;
        parent_path?: string | null;
        rendered_skill_md?: string | null;
        locked?: boolean | null;
      }> | null;
    } | null;
    model_pool?: Array<{
      provider: ModelProvider;
      label?: string | null;
      base_url?: string | null;
      api_key?: string | null;
      api_key_masked?: string | null;
      has_api_key?: boolean;
      available_models?: string[] | null;
      default_model?: string | null;
      sync_status?: string | null;
      sync_message?: string | null;
      enabled?: boolean;
      locked?: boolean;
    }> | null;
    model_profiles?: Array<{
      key: string;
      label: string;
      provider: ModelProvider;
      model: string;
      base_url: string | null;
      api_key_masked?: string | null;
      has_api_key?: boolean;
      enabled: boolean;
      locked: boolean;
    }> | null;
  }>('/api/v1/auto-reverse/config');

  const modelPool = (payload.model_pool ?? []).map(toModelPoolEntry);
  const fallbackProfiles = modelPool.flatMap((entry) =>
    (entry.availableModels ?? []).map((model) => ({
      key: `${entry.provider}:${model}`,
      label: `${entry.label ?? MODEL_PROVIDER_LABELS[entry.provider]} / ${model}`,
      provider: entry.provider,
      model,
      baseUrl: entry.baseUrl,
      apiKey: '',
      apiKeyMasked: entry.apiKeyMasked,
      hasApiKey: entry.hasApiKey,
      enabled: entry.enabled,
      locked: entry.locked,
    })),
  );
  const rawModelProfiles = payload.model_profiles ?? [];
  const parsedModelProfiles = rawModelProfiles.map((item) => toModelProfileConfig(item)).filter((item): item is ModelProfileConfig => Boolean(item));
  const modelProfiles = parsedModelProfiles.length > 0 ? parsedModelProfiles : fallbackProfiles;

  return {
    browserMode: normalizeBrowserMode(payload.browser_mode),
    browserModes: (payload.browser_modes ?? []).map((item) => normalizeBrowserMode(item)).filter((item, index, list) => list.indexOf(item) === index),
    debugModeIsolationEnabled: payload.debug_mode_isolation_enabled ?? true,
    standaloneBrowser: String(payload.standalone_browser ?? ''),
    standaloneExecutablePath: String(payload.standalone_executable_path ?? ''),
    skills: payload.skills ?? [],
    mcpTools: payload.mcp_tools ?? [],
    lockedMcpTools: payload.locked_mcp_tools ?? [],
    lockedMcpToolsByMode: normalizeLockedMcpToolsByMode(payload.locked_mcp_tools_by_mode),
    skillsEnabled: payload.skills_enabled ?? false,
    browserAgentSystemPrompt: payload.browser_agent_system_prompt ?? '',
    standaloneBrowserAgentSystemPrompt: payload.standalone_browser_agent_system_prompt ?? '',
    browserPrompt: payload.browser_prompt ?? '',
    standaloneBrowserPrompt: payload.standalone_browser_prompt ?? '',
    analysePrompt: payload.analyse_prompt ?? '',
    mcpEntries: (payload.mcp_entries ?? []).map((item) => ({
      name: item.name,
      command: item.command,
      args: item.args ?? [],
      env: item.env ?? {},
      status: item.status ?? 'configured',
      locked: item.locked,
    })),
    modelPool,
    modelProfiles,
    skillGenerator: toSkillGeneratorConfig(payload.skill_generator),
  };
}

export async function saveAutoReverseConfig(payload: AutoReverseConfigPayload): Promise<void> {
  const normalizedModelPool = payload.modelPool.length > 0 ? payload.modelPool : profilesToModelPool(payload.modelProfiles, payload.modelPool);
  await requestJson('/api/v1/auto-reverse/config', {
    method: 'PUT',
    body: JSON.stringify({
      browser_mode: payload.browserMode,
      browser_modes: payload.browserModes,
      debug_mode_isolation_enabled: payload.debugModeIsolationEnabled,
      standalone_browser: payload.standaloneBrowser,
      standalone_executable_path: payload.standaloneExecutablePath,
      skills: payload.skills,
      mcp_tools: payload.mcpTools,
      locked_mcp_tools: payload.lockedMcpTools,
      locked_mcp_tools_by_mode: payload.lockedMcpToolsByMode,
      skills_enabled: payload.skillsEnabled,
      browser_agent_system_prompt: payload.browserAgentSystemPrompt,
      standalone_browser_agent_system_prompt: payload.standaloneBrowserAgentSystemPrompt,
      browser_prompt: payload.browserPrompt,
      standalone_browser_prompt: payload.standaloneBrowserPrompt,
      analyse_prompt: payload.analysePrompt,
      mcp_entries: payload.mcpEntries.map((item) => ({
        name: item.name,
        command: item.command,
        args: item.args,
        env: item.env,
        status: item.status,
        locked: item.locked,
      })),
      skill_generator: {
        enabled: payload.skillGenerator.enabled,
        model_profile_key: payload.skillGenerator.modelProfileKey,
        reference_skill_names: payload.skillGenerator.referenceSkillNames,
        reference_skill_paths: payload.skillGenerator.referenceSkillNames,
        system_prompt: payload.skillGenerator.systemPrompt,
        user_prompt_template: payload.skillGenerator.userPromptTemplate,
        temperature: payload.skillGenerator.temperature,
        output_mode: payload.skillGenerator.outputMode,
        save_target: payload.skillGenerator.saveTarget,
        last_target_name: payload.skillGenerator.lastTargetName,
        last_prompt: payload.skillGenerator.lastPrompt,
        last_draft_id: payload.skillGenerator.lastDraftId,
        last_generated_skills: [],
      },
      model_pool: normalizedModelPool.map((item) => ({
        provider: item.provider,
        label: item.label,
        base_url: item.baseUrl,
        api_key: item.apiKey,
        api_key_masked: item.apiKeyMasked,
        has_api_key: item.hasApiKey,
        available_models: item.availableModels,
        default_model: item.defaultModel,
        sync_status: item.syncStatus,
        sync_message: item.syncMessage,
        enabled: item.enabled,
        locked: item.locked,
      })),
      model_profiles: payload.modelProfiles.map((item) => ({
        key: item.key,
        label: item.label,
        provider: item.provider,
        model: item.model,
        base_url: item.baseUrl,
        api_key: item.apiKey,
        api_key_masked: item.apiKeyMasked,
        has_api_key: item.hasApiKey,
        enabled: item.enabled,
        locked: item.locked,
      })),
    }),
  });
}

export async function fetchSkillsCatalogByApi(): Promise<SkillsCatalogPayload> {
  const payload = await requestJson<{
    current_version?: string | null;
    updated_at?: string | null;
    entries?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked?: boolean | null;
    }> | null;
    drafts?: Array<{
      draft_id?: string | null;
      root_path?: string | null;
      skill_count?: number | null;
      entry_count?: number | null;
      created_at?: string | null;
      source?: string | null;
    }> | null;
  }>('/api/v1/auto-reverse/skills/catalog');

  return toSkillsCatalogPayload(payload);
}

export async function saveSkillsCatalogByApi(entries: SkillEntry[]): Promise<SkillsCatalogPayload> {
  const payload = await requestJson<{
    current_version?: string | null;
    updated_at?: string | null;
    entries?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked?: boolean | null;
    }> | null;
    drafts?: Array<{
      draft_id?: string | null;
      root_path?: string | null;
      skill_count?: number | null;
      entry_count?: number | null;
      created_at?: string | null;
      source?: string | null;
    }> | null;
  }>('/api/v1/auto-reverse/skills', {
    method: 'PUT',
    body: JSON.stringify({
      entries: entries.map((item) => ({
        name: item.name,
        description: item.description,
        instructions: item.instructions,
        path: item.path ?? item.name,
        content: item.renderedSkillMd,
        files: item.files,
        file_count: item.fileCount,
        rendered_skill_md: item.renderedSkillMd,
        locked: item.locked,
      })),
    }),
  });

  return toSkillsCatalogPayload(payload);
}

export async function generateSkillByApi(payload: {
  targetName: string;
  prompt: string;
  modelProfileKey: string;
  referenceSkillNames: string[];
  systemPrompt?: string;
  userPromptTemplate?: string;
  temperature?: number;
  saveAfterGenerate?: boolean;
  overwriteExisting?: boolean;
}): Promise<SkillGenerationResult> {
  const result = await requestJson<{
    root_path?: string | null;
    draft_id?: string | null;
    generated_skills?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked: boolean;
    }> | null;
    generated_skill: {
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked: boolean;
    };
    rendered_skill_md?: string | null;
    saved?: boolean | null;
    used_model: { provider: ModelProvider | string; model: string; profile_key: string };
    warnings?: string[] | null;
  }>('/api/v1/auto-reverse/skills/generate-draft', {
    method: 'POST',
    body: JSON.stringify({
      target_name: payload.targetName,
      target_path: payload.targetName,
      prompt: payload.prompt,
      model_profile_key: payload.modelProfileKey,
      reference_skill_names: payload.referenceSkillNames,
      reference_skill_paths: payload.referenceSkillNames,
      system_prompt: payload.systemPrompt,
      user_prompt_template: payload.userPromptTemplate,
      temperature: payload.temperature,
      save_after_generate: payload.saveAfterGenerate === true,
      overwrite_existing: payload.overwriteExisting === true,
    }),
  });

  const generatedSkills = (result.generated_skills ?? (result.generated_skill ? [result.generated_skill] : []))
    .map((item) => toSkillEntry(item));
  const rootPath = String(result.root_path ?? generatedSkills[0]?.path ?? payload.targetName).trim();

  return {
    draftId: String(result.draft_id ?? '').trim(),
    rootPath,
    generatedSkills: generatedSkills.map((item, index) => (
      index === 0 && result.generated_skill && !result.generated_skills
        ? toSkillEntry({
          ...result.generated_skill,
          rendered_skill_md: result.generated_skill.rendered_skill_md ?? result.rendered_skill_md,
        })
        : item
    )),
    saved: result.saved === true,
    usedModel: {
      provider: result.used_model.provider,
      model: result.used_model.model,
      profileKey: result.used_model.profile_key,
    },
    warnings: (result.warnings ?? []).map((item) => String(item)),
  };
}

export async function applySkillDraftByApi(draftId: string): Promise<SkillsCatalogPayload> {
  const payload = await requestJson<{
    current_version?: string | null;
    updated_at?: string | null;
    entries?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked?: boolean | null;
    }> | null;
    drafts?: Array<{
      draft_id?: string | null;
      root_path?: string | null;
      skill_count?: number | null;
      entry_count?: number | null;
      created_at?: string | null;
      source?: string | null;
    }> | null;
  }>('/api/v1/auto-reverse/skills/drafts/apply', {
    method: 'POST',
    body: JSON.stringify({
      draft_id: draftId,
    }),
  });

  return toSkillsCatalogPayload(payload);
}

export async function importSkillsZipPreviewByApi(file: File): Promise<SkillEntry[]> {
  const formData = new FormData();
  formData.append('file', file);

  const payload = await requestJson<{
    entries?: Array<{
      name?: string | null;
      description?: string | null;
      instructions?: string | null;
      skill_path?: string | null;
      path?: string | null;
      content?: string | null;
      files?: Record<string, string> | null;
      file_count?: number | null;
      depth?: number | null;
      parent_path?: string | null;
      rendered_skill_md?: string | null;
      locked?: boolean | null;
    }> | null;
  }>('/api/v1/auto-reverse/skills/import-zip-preview', {
    method: 'POST',
    body: formData,
  });

  return (payload.entries ?? []).map((item) => toSkillEntry(item));
}

export async function scanLocalBrowsersByApi(): Promise<LocalBrowserScanResult[]> {
  const payload = await requestJson<{
    items?: Array<{
      browser?: string | null;
      label?: string | null;
      source?: string | null;
      location?: string | null;
      executable_path?: string | null;
      available?: boolean | null;
    }> | null;
  }>('/api/v1/auto-reverse/local-browsers/scan');

  return (payload.items ?? []).map((item) => ({
    browser: normalizeLocalBrowserName(item.browser),
    label: (item.label ?? item.browser ?? '').trim(),
    location: (item.location ?? '').trim(),
    executablePath: (item.executable_path ?? '').trim(),
    source: (item.source ?? '').trim(),
    available: item.available === true,
  }));
}

export async function submitAutoReverseTask(payload: {
  urls: string[];
  browserConfig: AgentResourceSelection;
  analyseConfig: AgentResourceSelection;
  headless?: boolean;
  maxConcurrent?: number;
}): Promise<{ taskId: string; status: string }> {
  const browserFromKey = splitModelProfileKey(payload.browserConfig.modelProfileKey);
  const analyseFromKey = splitModelProfileKey(payload.analyseConfig.modelProfileKey);
  const result = await requestJson<{ task_id: string; status: string }>('/api/v1/auto-reverse/tasks', {
    method: 'POST',
    body: JSON.stringify({
      urls: payload.urls,
      browser_config: {
        browser_mode: payload.browserConfig.browserMode,
        mcp_tools: payload.browserConfig.mcpTools,
        skills: payload.browserConfig.skills,
        model_provider: payload.browserConfig.modelProvider ?? browserFromKey.provider,
        model_name: payload.browserConfig.modelName ?? browserFromKey.modelName,
        model_profile_key: payload.browserConfig.modelProfileKey,
      },
      analyse_config: {
        mcp_tools: payload.analyseConfig.mcpTools,
        skills: payload.analyseConfig.skills,
        model_provider: payload.analyseConfig.modelProvider ?? analyseFromKey.provider,
        model_name: payload.analyseConfig.modelName ?? analyseFromKey.modelName,
        model_profile_key: payload.analyseConfig.modelProfileKey,
      },
      headless: payload.headless ?? false,
      max_concurrent: payload.maxConcurrent ?? null,
    }),
  });
  return { taskId: result.task_id, status: result.status };
}

export async function fetchBrowserTaskBootstrap(): Promise<BrowserTaskBootstrapPayload> {
  const payload = await requestJson<{
    skills?: string[] | null;
    skills_enabled?: boolean | null;
    model_profiles?: Array<{
      key: string;
      label: string;
      provider: ModelProvider;
      model: string;
      base_url?: string | null;
      enabled: boolean;
    }> | null;
    runtime_mode?: string | null;
    persistence_mode?: string | null;
    mcp_selector_hidden?: boolean | null;
    system_prompt_source?: string | null;
  }>('/api/v1/browser-task/bootstrap');

  const parsedModelProfiles = (payload.model_profiles ?? []).map((item) => toModelProfileOption(item)).filter((item): item is ModelProfileOption => Boolean(item));

  return {
    skills: payload.skills ?? [],
    skillsEnabled: payload.skills_enabled ?? false,
    modelProfiles: parsedModelProfiles,
    runtimeMode: String(payload.runtime_mode ?? 'standalone'),
    persistenceMode: String(payload.persistence_mode ?? 'memory_only'),
    mcpSelectorHidden: payload.mcp_selector_hidden !== false,
    systemPromptSource: String(payload.system_prompt_source ?? 'browser_agent_system_prompt'),
  };
}

export async function createBrowserTaskSession(payload: BrowserTaskSessionCreatePayload): Promise<BrowserTaskSessionCreateResult> {
  const result = await requestJson<{
    session_id: string;
    bootstrap_started?: boolean | null;
    session_state: {
      session_id: string;
      status: string;
      start_url?: string | null;
      current_url?: string | null;
      page_title?: string | null;
      tab_count?: number | null;
      last_tool_name?: string | null;
      last_tool_summary?: string | null;
      message_count?: number | null;
      created_at: string;
      updated_at: string;
    };
  }>('/api/v1/browser-task/sessions', {
    method: 'POST',
    body: JSON.stringify({
      skills: payload.skills,
      model_profile_key: payload.modelProfileKey,
    }),
  });

  return {
    sessionId: result.session_id,
    bootstrapStarted: result.bootstrap_started === true,
    sessionState: {
      sessionId: result.session_state.session_id,
      status: result.session_state.status,
      startUrl: String(result.session_state.start_url ?? ''),
      currentUrl: String(result.session_state.current_url ?? ''),
      pageTitle: String(result.session_state.page_title ?? ''),
      tabCount: Number(result.session_state.tab_count ?? 0),
      lastToolName: String(result.session_state.last_tool_name ?? ''),
      lastToolSummary: String(result.session_state.last_tool_summary ?? ''),
      messageCount: Number(result.session_state.message_count ?? 0),
      createdAt: result.session_state.created_at,
      updatedAt: result.session_state.updated_at,
    },
  };
}

export async function sendBrowserTaskMessage(sessionId: string, content: string): Promise<BrowserTaskSendMessageResult> {
  const result = await requestJson<{
    session_id: string;
    message_id: string;
    accepted: boolean;
  }>(`/api/v1/browser-task/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });

  return {
    sessionId: result.session_id,
    messageId: result.message_id,
    accepted: result.accepted === true,
  };
}

export async function closeBrowserTaskSession(sessionId: string): Promise<void> {
  await requestJson(`/api/v1/browser-task/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function stopBrowserTaskSession(sessionId: string): Promise<BrowserTaskStopResult> {
  const result = await requestJson<{
    session_id: string;
    stopped: boolean;
    session_state: {
      session_id: string;
      status: string;
      start_url?: string | null;
      current_url?: string | null;
      page_title?: string | null;
      tab_count?: number | null;
      last_tool_name?: string | null;
      last_tool_summary?: string | null;
      message_count?: number | null;
      created_at: string;
      updated_at: string;
    };
  }>(`/api/v1/browser-task/sessions/${sessionId}/stop`, {
    method: 'POST',
  });

  return {
    sessionId: result.session_id,
    stopped: result.stopped === true,
    sessionState: {
      sessionId: result.session_state.session_id,
      status: result.session_state.status,
      startUrl: String(result.session_state.start_url ?? ''),
      currentUrl: String(result.session_state.current_url ?? ''),
      pageTitle: String(result.session_state.page_title ?? ''),
      tabCount: Number(result.session_state.tab_count ?? 0),
      lastToolName: String(result.session_state.last_tool_name ?? ''),
      lastToolSummary: String(result.session_state.last_tool_summary ?? ''),
      messageCount: Number(result.session_state.message_count ?? 0),
      createdAt: result.session_state.created_at,
      updatedAt: result.session_state.updated_at,
    },
  };
}

function parseBrowserTaskEvent(eventType: string, rawData: string): BrowserTaskStreamEvent {
  let payload: Record<string, unknown> = {};
  try {
    payload = rawData ? (JSON.parse(rawData) as Record<string, unknown>) : {};
  } catch {
    payload = { message: rawData };
  }
  return { type: eventType, payload };
}

export function openBrowserTaskStream(
  sessionId: string,
  handlers: {
    onEvent: (event: BrowserTaskStreamEvent) => void;
    onError?: (error: Error) => void;
    onClose?: () => void;
  },
): BrowserTaskStreamController {
  const controller = new AbortController();
  const done = (async () => {
    const response = await fetch(buildUrl(`/api/v1/browser-task/sessions/${sessionId}/stream`), {
      method: 'GET',
      headers: buildAuthHeaders(),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      const text = await response.text();
      throw new Error(`${response.status} ${response.statusText}${text ? `: ${text}` : ''}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let eventType = 'message';
    let dataLines: string[] = [];

    const dispatch = () => {
      if (!dataLines.length) {
        eventType = 'message';
        dataLines = [];
        return;
      }
      handlers.onEvent(parseBrowserTaskEvent(eventType, dataLines.join('\n')));
      eventType = 'message';
      dataLines = [];
    };

    while (true) {
      const { value, done: streamDone } = await reader.read();
      if (streamDone) {
        dispatch();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line) {
          dispatch();
          continue;
        }
        if (line.startsWith(':')) {
          continue;
        }
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim() || 'message';
          continue;
        }
        if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trimStart());
        }
      }
    }
  })()
    .catch((error) => {
      if (controller.signal.aborted) {
        return;
      }
      handlers.onError?.(error instanceof Error ? error : new Error(String(error)));
    })
    .finally(() => {
      handlers.onClose?.();
    });

  return {
    abort: () => controller.abort(),
    done,
  };
}

export async function fetchAutoReverseTaskStatus(taskId: string): Promise<AutoReverseTaskStatus> {
  const payload = await requestJson<{
    task_id: string;
    status: string;
    urls: string[];
    steps: Array<{
      key: string;
      status: string;
      total: number;
      pending: number;
      queued?: number;
      running: number;
      success: number;
      failed: number;
      skipped?: number;
    }>;
    items: Array<{
      url: string;
      url_index: number;
      session_id: string | null;
      browser_stage: { status: string; message?: string; started_at?: string; completed_at?: string };
      analyse_stage: { status: string; message?: string; started_at?: string; completed_at?: string };
      final_status: string;
      error: string | null;
      report_text: string;
      browser_tools?: Array<{ name: string; status: string; count?: number }>;
      analyse_tools?: Array<{ name: string; status: string; count?: number }>;
      created_at: string;
      updated_at: string;
    }>;
    stages: Array<{ agent_tag: string; status: string; message?: string; started_at?: string; completed_at?: string }>;
    created_at: string;
    updated_at: string;
  }>(`/api/v1/auto-reverse/tasks/${taskId}`);

  return {
    taskId: payload.task_id,
    status: payload.status,
    urls: payload.urls,
    steps: payload.steps.map((step) => ({
      key: step.key,
      status: step.status,
      total: step.total,
      pending: step.pending,
      queued: step.queued ?? 0,
      running: step.running,
      success: step.success,
      failed: step.failed,
      skipped: step.skipped ?? 0,
    })),
    items: payload.items.map((item) => ({
      url: item.url,
      urlIndex: item.url_index,
      sessionId: item.session_id,
      browserStage: {
        status: item.browser_stage.status,
        message: item.browser_stage.message,
        startedAt: item.browser_stage.started_at,
        completedAt: item.browser_stage.completed_at,
      },
      analyseStage: {
        status: item.analyse_stage.status,
        message: item.analyse_stage.message,
        startedAt: item.analyse_stage.started_at,
        completedAt: item.analyse_stage.completed_at,
      },
      finalStatus: item.final_status,
      error: item.error,
      reportText: item.report_text,
      browserTools: (item.browser_tools ?? []).map((tool) => ({
        name: String(tool.name ?? ""),
        status: String(tool.status ?? "completed"),
        count: Number(tool.count ?? 1),
      })),
      analyseTools: (item.analyse_tools ?? []).map((tool) => ({
        name: String(tool.name ?? ""),
        status: String(tool.status ?? "completed"),
        count: Number(tool.count ?? 1),
      })),
      createdAt: item.created_at,
      updatedAt: item.updated_at,
    })),
    stages: payload.stages.map((item) => ({
      agentTag: item.agent_tag,
      status: item.status,
      message: item.message,
      startedAt: item.started_at,
      completedAt: item.completed_at,
    })),
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
  };
}

export async function fetchAutoReverseTaskResults(taskId: string): Promise<AnalysisResultItem[]> {
  const payload = await requestJson<
    Array<{ url: string; session_id: string | null; success: boolean; report_text: string; error: string | null; created_at: string }>
  >(`/api/v1/auto-reverse/tasks/${taskId}/results`);

  return payload.map((item) => ({
    url: item.url,
    sessionId: item.session_id,
    success: item.success,
    reportText: item.report_text,
    error: item.error,
    createdAt: item.created_at,
  }));
}

export async function fetchSuccessResultArchives(options?: {
  taskId?: string;
  limit?: number;
}): Promise<SuccessResultArchiveItem[]> {
  const params = new URLSearchParams();
  if (options?.taskId) {
    params.set('task_id', options.taskId);
  }
  if (typeof options?.limit === 'number') {
    params.set('limit', String(options.limit));
  }
  const payload = await requestJson<
    Array<{ id: number; task_id: string; url: string; session_id: string | null; report_text: string; created_at: string }>
  >(`/api/v1/auto-reverse/success-results${params.size > 0 ? `?${params.toString()}` : ''}`);

  return payload.map((item) => ({
    id: item.id,
    taskId: item.task_id,
    url: item.url,
    sessionId: item.session_id,
    reportText: item.report_text,
    createdAt: item.created_at,
  }));
}

export async function listUsers(): Promise<SettingAccount[]> {
  const users = await requestJson<Array<{ id: number; username: string; created_at: string }>>('/api/v1/users');
  return users.map((item) => ({ id: item.id, username: item.username, createdAt: item.created_at }));
}

export async function createUser(username: string, password: string): Promise<void> {
  await requestJson('/api/v1/users', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function changePassword(userId: number, newPassword: string): Promise<void> {
  await requestJson(`/api/v1/users/${userId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ new_password: newPassword }),
  });
}
