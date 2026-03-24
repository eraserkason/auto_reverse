<template>
  <n-card hoverable class="stat-card" size="small" :bordered="false">
    <div class="stat-card__content">
      <div class="stat-card__main">
        <span class="stat-card__label">{{ label }}</span>
        <span class="stat-card__value">{{ value }}</span>
      </div>
      <div v-if="$slots.icon" class="stat-card__icon-wrapper">
        <slot name="icon"></slot>
      </div>
    </div>
    
    <div v-if="captionText || hasTrend" class="stat-card__footer">
      <span v-if="captionText" class="stat-card__caption">{{ captionText }}</span>
      <n-tag v-if="hasTrend" :bordered="false" size="small" :type="trendType" round class="stat-card__trend">
        <template #icon v-if="trendType === 'success'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
        </template>
        <template #icon v-else-if="trendType === 'error'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>
        </template>
        {{ trendText }}
      </n-tag>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { NCard, NTag } from 'naive-ui';
import { useLocale } from '@/composables/useLocale';

const props = withDefaults(
  defineProps<{
    label: string;
    value: string | number;
    trend?: number | null;
    caption?: string;
  }>(),
  {
    trend: null,
    caption: '',
  },
);

const { t } = useLocale();
const hasTrend = computed(() => typeof props.trend === 'number');
const captionText = computed(() => props.caption.trim());

const trendType = computed<'success' | 'error' | 'default'>(() => {
  if ((props.trend ?? 0) > 0) return 'success';
  if ((props.trend ?? 0) < 0) return 'error';
  return 'default';
});

const trendText = computed(() => {
  const trendValue = props.trend ?? 0;
  if (trendValue > 0) return t('statCard.trend.up', { value: trendValue });
  if (trendValue < 0) return t('statCard.trend.down', { value: trendValue });
  return t('statCard.trend.flat');
});
</script>

<style scoped>
.stat-card {
  height: 100%;
  border-radius: var(--n-border-radius);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  overflow: hidden;
}

html[data-theme="light"] .stat-card {
  box-shadow: var(--n-box-shadow-1);
}

html[data-theme="dark"] .stat-card {
  border: 1px solid var(--n-border-color);
}

.stat-card:hover {
  transform: translateY(-2px);
}

html[data-theme="light"] .stat-card:hover {
  box-shadow: var(--n-box-shadow-2);
}

html[data-theme="dark"] .stat-card:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.stat-card__content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.stat-card__main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-card__label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--n-text-color-2);
  letter-spacing: 0.02em;
}

.stat-card__value {
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--n-text-color-base);
  line-height: 1.1;
  font-family: var(--n-font-family-mono, monospace);
}

.stat-card__icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background-color: var(--n-color-modal);
  color: var(--n-primary-color);
}

html[data-theme="light"] .stat-card__icon-wrapper {
  background-color: rgba(var(--n-primary-color-rgb, 99, 102, 241), 0.1);
}

.stat-card__icon-wrapper :deep(svg) {
  width: 20px;
  height: 20px;
}

.stat-card__footer {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.stat-card__caption {
  font-size: 0.8rem;
  color: var(--n-text-color-3);
}

.stat-card__trend {
  font-weight: 500;
  padding: 0 8px;
}
</style>