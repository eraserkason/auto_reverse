<template>
  <footer class="bt-composer">
    <div class="bt-composer__input-wrap">
      <n-input
        :id="promptFieldId"
        v-model:value="model"
        ref="promptTextareaRef"
        class="bt-composer__textarea"
        type="textarea"
        autocomplete="off"
        :aria-describedby="`${promptHintId} ${promptCountId}`"
        :placeholder="t('browserTask.fields.promptPlaceholder')"
        :autosize="{ minRows: 1, maxRows: 5 }"
        @keydown.enter.exact.prevent="$emit('submit')"
      />
    </div>

    <div class="bt-composer__bar">
      <div class="bt-composer__meta">
        <small :id="promptHintId" class="bt-composer__hint">{{ composerMetaHint }}</small>
        <span :id="promptCountId" class="bt-composer__char-count">{{ draftCharacterCount }}</span>
      </div>

      <div class="bt-composer__actions">
        <n-dropdown
          placement="top-start"
          trigger="click"
          :options="actionOptions"
          @select="handleActionSelect"
        >
          <button type="button" class="bt-composer__icon-btn" aria-label="More actions">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <circle cx="5" cy="12" r="1.5" />
              <circle cx="12" cy="12" r="1.5" />
              <circle cx="19" cy="12" r="1.5" />
            </svg>
          </button>
        </n-dropdown>
        <button
          type="button"
          class="bt-composer__send"
          :class="{ 'bt-composer__send--stop': isBusy }"
          :disabled="primaryActionDisabled"
          @click="$emit('primary-action')"
        >
          <svg v-if="!isBusy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="m5 12 14-7-4 7 4 7Z" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          <span>{{ primaryActionLabel }}</span>
        </button>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { NDropdown, NInput, type DropdownOption } from 'naive-ui';

import { useLocale } from '@/composables/useLocale';

const model = defineModel<string>({ required: true });

const props = defineProps<{
  isBusy: boolean;
  resetSessionDisabled: boolean;
  primaryActionDisabled: boolean;
  primaryActionLabel: string;
  composerMetaHint: string;
  draftCharacterCount: string;
  promptFieldId: string;
  promptHintId: string;
  promptCountId: string;
}>();

const emit = defineEmits<{
  'insert-example': [];
  'reset-session': [];
  'primary-action': [];
  submit: [];
}>();

const promptTextareaRef = ref<InstanceType<typeof NInput> | null>(null);

const actionOptions = computed<DropdownOption[]>(() => [
  {
    label: t('browserTask.fields.insertExample'),
    key: 'insert-example',
    disabled: props.isBusy,
  },
  {
    label: t('browserTask.actions.resetSession'),
    key: 'reset-session',
    disabled: props.resetSessionDisabled,
  },
]);

function handleActionSelect(key: string | number): void {
  if (key === 'insert-example') {
    emit('insert-example');
    return;
  }
  if (key === 'reset-session') {
    emit('reset-session');
  }
}

defineExpose({
  promptTextareaRef,
});

const { t } = useLocale();
</script>

<style scoped>
.bt-composer {
  position: sticky;
  bottom: max(0px, env(safe-area-inset-bottom));
  z-index: 3;
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--panel-border);
  border-radius: 20px;
  background: var(--panel-bg);
  box-shadow: var(--panel-shadow);
  backdrop-filter: blur(12px);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.bt-composer:focus-within {
  border-color: rgba(var(--accent-rgb), 0.32);
  box-shadow: var(--panel-shadow), 0 0 0 3px rgba(var(--accent-rgb), 0.08);
}

.bt-composer__input-wrap {
  display: grid;
}

.bt-composer__textarea :deep(.n-input-wrapper) {
  border-radius: 14px;
  background: var(--panel-bg-soft);
}

.bt-composer__textarea :deep(.n-input__textarea-el) {
  line-height: 1.6;
}

.bt-composer__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.bt-composer__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.bt-composer__hint {
  color: var(--text-muted);
  font-size: 0.76rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bt-composer__char-count {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-soft);
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.bt-composer__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.bt-composer__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-muted);
  cursor: pointer;
  font: inherit;
  padding: 0;
  transition: all var(--transition-base);
}

.bt-composer__icon-btn:hover {
  border-color: var(--panel-border-strong);
  color: var(--accent-500);
  background: var(--bg-accent-soft);
}

.bt-composer__send {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border-radius: 12px;
  border: none;
  background: var(--accent-500);
  color: #fff;
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}

.bt-composer__send:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.3);
}

.bt-composer__send:active:not(:disabled) {
  transform: translateY(0) scale(0.97);
}

.bt-composer__send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bt-composer__send--stop {
  background: var(--warning-500);
}

.bt-composer__send--stop:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
}

@media (max-width: 959px) {
  .bt-composer {
    bottom: calc(var(--mobile-bottom-nav-height) + 10px);
  }
}

@media (max-width: 767px) {
  .bt-composer {
    border-radius: 14px;
    padding: 10px;
  }
}

@media (max-width: 640px) {
  .bt-composer__hint {
    display: none;
  }

  .bt-composer__meta {
    display: none;
  }

  .bt-composer__send span {
    display: none;
  }

  .bt-composer__send {
    width: 36px;
    padding: 0;
    justify-content: center;
    border-radius: 10px;
  }
}
</style>
