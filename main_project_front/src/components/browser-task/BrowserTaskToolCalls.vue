<template>
  <section class="bt-tools-panel">
    <header class="bt-tools-panel__head">
      <div class="bt-tools-panel__title-row">
        <h4>{{ t('browserTask.toolCalls.title') }}</h4>
        <span v-if="toolChips.length > 0" class="bt-tools-panel__badge">{{ toolChips.length }}</span>
      </div>
    </header>

    <div v-if="toolChips.length > 0" class="bt-tool-chips">
      <button
        type="button"
        class="bt-tool-chip"
        :class="{ 'bt-tool-chip--active': selectedToolFilter === 'all' }"
        :aria-pressed="selectedToolFilter === 'all' ? 'true' : 'false'"
        @click="$emit('filter', 'all')"
      >
        <span class="bt-tool-chip__label">{{ t('browserTask.observer.allTools') }}</span>
      </button>

      <button
        v-for="chip in toolChips"
        :key="chip.key"
        type="button"
        class="bt-tool-chip"
        :class="[
          `bt-tool-chip--${chip.tone}`,
          { 'bt-tool-chip--active': chip.active },
        ]"
        :aria-pressed="chip.active ? 'true' : 'false'"
        @click="$emit('filter', chip.key)"
      >
        <span class="bt-tool-chip__indicator" :class="`bt-tool-chip__indicator--${chip.tone}`"></span>
        <span class="bt-tool-chip__label">{{ chip.label }}</span>
        <span class="bt-tool-chip__count">{{ chip.count }}</span>
      </button>
    </div>
    <p v-else class="bt-tools-panel__empty">{{ t('browserTask.toolCalls.empty') }}</p>

    <div v-if="toolFeedItems.length > 0" class="bt-tool-feed">
      <button type="button" class="bt-tool-feed__toggle" @click="feedExpanded = !feedExpanded">
        <span>{{ t('browserTask.toolCalls.eyebrow') }}</span>
        <svg :class="{ 'is-expanded': feedExpanded }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      <transition name="feed-slide">
        <ul v-if="feedExpanded" class="bt-tool-feed__list">
          <li v-for="item in toolFeedItems" :key="item.id" class="bt-tool-feed__item">
            <div class="bt-tool-feed__meta">
              <strong>{{ item.title }}</strong>
              <span>{{ item.time }}</span>
            </div>
            <p>{{ item.summary }}</p>
          </li>
        </ul>
      </transition>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { useLocale } from '@/composables/useLocale';
import type { ToolChipItem, ToolFeedItem } from './types';

defineProps<{
  toolChips: ToolChipItem[];
  toolFeedItems: ToolFeedItem[];
  selectedToolFilter: string;
}>();

defineEmits<{
  filter: [key: string];
}>();

const feedExpanded = ref(false);
const { t } = useLocale();
</script>

<style scoped>
.bt-tools-panel {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-shadow);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.bt-tools-panel:hover {
  border-color: var(--panel-border-strong);
}

.bt-tools-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.bt-tools-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bt-tools-panel__title-row h4 {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 700;
}

.bt-tools-panel__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--bg-accent-soft);
  color: var(--accent-500);
  font-size: 0.72rem;
  font-weight: 800;
}

.bt-tools-panel__empty {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.86rem;
}

.bt-tool-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bt-tool-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  color: var(--text-secondary);
  font: inherit;
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}

.bt-tool-chip:hover {
  border-color: var(--panel-border-strong);
  background: var(--bg-accent-soft);
  color: var(--accent-500);
  transform: translateY(-1px);
}

.bt-tool-chip--active {
  border-color: rgba(var(--accent-rgb), 0.36);
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent-500);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.08);
}

.bt-tool-chip__indicator {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  flex-shrink: 0;
}

.bt-tool-chip__indicator--accent {
  background: var(--accent-500);
  box-shadow: 0 0 6px rgba(var(--accent-rgb), 0.4);
  animation: chip-pulse 2s ease-in-out infinite;
}

.bt-tool-chip__indicator--success {
  background: var(--success-500);
  box-shadow: 0 0 6px rgba(5, 150, 105, 0.4);
}

.bt-tool-chip__indicator--warning {
  background: var(--warning-500);
  box-shadow: 0 0 6px rgba(217, 119, 6, 0.4);
  animation: chip-pulse 2s ease-in-out infinite;
}

.bt-tool-chip__indicator--danger {
  background: var(--danger-500);
  box-shadow: 0 0 6px rgba(220, 38, 38, 0.4);
}

.bt-tool-chip__indicator--neutral {
  background: var(--text-muted);
  opacity: 0.5;
}

.bt-tool-chip__count {
  font-variant-numeric: tabular-nums;
  opacity: 0.7;
}

@keyframes chip-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.bt-tool-feed__toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  border: none;
  background: none;
  color: var(--text-muted);
  font: inherit;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: color var(--transition-base);
}

.bt-tool-feed__toggle:hover {
  color: var(--accent-500);
}

.bt-tool-feed__toggle svg {
  transition: transform var(--transition-base);
}

.bt-tool-feed__toggle svg.is-expanded {
  transform: rotate(180deg);
}

.bt-tool-feed__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.bt-tool-feed__item {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  transition: border-color var(--transition-base);
}

.bt-tool-feed__item:hover {
  border-color: var(--panel-border-strong);
}

.bt-tool-feed__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.bt-tool-feed__meta strong,
.bt-tool-feed__meta span,
.bt-tool-feed__item p {
  margin: 0;
}

.bt-tool-feed__meta strong {
  font-size: 0.84rem;
}

.bt-tool-feed__meta span {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.bt-tool-feed__item p {
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.feed-slide-enter-active,
.feed-slide-leave-active {
  transition: all 0.24s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.feed-slide-enter-from,
.feed-slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.feed-slide-enter-to,
.feed-slide-leave-from {
  opacity: 1;
  max-height: 600px;
}

@media (prefers-reduced-motion: reduce) {
  .bt-tool-chip__indicator--accent,
  .bt-tool-chip__indicator--warning {
    animation: none;
  }
}

@media (max-width: 640px) {
  .bt-tools-panel {
    padding: 12px 14px;
  }
}
</style>
