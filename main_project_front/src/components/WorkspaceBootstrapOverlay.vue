<template>
  <div class="workspace-loader-shell" role="status" aria-live="polite" aria-busy="true">
    <section class="workspace-loader-card">
      <div class="workspace-loader-card__track" aria-hidden="true">
        <span class="workspace-loader-card__track-bar"></span>
      </div>

      <div class="workspace-loader-card__body">
        <div class="workspace-loader-card__copy">
          <div class="workspace-loader-card__heading">
            <strong>{{ t('layout.bootstrap.title') }}</strong>
            <span class="workspace-loader-card__status">{{ t('layout.bootstrap.status') }}</span>
          </div>
          <p>{{ currentStageLabel }}</p>
        </div>
        <div class="workspace-loader-card__dots" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { useLocale } from '@/composables/useLocale';

const props = defineProps<{
  dashboardReady: boolean;
  resourcesReady: boolean;
}>();

const { t } = useLocale();

const currentStageLabel = computed(() => {
  if (!props.dashboardReady) {
    return t('layout.bootstrap.stages.dashboard.label');
  }
  if (!props.resourcesReady) {
    return t('layout.bootstrap.stages.services.label');
  }
  return t('layout.bootstrap.footer.ready');
});
</script>

<style scoped>
.workspace-loader-shell {
  position: fixed;
  inset-inline: 0;
  top: 18px;
  z-index: 1600;
  display: flex;
  justify-content: center;
  padding: 0 18px;
  pointer-events: none;
}

.workspace-loader-card {
  width: min(520px, 100%);
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid color-mix(in srgb, var(--panel-border-strong) 72%, transparent);
  background: color-mix(in srgb, var(--panel-bg) 94%, rgba(255, 255, 255, 0.06));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-sm);
}

.workspace-loader-card__track {
  position: relative;
  overflow: hidden;
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--panel-bg-soft) 82%, transparent);
}

.workspace-loader-card__track-bar {
  position: absolute;
  inset-block: 0;
  width: 38%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent-500), color-mix(in srgb, var(--accent-500) 52%, #22c55e));
  animation: workspace-loader-slide 1.4s ease-in-out infinite;
}

.workspace-loader-card__body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.workspace-loader-card__copy {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.workspace-loader-card__heading {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.workspace-loader-card__copy strong {
  font-size: 1rem;
  letter-spacing: -0.02em;
}

.workspace-loader-card__status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--accent-500) 24%, transparent);
  background: color-mix(in srgb, var(--accent-500) 12%, var(--panel-bg-soft));
  color: var(--text-secondary);
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
}

.workspace-loader-card__copy p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
}

.workspace-loader-card__dots {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.workspace-loader-card__dots span {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent-500) 82%, white 18%);
  animation: workspace-loader-pulse 1.2s ease-in-out infinite;
}

.workspace-loader-card__dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.workspace-loader-card__dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes workspace-loader-slide {
  0% {
    transform: translateX(-110%);
  }
  50% {
    transform: translateX(120%);
  }
  100% {
    transform: translateX(250%);
  }
}

@keyframes workspace-loader-pulse {
  0%,
  100% {
    opacity: 0.28;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-1px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .workspace-loader-card__track-bar,
  .workspace-loader-card__dots span {
    animation: none;
  }
}

@media (max-width: 640px) {
  .workspace-loader-shell {
    top: 12px;
    padding: 0 12px;
  }

  .workspace-loader-card {
    padding: 12px 13px;
    border-radius: 16px;
  }

  .workspace-loader-card__body {
    align-items: flex-start;
  }
}
</style>
