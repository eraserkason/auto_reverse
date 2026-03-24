import type { TaskExecutionItem, TaskExecutionStage } from '@/views/api';

function normalizeTaskMessage(value?: string | null): string {
  return String(value ?? '').trim();
}

function isFailureStatus(status?: string | null): boolean {
  const normalized = String(status ?? '').toLowerCase();
  return normalized.includes('fail') || normalized.includes('error');
}

function getStageFailureReason(stage?: TaskExecutionStage | null): string {
  if (!stage || !isFailureStatus(stage.status)) {
    return '';
  }
  return normalizeTaskMessage(stage.message);
}

export function getTaskExecutionFailureReason(item?: TaskExecutionItem | null): string {
  if (!item) {
    return '';
  }

  return (
    normalizeTaskMessage(item.error)
    || getStageFailureReason(item.analyseStage)
    || getStageFailureReason(item.browserStage)
  );
}
