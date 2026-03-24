<template>
  <details v-if="item" class="ri" :open="isOpen" @toggle="handleToggle">
    <summary class="ri__summary">
      <div class="ri__summary-main" @mouseleave="clearDesktopAgentHover">
        <div class="ri__head">
          <p class="ri__url">{{ item.url }}</p>
          <span class="status-tag" :class="statusClass(item.finalStatus)">
            {{ getTaskStatusLabel(item.finalStatus) }}
          </span>
        </div>

        <div class="ri__info-bar">
          <button
            type="button"
            class="ri__stage-chip ri__stage-chip--action"
            :class="statusClass(item.browserStage.status)"
            :aria-expanded="activeAgent === 'browser_agent' ? 'true' : 'false'"
            @mouseenter="setDesktopAgent('browser_agent')"
            @focus="setDesktopAgent('browser_agent')"
            @blur="clearDesktopAgentHover"
            @click.stop.prevent="toggleMobileAgent('browser_agent')"
          >
            {{ browserLabel }} · {{ getTaskStatusLabel(item.browserStage.status) }}
          </button>
          <button
            type="button"
            class="ri__stage-chip ri__stage-chip--action"
            :class="statusClass(item.analyseStage.status)"
            :aria-expanded="activeAgent === 'analyse_agent' ? 'true' : 'false'"
            @mouseenter="setDesktopAgent('analyse_agent')"
            @focus="setDesktopAgent('analyse_agent')"
            @blur="clearDesktopAgentHover"
            @click.stop.prevent="toggleMobileAgent('analyse_agent')"
          >
            {{ analyseLabel }} · {{ getTaskStatusLabel(item.analyseStage.status) }}
          </button>
          <span class="ri__time">{{ formatDateTime(item.updatedAt) }}</span>
        </div>

        <transition name="ri-tools-fade">
          <div v-if="activeAgent" class="ri__tool-reveal" @click.stop>
            <span class="ri__tool-reveal-label">{{ activeAgentLabel }} · {{ mcpToolsLabel }}</span>
            <div v-if="activeAgentTools.length > 0" class="ri__tool-chip-list">
              <span
                v-for="tool in activeAgentTools"
                :key="`${activeAgent}-${tool.name}`"
                class="ri__tool-chip"
                :class="toolChipClass(tool.status)"
              >
                <span class="ri__tool-chip-name">{{ tool.name }}</span>
                <span v-if="tool.count > 1" class="ri__tool-chip-count">×{{ tool.count }}</span>
              </span>
            </div>
            <span v-else class="ri__tool-empty">{{ noMcpToolsText }}</span>
          </div>
        </transition>
      </div>

      <span class="ri__chevron" aria-hidden="true"></span>
    </summary>

    <div class="ri__body">
      <article class="ri__result">
        <div class="ri__result-bar">
          <span class="ri__result-label">{{ bodyLabel }}</span>
          <span class="ri__result-session">{{ item.sessionId || emptyText }}</span>
        </div>
        <pre class="ri__result-body">{{ bodyContent }}</pre>
      </article>
    </div>
  </details>

  <section v-else class="ri ri--empty">
    <div class="ri__empty">
      <p>{{ emptyCopy }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { getTaskExecutionFailureReason } from '@/utils/autoReverseTask';
import type { TaskExecutionItem, TaskExecutionToolItem } from '@/views/api';

type ActiveAgentKey = 'browser_agent' | 'analyse_agent';

const props = withDefaults(defineProps<{
  item: TaskExecutionItem | null;
  title: string;
  subtitle: string;
  emptyCopy: string;
  browserLabel: string;
  analyseLabel: string;
  mcpToolsLabel: string;
  noMcpToolsText: string;
  isMobile?: boolean;
  finalLabel: string;
  sessionLabel: string;
  updatedLabel: string;
  reportLabel: string;
  errorLabel: string;
  emptyText: string;
  noReport: string;
  initiallyOpen?: boolean;
  getTaskStatusLabel: (status: string) => string;
  formatDateTime: (value?: string | number | Date | null) => string;
  formatStageTime: (startedAt?: string, completedAt?: string) => string;
}>(), {
  initiallyOpen: false,
  isMobile: false,
});

function statusClass(status: string): string {
  const lower = status.toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'status-tag--success';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'status-tag--warning';
  if (lower.includes('skip')) return 'status-tag--skipped';
  if (lower.includes('fail') || lower.includes('error')) return 'status-tag--danger';
  return '';
}

function toolChipClass(status: string): string {
  const lower = status.toLowerCase();
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'ri__tool-chip--running';
  if (lower.includes('fail') || lower.includes('error')) return 'ri__tool-chip--danger';
  return 'ri__tool-chip--success';
}

function handleToggle(event: Event): void {
  isOpen.value = (event.currentTarget as HTMLDetailsElement).open;
}

const item = computed(() => props.item);
const isOpen = ref(Boolean(props.initiallyOpen));
const failureReason = computed(() => getTaskExecutionFailureReason(item.value));
const bodyLabel = computed(() => (failureReason.value ? props.errorLabel : props.reportLabel));
const bodyContent = computed(() => failureReason.value || item.value?.reportText || props.noReport);
const hoveredAgent = ref<ActiveAgentKey | null>(null);
const mobileAgent = ref<ActiveAgentKey | null>(null);

const activeAgent = computed<ActiveAgentKey | null>(() => (props.isMobile ? mobileAgent.value : hoveredAgent.value));
const activeAgentLabel = computed(() => {
  if (activeAgent.value === 'browser_agent') return props.browserLabel;
  if (activeAgent.value === 'analyse_agent') return props.analyseLabel;
  return '';
});
const activeAgentTools = computed<TaskExecutionToolItem[]>(() => {
  if (!item.value || !activeAgent.value) return [];
  return activeAgent.value === 'browser_agent' ? item.value.browserTools : item.value.analyseTools;
});

watch(item, () => {
  hoveredAgent.value = null;
  mobileAgent.value = null;
});

function setDesktopAgent(agent: ActiveAgentKey): void {
  if (props.isMobile) return;
  hoveredAgent.value = agent;
}

function clearDesktopAgentHover(): void {
  if (props.isMobile) return;
  hoveredAgent.value = null;
}

function toggleMobileAgent(agent: ActiveAgentKey): void {
  if (!props.isMobile) return;
  mobileAgent.value = mobileAgent.value === agent ? null : agent;
}

const {
  emptyCopy,
  browserLabel,
  analyseLabel,
  mcpToolsLabel,
  noMcpToolsText,
  emptyText,
  getTaskStatusLabel,
  formatDateTime,
} = props;
</script>

<style scoped>
.ri {
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--shadow-xs);
  min-width: 0;
  transition: border-color 200ms ease-out, box-shadow 200ms ease-out;
}

