<template>
  <section class="bt-timeline-panel">
    <header class="bt-timeline-panel__head">
      <div class="bt-timeline-panel__title-row">
        <h4>{{ t('browserTask.timeline.title') }}</h4>
      </div>
    </header>

    <div ref="timelineRef" class="bt-timeline" @scroll="$emit('scroll')">
      <ul v-if="agentTimelineItems.length > 0" class="bt-timeline__list">
        <li
          v-for="(item, index) in agentTimelineItems"
          :key="item.id"
          class="bt-timeline__item"
          :class="`bt-timeline__item--${item.tone}`"
        >
          <div class="bt-timeline__track">
            <span class="bt-timeline__dot"></span>
            <span v-if="index < agentTimelineItems.length - 1" class="bt-timeline__line"></span>
          </div>
          <div class="bt-timeline__body">
            <div class="bt-timeline__meta">
              <strong>{{ item.title }}</strong>
              <span>{{ item.time }}</span>
            </div>
            <p v-if="item.summary">{{ item.summary }}</p>
          </div>
        </li>
      </ul>
      <p v-else class="bt-timeline-panel__empty">{{ t('browserTask.timeline.empty') }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { useLocale } from '@/composables/useLocale';
import type { AgentTimelineItem } from './types';

defineProps<{
  agentTimelineItems: AgentTimelineItem[];
}>();

defineEmits<{
  scroll: [];
}>();

const timelineRef = ref<HTMLElement | null>(null);

defineExpose({
  timelineRef,
});
const { t } = useLocale();
</script>

<style scoped>
.bt-timeline-panel {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-shadow);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.bt-timeline-panel:hover {
  border-color: var(--panel-border-strong);
}

.bt-timeline-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.bt-timeline-panel__title-row {
  display: grid;
  gap: 4px;
}

.bt-timeline-panel__eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.bt-timeline-panel__title-row h4 {
  margin: 0;
  font-size: 0.96rem;
}

.bt-timeline-panel__empty {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.86rem;
}

.bt-timeline {
  max-height: 380px;
  overflow: auto;
  padding-right: 4px;
  scrollbar-gutter: stable;
}

.bt-timeline__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.bt-timeline__item {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  gap: 10px;
  min-height: 0;
}

.bt-timeline__track {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4px;
}

.bt-timeline__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  border: 2px solid var(--bg-surface);
  background: var(--text-muted);
  flex-shrink: 0;
  z-index: 1;
  transition: background-color var(--transition-base), box-shadow var(--transition-base);
}

.bt-timeline__line {
  width: 2px;
  flex: 1;
  min-height: 8px;
  background: color-mix(in srgb, var(--text-muted) 16%, transparent);
  border-radius: 1px;
}

.bt-timeline__item--accent .bt-timeline__dot {
  background: var(--accent-500);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.18);
}

.bt-timeline__item--success .bt-timeline__dot {
  background: var(--success-500);
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.18);
}

.bt-timeline__item--warning .bt-timeline__dot {
  background: var(--warning-500);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.18);
}

.bt-timeline__item--danger .bt-timeline__dot {
  background: var(--danger-500);
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.18);
}

.bt-timeline__body {
  display: grid;
  gap: 4px;
  padding: 10px 14px 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  margin-bottom: 6px;
  transition: border-color var(--transition-base);
}

.bt-timeline__body:hover {
  border-color: var(--panel-border-strong);
}

.bt-timeline__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.bt-timeline__meta strong {
  margin: 0;
  font-size: 0.86rem;
}

.bt-timeline__meta span {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.bt-timeline__body p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

@media (max-width: 640px) {
  .bt-timeline-panel {
    padding: 14px;
  }

  .bt-timeline {
    max-height: 300px;
  }
}
</style>
