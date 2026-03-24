<template>
  <div class="auto-reverse-runtime-summary">
    <article
      v-for="card in cards"
      :key="`${card.label}-${card.value}`"
      class="auto-reverse-runtime-summary__card"
      :class="{
        'auto-reverse-runtime-summary__card--primary': card.tone === 'primary',
        'auto-reverse-runtime-summary__card--mono': card.tone === 'mono',
      }"
    >
      <p class="auto-reverse-runtime-summary__label">{{ card.label }}</p>
      <strong class="auto-reverse-runtime-summary__value">{{ card.value }}</strong>
      <p v-if="card.meta" class="auto-reverse-runtime-summary__meta">{{ card.meta }}</p>
    </article>
  </div>
</template>

<script setup lang="ts">
interface RuntimeSummaryCard {
  label: string;
  value: string | number;
  meta?: string;
  tone?: 'primary' | 'mono' | 'neutral';
}

defineProps<{
  cards: RuntimeSummaryCard[];
}>();
</script>

<style scoped>
.auto-reverse-runtime-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(140px, 100%), 1fr));
  gap: 8px;
}

.auto-reverse-runtime-summary__card {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  transition: border-color 200ms ease-out;
}

.auto-reverse-runtime-summary__card:hover {
  border-color: var(--panel-border-strong);
}

.auto-reverse-runtime-summary__card--primary {
  border-color: color-mix(in srgb, var(--accent-500) 18%, transparent);
  background: color-mix(in srgb, var(--accent-500) 4%, var(--panel-bg-soft));
}

.auto-reverse-runtime-summary__card--mono {
  border-color: var(--panel-border);
  background: var(--panel-bg-soft);
}

.auto-reverse-runtime-summary__card--mono .auto-reverse-runtime-summary__value {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  word-break: break-all;
  color: var(--text-secondary);
}

.auto-reverse-runtime-summary__label,
.auto-reverse-runtime-summary__value,
.auto-reverse-runtime-summary__meta {
  margin: 0;
}

.auto-reverse-runtime-summary__label,
.auto-reverse-runtime-summary__meta {
  color: var(--text-muted);
}

.auto-reverse-runtime-summary__label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.auto-reverse-runtime-summary__value {
  color: var(--text-primary);
  font-size: 0.96rem;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.02em;
}

.auto-reverse-runtime-summary__meta {
  font-size: 0.72rem;
  line-height: 1.4;
  margin-top: auto;
}
</style>
