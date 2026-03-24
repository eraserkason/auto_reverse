<template>
  <div class="hstepper" role="list" :aria-label="t('autoReverse.task.title')">
    <div
      v-for="(step, index) in steps"
      :key="step.key"
      class="hstepper__step"
      :class="stepClasses(step)"
      role="listitem"
    >
      <div class="hstepper__dot" :class="dotClass(step.status)"></div>
      <span class="hstepper__name">{{ getStepLabel(step.key) }}</span>
      <span class="hstepper__tag" :class="dotClass(step.status)">{{ getTaskStatusLabel(step.status) }}</span>
      <div v-if="index < steps.length - 1" class="hstepper__connector" :class="connectorClass(step)"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLocale } from '@/composables/useLocale';
import type { TaskStepSummary } from '@/views/api';

defineProps<{
  steps: TaskStepSummary[];
}>();

const { t, getTaskStatusLabel } = useLocale();

const getStepLabel = (key: string): string => t(`autoReverse.progress.steps.${key}`);

const dotClass = (status: string): string => {
  const lower = status.toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'hstepper--success';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'hstepper--warning';
  if (lower.includes('skip')) return 'hstepper--skipped';
  if (lower.includes('fail') || lower.includes('error')) return 'hstepper--danger';
  return '';
};

const stepClasses = (step: TaskStepSummary): Record<string, boolean> => {
  const lower = step.status.toLowerCase();
  return {
    'hstepper__step--done': lower.includes('success') || lower.includes('complete'),
    'hstepper__step--active': lower.includes('running') || lower.includes('queued') || lower.includes('pending'),
    'hstepper__step--error': lower.includes('fail') || lower.includes('error'),
  };
};

const connectorClass = (step: TaskStepSummary): string => {
  const lower = step.status.toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'hstepper__connector--done';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'hstepper__connector--active';
  return '';
};
</script>

<style scoped>
.hstepper {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  overflow-x: auto;
}

.hstepper__step {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  position: relative;
  padding: 4px 0;
}

.hstepper__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  flex-shrink: 0;
  transition: background 200ms ease, box-shadow 200ms ease;
}

.hstepper__dot.hstepper--success {
  background: var(--success-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--success-500) 16%, transparent);
}

.hstepper__dot.hstepper--warning {
  background: var(--warning-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning-500) 16%, transparent);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.hstepper__dot.hstepper--danger {
  background: var(--danger-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger-500) 16%, transparent);
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hstepper__name {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.hstepper__tag {
  font-size: 0.64rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  white-space: nowrap;
  color: var(--text-muted);
  background: transparent;
}

.hstepper__tag.hstepper--success {
  color: var(--success-500);
  background: color-mix(in srgb, var(--success-500) 10%, transparent);
}

.hstepper__tag.hstepper--warning {
  color: var(--warning-500);
  background: color-mix(in srgb, var(--warning-500) 10%, transparent);
}

.hstepper__tag.hstepper--danger {
  color: var(--danger-500);
  background: color-mix(in srgb, var(--danger-500) 10%, transparent);
}


.hstepper__connector {
  width: 20px;
  height: 2px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--text-muted) 18%, transparent);
  margin: 0 6px;
  flex-shrink: 0;
  transition: background 200ms ease;
}

.hstepper__connector--done {
  background: color-mix(in srgb, var(--success-500) 40%, transparent);
}

.hstepper__connector--active {
  background: color-mix(in srgb, var(--accent-500) 30%, transparent);
}

@media (prefers-reduced-motion: reduce) {
  .hstepper__dot.hstepper--warning {
    animation: none;
  }
}
</style>
