import { ref } from 'vue';

import {
  openBrowserTaskStream,
  type BrowserTaskStreamEvent,
  type BrowserTaskStreamController,
} from '@/views/api';
import type { BrowserTaskRuntimeApi } from './useBrowserTaskRuntime';
import type { BrowserTaskMessagesApi } from './useBrowserTaskMessages';
import { normalizeSessionState, normalizeMessage, summarizeText } from '@/components/browser-task/utils';
import type { Ref } from 'vue';
import type { BrowserTaskSessionState } from '@/views/api';

export interface BrowserTaskStreamOptions {
  runtime: BrowserTaskRuntimeApi;
  messages: BrowserTaskMessagesApi;
  sessionState: Ref<BrowserTaskSessionState | null>;
  stoppingRun: Ref<boolean>;
  errorMessage: Ref<string>;
  t: (key: string, params?: Record<string, unknown>) => string;
}

export function useBrowserTaskStream(opts: BrowserTaskStreamOptions) {
  const { runtime, messages, sessionState, stoppingRun, errorMessage, t } = opts;
  const streamConnected = ref(false);
  const streamController = ref<BrowserTaskStreamController | null>(null);

  function summarizeRuntimeValue(value: unknown, max = 140): string {
    if (value === undefined || value === null || value === '') {
      return t('common.misc.empty');
    }
    if (typeof value === 'string') {
      return summarizeText(value, max);
    }
    try {
      return summarizeText(JSON.stringify(value), max);
    } catch {
      return summarizeText(String(value), max);
    }
  }

  function recordSessionStateTransition(next: BrowserTaskSessionState): void {
    const fingerprint = [
      next.status,
      next.currentUrl,
      next.pageTitle,
      next.lastToolName,
      next.updatedAt,
    ].join('|');
    if (fingerprint === runtime.lastSessionStateFingerprint.value) {
      return;
    }
    runtime.lastSessionStateFingerprint.value = fingerprint;

    function formatSessionStatus(status?: string): string {
      if (!status) return t('browserTask.status.idle');
      return t(`browserTask.statusLabels.${status}`);
    }

    if (next.status === 'ready' || next.status === 'bootstrapping' || next.status === 'stopping' || next.status === 'error') {
      runtime.appendRuntimeEvent({
        kind: 'session',
        rawType: 'session.state',
        label: `${t('browserTask.observer.phase.session')} · ${formatSessionStatus(next.status)}`,
        summary: next.currentUrl || next.pageTitle || next.lastToolSummary || t('common.misc.empty'),
        status: next.status === 'error' ? 'failed' : next.status === 'stopping' ? 'stopped' : next.status === 'bootstrapping' ? 'running' : 'completed',
        tone: next.status === 'error' ? 'danger' : next.status === 'stopping' ? 'warning' : next.status === 'bootstrapping' ? 'accent' : 'success',
        runId: runtime.activeRunId.value ?? runtime.latestRunId.value ?? 0,
      });
    }
  }

  function handleStreamEvent(event: BrowserTaskStreamEvent): void {
    const payload = event.payload;

    if (event.type === 'session.created' || event.type === 'session.state' || event.type === 'session.closed') {
      const state = normalizeSessionState(((payload.state as Record<string, unknown> | undefined) ?? payload));
      if (state) {
        sessionState.value = state;
        if (state.status !== 'stopping') {
          stoppingRun.value = false;
        }
        if (event.type === 'session.created') {
          runtime.appendRuntimeEvent({
            kind: 'session',
            rawType: event.type,
            label: t('browserTask.observer.sessionCreated'),
            summary: state.currentUrl || state.sessionId || t('common.misc.empty'),
            status: 'completed',
            tone: 'success',
            runId: 0,
          });
        } else if (event.type === 'session.closed') {
          runtime.appendRuntimeEvent({
            kind: 'session',
            rawType: event.type,
            label: t('browserTask.activity.sessionClosedLabel'),
            summary: t('browserTask.activity.sessionClosedSummary'),
            status: 'stopped',
            tone: 'warning',
            runId: 0,
          });
        } else {
          recordSessionStateTransition(state);
        }
      }
      return;
    }

    if (event.type === 'message.user' || event.type === 'assistant.message') {
      const message = normalizeMessage(payload);
      if (message) {
        messages.upsertMessage(message);
      }
      return;
    }

    if (event.type === 'assistant.delta') {
      const messageId = String(payload.message_id ?? '');
      const delta = String(payload.delta ?? '');
      if (!messageId || !delta) {
        return;
      }
      const existing = messages.messages.value.find((item) => item.id === messageId);
      messages.upsertMessage({
        id: messageId,
        role: 'assistant',
        content: `${existing?.content ?? ''}${delta}`,
        status: 'streaming',
        createdAt: existing?.createdAt ?? new Date().toISOString(),
      });
      return;
    }

    if (event.type === 'tool.started') {
      const toolName = String(payload.tool_name ?? t('common.misc.empty'));
      const eventId = runtime.appendRuntimeEvent({
        kind: 'tool',
        rawType: event.type,
        label: `${t('browserTask.activity.toolStarted')} · ${toolName}`,
        summary: summarizeRuntimeValue(payload.input),
        status: 'running',
        tone: 'accent',
        toolName,
        runId: runtime.activeRunId.value ?? runtime.latestRunId.value ?? 0,
      });
      if (!runtime.pendingToolEventIds[toolName]) {
        runtime.pendingToolEventIds[toolName] = [];
      }
      runtime.pendingToolEventIds[toolName]!.push(eventId);
      return;
    }

    if (event.type === 'tool.finished') {
      const toolName = String(payload.tool_name ?? t('common.misc.empty'));
      const eventId = runtime.pendingToolEventIds[toolName]?.pop();
      if (eventId) {
        runtime.updateRuntimeEvent(eventId, {
          rawType: event.type,
          label: `${t('browserTask.activity.toolFinished')} · ${toolName}`,
          summary: summarizeRuntimeValue(payload.summary),
          status: 'completed',
          tone: 'success',
        });
        if (runtime.pendingToolEventIds[toolName]?.length === 0) {
          delete runtime.pendingToolEventIds[toolName];
        }
      } else {
        runtime.appendRuntimeEvent({
          kind: 'tool',
          rawType: event.type,
          label: `${t('browserTask.activity.toolFinished')} · ${toolName}`,
          summary: summarizeRuntimeValue(payload.summary),
          status: 'completed',
          tone: 'success',
          toolName,
          runId: runtime.activeRunId.value ?? runtime.latestRunId.value ?? 0,
        });
      }
      return;
    }

    if (event.type === 'run.started') {
      runtime.ensureRunStarted(String(payload.kind ?? 'message'), t, summarizeRuntimeValue);
      return;
    }

    if (event.type === 'run.completed') {
      runtime.settleRun('completed', t('browserTask.activity.runCompletedLabel'), t('browserTask.activity.runCompletedSummary'), 'success');
      return;
    }

    if (event.type === 'run.stopped') {
      stoppingRun.value = false;
      runtime.settleRun(
        'stopped',
        t('browserTask.activity.runStoppedLabel'),
        summarizeRuntimeValue(payload.summary ?? t('browserTask.activity.runStoppedSummary')),
        'warning',
      );
      return;
    }

    if (event.type === 'run.failed') {
      stoppingRun.value = false;
      const summary = summarizeRuntimeValue(payload.message ?? payload.summary ?? t('browserTask.activity.runFailedSummary'));
      runtime.settleRun('failed', t('browserTask.activity.runFailedLabel'), summary, 'danger');
      errorMessage.value = summary;
      return;
    }

    if (event.type === 'error') {
      stoppingRun.value = false;
      const summary = summarizeRuntimeValue(payload.message ?? payload.summary ?? t('browserTask.activity.runFailedSummary'));
      runtime.appendRuntimeEvent({
        kind: 'error',
        rawType: event.type,
        label: t('browserTask.activity.runFailedLabel'),
        summary,
        status: 'failed',
        tone: 'danger',
        runId: runtime.activeRunId.value ?? runtime.latestRunId.value ?? 0,
      });
      if (runtime.activeRunEventId.value) {
        runtime.settleRun('failed', t('browserTask.activity.runFailedLabel'), summary, 'danger');
      }
      errorMessage.value = summary;
    }
  }

  function closeStream(): void {
    streamController.value?.abort();
    streamController.value = null;
    streamConnected.value = false;
  }

  function connectStream(sessionId: string): void {
    closeStream();
    streamConnected.value = true;
    streamController.value = openBrowserTaskStream(sessionId, {
      onEvent: handleStreamEvent,
      onError: (error) => {
        streamConnected.value = false;
        errorMessage.value = error.message;
      },
      onClose: () => {
        streamConnected.value = false;
      },
    });
  }

  return {
    streamConnected,
    streamController,
    connectStream,
    closeStream,
    handleStreamEvent,
  };
}

export type BrowserTaskStreamApi = ReturnType<typeof useBrowserTaskStream>;
