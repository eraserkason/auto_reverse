import type { BrowserTaskMessage, BrowserTaskSessionState } from '@/views/api';

export function summarizeText(value: string, max = 140): string {
  const normalized = value.replace(/\s+/g, ' ').trim();
  if (!normalized) {
    return '';
  }
  if (normalized.length <= max) {
    return normalized;
  }
  return `${normalized.slice(0, max - 1)}…`;
}

export function extractUrls(value: string): string[] {
  return value.match(/https?:\/\/[^\s<>"']+/gi) ?? [];
}

export function truncateUrl(value: string, max = 80): string {
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, 42)}…${value.slice(-24)}`;
}

export function normalizeSessionState(payload: Record<string, unknown> | null | undefined): BrowserTaskSessionState | null {
  if (!payload) {
    return null;
  }
  return {
    sessionId: String(payload.session_id ?? payload.sessionId ?? ''),
    status: String(payload.status ?? 'idle'),
    startUrl: String(payload.start_url ?? payload.startUrl ?? ''),
    currentUrl: String(payload.current_url ?? payload.currentUrl ?? ''),
    pageTitle: String(payload.page_title ?? payload.pageTitle ?? ''),
    tabCount: Number(payload.tab_count ?? payload.tabCount ?? 0),
    lastToolName: String(payload.last_tool_name ?? payload.lastToolName ?? ''),
    lastToolSummary: String(payload.last_tool_summary ?? payload.lastToolSummary ?? ''),
    messageCount: Number(payload.message_count ?? payload.messageCount ?? 0),
    createdAt: String(payload.created_at ?? payload.createdAt ?? ''),
    updatedAt: String(payload.updated_at ?? payload.updatedAt ?? ''),
  };
}

export function normalizeMessage(payload: Record<string, unknown> | null | undefined): BrowserTaskMessage | null {
  if (!payload) {
    return null;
  }
  return {
    id: String(payload.id ?? ''),
    role: String(payload.role ?? 'system'),
    content: String(payload.content ?? ''),
    status: String(payload.status ?? 'done'),
    createdAt: String(payload.created_at ?? payload.createdAt ?? new Date().toISOString()),
  };
}

export function formatCompactSessionId(value?: string): string {
  if (!value) {
    return '';
  }
  if (value.length <= 18) {
    return value;
  }
  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}
