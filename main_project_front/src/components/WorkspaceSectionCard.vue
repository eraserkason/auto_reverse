<template>
  <n-card :bordered="false" :size="size" class="workspace-section-card">
    <template v-if="title || $slots.header" #header>
      <slot name="header">
        <div class="workspace-section-card__header">
          <div class="workspace-section-card__copy">
            <span v-if="eyebrow" class="workspace-section-card__eyebrow">{{ eyebrow }}</span>
            <n-h3 style="margin: 0; font-weight: 600;">{{ title }}</n-h3>
            <span v-if="description" class="workspace-section-card__description">{{ description }}</span>
          </div>
          <div v-if="$slots.actions" class="workspace-section-card__actions">
            <slot name="actions" />
          </div>
        </div>
      </slot>
    </template>
    <slot />
  </n-card>
</template>

<script setup lang="ts">
import { NCard, NH3 } from 'naive-ui';

withDefaults(
  defineProps<{
    eyebrow?: string;
    title?: string;
    description?: string;
    size?: 'small' | 'medium' | 'large' | 'huge';
  }>(),
  {
    eyebrow: '',
    title: '',
    description: '',
    size: 'medium',
  },
);
</script>

<style scoped>
.workspace-section-card {
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow-xs);
  transition: box-shadow 200ms ease-out, border-color 200ms ease-out;
}

.workspace-section-card:hover {
  box-shadow: var(--panel-shadow);
  border-color: var(--panel-border-strong);
}

.workspace-section-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.workspace-section-card__copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.workspace-section-card__eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--n-text-color-3);
}

.workspace-section-card__description {
  font-size: 0.84rem;
  color: var(--n-text-color-2);
  line-height: 1.55;
  max-width: 60ch;
}

.workspace-section-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 767px) {
  .workspace-section-card {
    border-radius: 14px;
    --n-padding-top: 14px !important;
    --n-padding-bottom: 14px !important;
    --n-padding-left: 16px !important;
  }

  .workspace-section-card__header {
    flex-direction: column;
  }

  .workspace-section-card__actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
