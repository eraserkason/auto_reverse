import { ref } from 'vue';

import type { TimelineTone, RuntimeEventStatus, RuntimeEvent } from '@/components/browser-task/types';

export function useBrowserTaskRuntime() {
  const runtimeEvents = ref<RuntimeEvent[]>([]);
  const activeRunId = ref<number | null>(null);
  const latestRunId = ref<number | null>(null);
  const activeRunEventId = ref<string | null>(null);
  const selectedToolFilter = ref<'all' | string>('all');
  const lastSessionStateFingerprint = ref('');

  const pendingToolEventIds: Record<string, string[]> = {};
  let runtimeEventSequence = 0;
  let runSequence = 0;

  function nextRuntimeEventId(prefix: string): string {
    runtimeEventSequence += 1;
    return `${prefix}-${runtimeEventSequence}`;
  }

  function appendRuntimeEvent(event: Omit<RuntimeEvent, 'id' | 'createdAt'> & { id?: string; createdAt?: string }): string {
    const id = event.id ?? nextRuntimeEventId(event.kind);
    runtimeEvents.value.push({
      id,
      kind: event.kind,
      rawType: event.rawType,
      label: event.label,
      summary: event.summary,
      status: event.status,
      tone: event.tone,
      toolName: event.toolName,
      runId: event.runId,
      createdAt: event.createdAt ?? new Date().toISOString(),
    });
    return id;
  }

  function updateRuntimeEvent(eventId: string, patch: Partial<Omit<RuntimeEvent, 'id'>>): void {
    const index = runtimeEvents.value.findIndex((item) => item.id === eventId);
    if (index === -1) {
      return;
    }
    runtimeEvents.value.splice(index, 1, {
      ...runtimeEvents.value[index]!,
      ...patch,
    });
  }

  function clearPendingToolEventIds(): void {
    for (const key of Object.keys(pendingToolEventIds)) {
      delete pendingToolEventIds[key];
    }
  }

  function markToolEventsForRun(runId: number | null, nextStatus: RuntimeEventStatus, nextTone: TimelineTone): void {
    if (!runId) {
      return;
    }
    for (const item of runtimeEvents.value) {
      if (item.kind !== 'tool' || item.runId !== runId || item.status !== 'running') {
        continue;
      }
      item.status = nextStatus;
      item.tone = nextTone;
    }
  }

  function toggleToolFilter(toolName: string): void {
    selectedToolFilter.value = selectedToolFilter.value === toolName ? 'all' : toolName;
  }

  function resetRuntimeState(): void {
    runtimeEvents.value = [];
    selectedToolFilter.value = 'all';
    activeRunId.value = null;
    latestRunId.value = null;
    activeRunEventId.value = null;
    lastSessionStateFingerprint.value = '';
    runtimeEventSequence = 0;
    runSequence = 0;
    clearPendingToolEventIds();
  }

  function ensureRunStarted(
    kind: string,
    t: (key: string) => string,
    summarizeRuntimeValue: (value: unknown, max?: number) => string,
  ): void {
    runSequence += 1;
    activeRunId.value = runSequence;
    latestRunId.value = runSequence;
    selectedToolFilter.value = 'all';
    activeRunEventId.value = appendRuntimeEvent({
      kind: 'run',
      rawType: 'run.started',
      label: t('browserTask.activity.runStartedLabel'),
      summary: summarizeRuntimeValue(kind),
      status: 'running',
      tone: 'accent',
      runId: runSequence,
    });
  }

  function settleRun(
    status: RuntimeEventStatus,
    label: string,
    summary: string,
    tone: TimelineTone,
  ): void {
    const currentRunId = activeRunId.value ?? latestRunId.value ?? 0;
    if (activeRunEventId.value) {
      updateRuntimeEvent(activeRunEventId.value, { label, summary, status, tone });
    } else {
      appendRuntimeEvent({
        kind: 'run',
        rawType: status === 'failed' ? 'run.failed' : status === 'stopped' ? 'run.stopped' : 'run.completed',
        label,
        summary,
        status,
        tone,
        runId: currentRunId,
      });
    }
    markToolEventsForRun(currentRunId, status === 'completed' ? 'completed' : status, tone);
    clearPendingToolEventIds();
    activeRunId.value = null;
    activeRunEventId.value = null;
  }

  return {
    runtimeEvents,
    activeRunId,
    latestRunId,
    activeRunEventId,
    selectedToolFilter,
    lastSessionStateFingerprint,
    pendingToolEventIds,
    appendRuntimeEvent,
    updateRuntimeEvent,
    clearPendingToolEventIds,
    markToolEventsForRun,
    toggleToolFilter,
    resetRuntimeState,
    ensureRunStarted,
    settleRun,
  };
}

export type BrowserTaskRuntimeApi = ReturnType<typeof useBrowserTaskRuntime>;
