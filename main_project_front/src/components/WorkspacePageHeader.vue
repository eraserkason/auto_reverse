<template>
  <n-page-header class="workspace-page-header">
    <template #title>
      <div class="workspace-page-header__copy">
        <span v-if="eyebrow" class="workspace-page-header__eyebrow">
          {{ eyebrow }}
        </span>
        <h1>{{ title }}</h1>
      </div>
    </template>
    
    <template #subtitle>
      <span v-if="subtitle">{{ subtitle }}</span>
      <div v-if="tags.length > 0" class="workspace-page-header__tags">
        <n-tag
          v-for="tag in tags"
          :key="`${tag.label}-${tag.type || 'default'}`"
          :bordered="false"
          size="small"
          :type="tag.type || 'default'"
          round
        >
          {{ tag.label }}
        </n-tag>
      </div>
    </template>

    <template #extra>
      <div v-if="$slots.actions" class="workspace-page-header__actions">
        <slot name="actions" />
      </div>
    </template>

    <n-grid
      v-if="showStats && stats.length > 0"
      cols="1 620:2 1100:4"
      x-gap="12"
      y-gap="12"
      class="workspace-page-header__stats"
    >
      <n-grid-item v-for="stat in stats" :key="`${stat.label}-${stat.value}`">
        <n-card size="small" hoverable class="workspace-page-header__stat-card">
          <n-statistic :label="stat.label" :value="stat.value">
            <template #suffix v-if="stat.caption">
              <span class="workspace-page-header__stat-caption">{{ stat.caption }}</span>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>
  </n-page-header>
</template>

<script setup lang="ts">
import { NPageHeader, NGrid, NGridItem, NTag, NCard, NStatistic } from 'naive-ui';

export type WorkspaceHeaderTag = {
  label: string;
  type?: 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error';
};

export type WorkspaceHeaderStat = {
  label: string;
  value: string | number;
  caption?: string;
};

withDefaults(
  defineProps<{
    eyebrow?: string;
    title: string;
    subtitle?: string;
    tags?: WorkspaceHeaderTag[];
    stats?: WorkspaceHeaderStat[];
    showStats?: boolean;
  }>(),
  {
    eyebrow: '',
    subtitle: '',
    tags: () => [],
    stats: () => [],
    showStats: false,
  },
);
</script>

<style scoped>
.workspace-page-header {
  padding: 22px 24px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--n-color-modal) 90%, transparent);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--n-border-color);
  box-shadow: var(--shadow-xs);
}

.workspace-page-header__copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.workspace-page-header__eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--n-text-color-3);
}

.workspace-page-header h1 {
  margin: 0;
  font-size: clamp(1.4rem, 1.1vw + 1.1rem, 1.85rem);
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.workspace-page-header__tags {
  display: inline-flex;
  gap: 8px;
  margin-left: 12px;
  vertical-align: middle;
}

.workspace-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
  align-items: center;
}

.workspace-page-header__stats {
  margin-top: 16px;
}

.workspace-page-header__stat-card {
  border-radius: 16px;
  background: var(--bg-surface-muted);
}

.workspace-page-header__stat-caption {
  font-size: 0.8rem;
  color: var(--n-text-color-3);
}

@media (max-width: 767px) {
  .workspace-page-header :deep(.n-page-header-header) {
    flex-direction: column;
    align-items: flex-start;
  }

  .workspace-page-header__actions {
    margin-top: 12px;
    width: 100%;
    justify-content: flex-start;
  }

  .workspace-page-header {
    padding: 18px 16px;
    border-radius: 18px;
  }

  .workspace-page-header__tags {
    display: flex;
    flex-wrap: wrap;
    margin-left: 0;
    margin-top: 8px;
  }
}
</style>
