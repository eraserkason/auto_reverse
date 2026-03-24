<template>
  <section class="panel auto-reverse-hero">
    <div class="auto-reverse-hero__header">
      <div class="auto-reverse-hero__copy">
        <p class="page-eyebrow">{{ eyebrow }}</p>
        <h1 class="auto-reverse-hero__title">{{ title }}</h1>
        <p class="auto-reverse-hero__subtitle">{{ subtitle }}</p>
      </div>

      <n-button secondary class="auto-reverse-hero__action" :disabled="loading" @click="emit('reload')">
        {{ loading ? actionLoadingLabel : actionLabel }}
      </n-button>
    </div>

    <div v-if="badges.length > 0" class="auto-reverse-hero__badges" aria-label="hero-badges">
      <span v-for="badge in badges" :key="badge" class="soft-badge">{{ badge }}</span>
    </div>

    <div v-if="stats.length > 0" class="auto-reverse-hero__stats">
      <article
        v-for="stat in stats"
        :key="`${stat.label}-${stat.value}`"
        class="auto-reverse-hero__stat"
        :class="{
          'auto-reverse-hero__stat--accent': stat.tone === 'accent',
          'auto-reverse-hero__stat--mono': stat.tone === 'mono',
        }"
      >
        <p class="auto-reverse-hero__stat-label">{{ stat.label }}</p>
        <strong class="auto-reverse-hero__stat-value">{{ stat.value }}</strong>
        <p v-if="stat.hint" class="auto-reverse-hero__stat-hint">{{ stat.hint }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui';

interface HeroStat {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'accent' | 'mono' | 'neutral';
}

defineProps<{
  eyebrow: string;
  title: string;
  subtitle: string;
  badges: string[];
  stats: HeroStat[];
  loading: boolean;
  actionLabel: string;
  actionLoadingLabel: string;
}>();

const emit = defineEmits<{
  (e: 'reload'): void;
}>();
</script>

<style scoped>
.auto-reverse-hero {
  display: grid;
  gap: 16px;
  padding: 22px;
  border-radius: 22px;
  border-color: var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-highlight), var(--panel-shadow);
}

.auto-reverse-hero__header,
.auto-reverse-hero__copy,
.auto-reverse-hero__stats {
  display: grid;
}

.auto-reverse-hero__header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 20px;
}

.auto-reverse-hero__copy {
  gap: 10px;
}

.auto-reverse-hero__copy .page-eyebrow,
.auto-reverse-hero__title,
.auto-reverse-hero__subtitle,
.auto-reverse-hero__stat-label,
.auto-reverse-hero__stat-value,
.auto-reverse-hero__stat-hint {
  margin: 0;
}

.auto-reverse-hero__copy .page-eyebrow {
  color: var(--text-secondary);
}

.auto-reverse-hero__title {
  font-size: clamp(1.72rem, 1.3vw + 1.2rem, 2.34rem);
  letter-spacing: -0.03em;
  line-height: 1.12;
}

.auto-reverse-hero__subtitle {
  max-width: 64ch;
  color: var(--text-secondary);
  font-size: 0.94rem;
  line-height: 1.6;
}

.auto-reverse-hero__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.auto-reverse-hero__badges .soft-badge {
  border-color: var(--panel-border);
  background: var(--panel-bg-soft);
}

  .auto-reverse-hero__stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }

.auto-reverse-hero__stat {
  display: grid;
  gap: 6px;
  min-height: 92px;
  padding: 14px 15px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  box-shadow: var(--panel-highlight);
}

.auto-reverse-hero__stat--accent {
  border-color: var(--panel-border-strong);
  background: var(--panel-accent-bg);
}

.auto-reverse-hero__stat--mono .auto-reverse-hero__stat-value {
  font-family: var(--font-mono);
  font-size: 0.9rem;
  word-break: break-word;
}

.auto-reverse-hero__stat-label {
  color: var(--text-secondary);
  font-size: 0.76rem;
  font-weight: 700;
}

.auto-reverse-hero__stat-value {
  color: var(--text-primary);
  font-size: 1.08rem;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.01em;
}

.auto-reverse-hero__stat-hint {
  color: var(--text-muted);
  font-size: 0.78rem;
  line-height: 1.5;
  margin-top: auto;
}

.auto-reverse-hero__action {
  min-width: 148px;
}

@media (max-width: 1080px) {
  .auto-reverse-hero__header {
    grid-template-columns: 1fr;
  }

  .auto-reverse-hero__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .auto-reverse-hero {
    padding: 18px;
  }

  .auto-reverse-hero__stats {
    grid-template-columns: 1fr;
  }
}
</style>