.ri:hover,
.ri[open] {
  border-color: var(--panel-border-strong);
}

.ri[open] {
  box-shadow: var(--panel-shadow);
}

.ri__summary {
  list-style: none;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  padding: 12px;
  cursor: pointer;
}

.ri__summary::-webkit-details-marker {
  display: none;
}

.ri__summary-main {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.ri__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ri__url {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.3;
  word-break: break-word;
  min-width: 0;
}

.ri__info-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
}

.ri__stage-chip {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--text-muted);
  white-space: nowrap;
}

.ri__stage-chip--action {
  cursor: pointer;
  font: inherit;
  transition: border-color 180ms ease, background 180ms ease, color 180ms ease, transform 180ms ease;
}

.ri__stage-chip--action:hover {
  transform: translateY(-1px);
}

.ri__stage-chip--action:focus-visible {
  outline: 2px solid rgba(var(--accent-rgb), 0.26);
  outline-offset: 1px;
}

.ri__stage-chip.status-tag--success {
  color: var(--success-500);
  border-color: color-mix(in srgb, var(--success-500) 20%, transparent);
  background: color-mix(in srgb, var(--success-500) 8%, transparent);
}

.ri__stage-chip.status-tag--warning {
  color: var(--warning-500);
  border-color: color-mix(in srgb, var(--warning-500) 20%, transparent);
  background: color-mix(in srgb, var(--warning-500) 8%, transparent);
}

