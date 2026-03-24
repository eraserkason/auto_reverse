<template>
  <div class="bt-topbar motion-enter-soft">
    <div class="bt-topbar__main">
      <div class="bt-topbar__left">
        <h2>{{ t('browserTask.title') }}</h2>
        <n-tag :bordered="false" :class="statusBadgeClass" type="info" size="small" round>
          {{ sessionStatusLabel }}
        </n-tag>
      </div>

      <div class="bt-topbar__quick-actions">
        <WorkspaceRefreshButton
          class="bt-topbar__refresh"
          :label="t('browserTask.actions.reload')"
          :loading-label="t('browserTask.actions.reloadLoading')"
          :aria-label="loadingBootstrap ? t('browserTask.actions.reloadLoading') : t('browserTask.actions.reload')"
          :loading="loadingBootstrap"
          compact
          :show-label="false"
          @click="$emit('reload')"
        />
        <button
          v-if="!isInlineTaskSystem"
          ref="observerToggleButtonRef"
          type="button"
          class="bt-topbar__btn bt-topbar__btn--secondary"
          :aria-controls="taskSystemPanelId"
          :aria-expanded="observerOpen ? 'true' : 'false'"
          aria-haspopup="dialog"
          :aria-label="observerToggleLabel"
          @click="$emit('toggle-observer')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
        </button>
      </div>
    </div>

    <button
      type="button"
      class="bt-topbar__btn bt-topbar__btn--primary bt-topbar__primary"
      :disabled="creatingSession"
      :aria-label="creatingSession ? t('browserTask.actions.newSessionLoading') : t('browserTask.actions.newSession')"
      @click="$emit('new-session')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
        <path d="M5 12h14" /><path d="M12 5v14" />
      </svg>
      <span>{{ creatingSession ? t('browserTask.actions.newSessionLoading') : t('browserTask.actions.newSession') }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { NTag } from 'naive-ui';

import { useLocale } from '@/composables/useLocale';
import WorkspaceRefreshButton from '@/components/WorkspaceRefreshButton.vue';

defineProps<{
  loadingBootstrap: boolean;
  creatingSession: boolean;
  observerOpen: boolean;
  isInlineTaskSystem: boolean;
  statusBadgeClass: string;
  sessionStatusLabel: string;
  observerToggleLabel: string;
  taskSystemPanelId: string;
}>();

defineEmits<{
  reload: [];
  'toggle-observer': [];
  'new-session': [];
}>();

const observerToggleButtonRef = ref<HTMLButtonElement | null>(null);

defineExpose({
  observerToggleButtonRef,
});

const { t } = useLocale();
</script>

<style scoped>
.bt-topbar {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  width: var(--bt-chat-width);
  max-width: 100%;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--panel-shadow);
}

.bt-topbar__main {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.bt-topbar__left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-width: 0;
}

.bt-topbar__left h2 {
  margin: 0;
  font-size: clamp(1.2rem, 1vw + 0.9rem, 1.6rem);
  letter-spacing: -0.03em;
  white-space: nowrap;
}

.bt-topbar__quick-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.bt-topbar__refresh :deep(.workspace-refresh-btn) {
  width: 34px;
  min-width: 34px;
  height: 34px;
  padding-inline: 0;
}

.bt-topbar__primary {
  justify-self: end;
}

.bt-topbar__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 34px;
  padding: 0;
  width: 34px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-secondary);
  font: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
}

.bt-topbar__btn:hover:not(:disabled) {
  border-color: var(--panel-border-strong);
  color: var(--accent-500);
  background: var(--bg-accent-soft);
  transform: translateY(-1px);
}

.bt-topbar__btn:active:not(:disabled) {
  transform: translateY(0) scale(0.96);
}

.bt-topbar__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bt-topbar__btn--primary {
  width: auto;
  padding: 0 14px;
  border-color: transparent;
  background: var(--accent-500);
  color: #fff;
}

.bt-topbar__btn--primary:hover:not(:disabled) {
  background: var(--accent-500);
  filter: brightness(1.1);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.24);
  color: #fff;
}

@media (max-width: 767px) {
  .bt-topbar {
    grid-template-columns: 1fr;
    align-items: stretch;
    gap: 10px;
    padding: 12px 14px;
  }

  .bt-topbar__main {
    align-items: flex-start;
  }

  .bt-topbar__left {
    min-width: 0;
    flex: 1;
  }

  .bt-topbar__left h2 {
    font-size: 1.18rem;
  }

  .bt-topbar__quick-actions {
    justify-content: flex-end;
  }

  .bt-topbar__refresh :deep(.workspace-refresh-btn) {
    width: 36px;
    min-width: 36px;
    height: 36px;
  }

  .bt-topbar__btn {
    width: 36px;
    height: 36px;
  }

  .bt-topbar__primary {
    justify-self: start;
    width: auto;
    min-width: min(148px, 100%);
    max-width: 100%;
    padding: 0 16px;
  }
}
</style>
