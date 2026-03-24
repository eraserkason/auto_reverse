<template>
  <button
    type="button"
    class="workspace-refresh-btn"
    :class="{
      'workspace-refresh-btn--loading': loading,
      'workspace-refresh-btn--compact': compact,
    }"
    :disabled="disabled || loading"
    :aria-label="computedAriaLabel"
    @click="$emit('click')"
  >
    <span class="workspace-refresh-btn__icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6" />
        <path d="M2.5 22v-6h6" />
        <path d="M2 11.5a10 10 0 0 1 18.8-4.3" />
        <path d="M22 12.5a10 10 0 0 1-18.8 4.2" />
      </svg>
    </span>
    <span v-if="showLabel" class="workspace-refresh-btn__label">
      {{ loading ? loadingLabel : label }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  label: string;
  loadingLabel?: string;
  ariaLabel?: string;
  disabled?: boolean;
  loading?: boolean;
  compact?: boolean;
  showLabel?: boolean;
}>(), {
  loadingLabel: '',
  ariaLabel: '',
  disabled: false,
  loading: false,
  compact: false,
  showLabel: true,
});

defineEmits<{
  click: [];
}>();

const computedAriaLabel = computed(() => {
  if (props.ariaLabel) {
    return props.ariaLabel;
  }
  if (props.loading && props.loadingLabel) {
    return props.loadingLabel;
  }
  return props.label;
});
</script>

<style scoped>
.workspace-refresh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--panel-border-strong) 62%, transparent);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--panel-bg) 96%, rgba(255, 255, 255, 0.08)), color-mix(in srgb, var(--panel-bg-soft) 92%, transparent));
  color: var(--text-secondary);
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition:
    border-color 180ms ease-out,
    color 180ms ease-out,
    background 180ms ease-out,
    transform 180ms ease-out,
    box-shadow 180ms ease-out;
  box-shadow: var(--shadow-xs);
}

.workspace-refresh-btn:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: rgba(var(--accent-rgb), 0.32);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--panel-bg) 98%, rgba(var(--accent-rgb), 0.08)), color-mix(in srgb, var(--bg-accent-soft) 42%, transparent));
  transform: translateY(-1px);
}

.workspace-refresh-btn:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(var(--accent-rgb), 0.16),
    var(--shadow-xs);
}

.workspace-refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.workspace-refresh-btn--compact {
  min-height: 36px;
  padding-inline: 12px;
}

.workspace-refresh-btn__icon {
  display: inline-flex;
  width: 16px;
  height: 16px;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.workspace-refresh-btn__icon svg {
  width: 16px;
  height: 16px;
}

.workspace-refresh-btn__label {
  white-space: nowrap;
}

.workspace-refresh-btn--loading .workspace-refresh-btn__icon {
  animation: workspace-refresh-spin 0.9s linear infinite;
}

@keyframes workspace-refresh-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .workspace-refresh-btn--loading .workspace-refresh-btn__icon {
    animation: none;
  }
}

@media (max-width: 640px) {
  .workspace-refresh-btn {
    min-height: 36px;
    padding-inline: 12px;
  }
}
</style>