.ri__stage-chip.status-tag--danger {
  color: var(--danger-500);
  border-color: color-mix(in srgb, var(--danger-500) 20%, transparent);
  background: color-mix(in srgb, var(--danger-500) 8%, transparent);
}

.ri__time {
  font-size: 0.66rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  margin-left: auto;
}

.ri__tool-reveal {
  display: grid;
  gap: 6px;
  padding-top: 2px;
}

.ri__tool-reveal-label {
  color: var(--text-muted);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.ri__tool-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.ri__tool-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 20px;
  padding: 0 7px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  color: var(--text-secondary);
  font-size: 0.64rem;
  font-weight: 600;
  white-space: nowrap;
}

.ri__tool-chip--running {
  color: var(--accent-500);
  border-color: rgba(var(--accent-rgb), 0.26);
  background: rgba(var(--accent-rgb), 0.08);
}

.ri__tool-chip--success {
  color: var(--success-500);
  border-color: color-mix(in srgb, var(--success-500) 18%, transparent);
  background: color-mix(in srgb, var(--success-500) 6%, transparent);
}

.ri__tool-chip--danger {
  color: var(--danger-500);
  border-color: color-mix(in srgb, var(--danger-500) 18%, transparent);
  background: color-mix(in srgb, var(--danger-500) 6%, transparent);
}

.ri__tool-chip-count {
  opacity: 0.72;
  font-variant-numeric: tabular-nums;
}

.ri__tool-empty {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.ri__chevron {
  width: 11px;
  height: 11px;
  margin-top: 6px;
  border-right: 2px solid var(--text-muted);
  border-bottom: 2px solid var(--text-muted);
  transform: rotate(45deg);
  transition: transform 180ms ease;
}

.ri[open] .ri__chevron {
  transform: rotate(225deg);
}

.ri__body {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 0 12px 12px;
}

.ri__result {
  display: grid;
  gap: 0;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid var(--code-surface-border);
  background: var(--code-surface-bg);
}

.ri__result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--code-surface-border) 75%, transparent);
  background: color-mix(in srgb, var(--code-surface-bg) 84%, rgba(255, 255, 255, 0.04));
}

.ri__result-label,
.ri__result-session {
  color: rgba(226, 232, 240, 0.72);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.ri__result-body {
  margin: 0;
  min-height: 120px;
  max-height: 360px;
  overflow: auto;
  padding: 10px 12px;
  background: transparent;
  color: var(--code-surface-text);
  white-space: pre-wrap;
  line-height: 1.6;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  tab-size: 2;
}

.ri__result-body::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.ri__result-body::-webkit-scrollbar-thumb {
  border: 2px solid rgba(15, 23, 42, 0.9);
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.72);
}

.ri__empty {
  padding: 18px;
  color: var(--text-muted);
}

.ri__summary:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.26);
  outline-offset: -2px;
}

.ri-tools-fade-enter-active,
.ri-tools-fade-leave-active {
  transition: opacity 140ms ease, transform 140ms ease;
}

.ri-tools-fade-enter-from,
.ri-tools-fade-leave-to {
  opacity: 0;
  transform: translateY(-2px);
}

@media (prefers-reduced-motion: reduce) {
  .ri__stage-chip--action,
  .ri-tools-fade-enter-active,
  .ri-tools-fade-leave-active {
    transition: none;
  }
}

@media (max-width: 760px) {
  .ri__summary {
    grid-template-columns: 1fr auto;
  }

  .ri__info-bar {
    gap: 6px;
  }

  .ri__time {
    width: 100%;
    margin-left: 0;
  }
}
</style>
