<template>
  <article class="app-card">
    <header v-if="title || $slots.header" class="app-card__header">
      <slot name="header">
        <h3 class="app-card__title">{{ title }}</h3>
      </slot>
      <p v-if="description" class="app-card__desc">{{ description }}</p>
    </header>
    <div class="app-card__body">
      <slot />
    </div>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<style scoped>
.app-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  box-shadow: var(--shadow-soft);
}

.app-card__header {
  margin-bottom: var(--space-4);
}

.app-card__title {
  margin: 0;
  font-size: 1.04rem;
  color: var(--text-primary);
}

.app-card__desc {
  margin: var(--space-2) 0 0;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.app-card__body {
  color: var(--text-secondary);
}
</style>
