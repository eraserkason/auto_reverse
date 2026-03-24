<template>
  <details class="auto-reverse-report" :class="{ 'auto-reverse-report--archive': archive }">
    <summary class="auto-reverse-report__summary">
      <div class="auto-reverse-report__copy">
        <p class="auto-reverse-report__title">{{ title }}</p>
        <p class="auto-reverse-report__meta">{{ meta }}</p>
      </div>

      <div class="auto-reverse-report__aside">
        <div class="auto-reverse-report__aside-main">
          <span class="status-tag" :class="statusClass">{{ statusLabel }}</span>
          <span class="auto-reverse-report__disclosure" aria-hidden="true"></span>
        </div>
        <p v-if="timestamp">{{ timestamp }}</p>
      </div>
    </summary>

    <div class="auto-reverse-report__body-shell">
      <div class="auto-reverse-report__body-head">
        <span class="auto-reverse-report__body-label">{{ title }}</span>
      </div>
      <pre class="auto-reverse-report__body">{{ content }}</pre>
    </div>
  </details>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    meta: string;
    statusLabel: string;
    statusClass?: string;
    content: string;
    timestamp?: string;
    archive?: boolean;
  }>(),
  {
    statusClass: '',
    timestamp: '',
    archive: false,
  },
);
</script>

<style scoped>
.auto-reverse-report {
  overflow: hidden;
  content-visibility: auto;
  contain-intrinsic-size: 160px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out;
}

.auto-reverse-report--archive {
  border-color: rgba(34, 197, 94, 0.16);
  background: linear-gradient(180deg, color-mix(in srgb, var(--success-500) 12%, var(--panel-bg)), var(--panel-bg));
}

.auto-reverse-report[open] {
  border-color: rgba(var(--accent-rgb), 0.24);
  box-shadow: var(--panel-shadow);
}

.auto-reverse-report__summary {
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  background: transparent;
}

.auto-reverse-report__summary::-webkit-details-marker {
  display: none;
}

.auto-reverse-report__copy,
.auto-reverse-report__aside {
  display: grid;
  gap: 8px;
}

.auto-reverse-report__aside {
  justify-items: end;
  text-align: right;
  align-content: start;
}

.auto-reverse-report__aside-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.auto-reverse-report__title,
.auto-reverse-report__meta,
.auto-reverse-report__aside p {
  margin: 0;
}

.auto-reverse-report__title {
  color: var(--text-primary);
  font-size: 0.88rem;
  font-weight: 700;
  word-break: break-word;
  line-height: 1.35;
}

.auto-reverse-report__meta,
.auto-reverse-report__aside p {
  color: var(--text-muted);
  font-size: 0.82rem;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
}

.auto-reverse-report__disclosure {
  width: 11px;
  height: 11px;
  border-right: 2px solid var(--text-muted);
  border-bottom: 2px solid var(--text-muted);
  transform: rotate(45deg);
  transition: transform 180ms ease;
}

.auto-reverse-report[open] .auto-reverse-report__disclosure {
  transform: rotate(225deg);
}

.auto-reverse-report__body-shell {
  margin: 0 12px 12px;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid var(--code-surface-border);
  background: var(--code-surface-bg);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.auto-reverse-report__body-head {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

.auto-reverse-report__body-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(226, 232, 240, 0.72);
  font-family: var(--font-mono);
  font-size: 0.76rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.auto-reverse-report__body {
  margin: 0;
  min-height: 100px;
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

.auto-reverse-report__body::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.auto-reverse-report__body::-webkit-scrollbar-thumb {
  border: 2px solid rgba(15, 23, 42, 0.9);
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.72);
}

.auto-reverse-report__summary:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.26);
  outline-offset: -2px;
}

@media (max-width: 760px) {
  .auto-reverse-report__summary {
    flex-direction: column;
  }

  .auto-reverse-report__aside {
    justify-items: start;
    text-align: left;
  }

  .auto-reverse-report__aside-main {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
