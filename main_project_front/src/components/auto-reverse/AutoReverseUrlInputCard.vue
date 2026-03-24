<template>
  <article class="url-card">
    <div class="url-card__head">
      <label v-if="title" class="url-card__label" :for="resolvedInputId">{{ title }}</label>
      <div class="url-card__count-pill">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" width="13" height="13">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
        <strong>{{ count || '00' }}</strong>
      </div>
    </div>

    <div class="url-card__editor">
      <n-input
        :id="resolvedInputId"
        v-model:value="value"
        type="textarea"
        class="url-card__textarea"
        :autosize="{ minRows: 5, maxRows: 14 }"
        :placeholder="placeholder"
        :aria-describedby="hintId"
        autocomplete="off"
        autocapitalize="off"
        spellcheck="false"
      />
    </div>

    <p v-if="helperText" :id="hintId" class="url-card__hint">{{ helperText }}</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { NInput } from 'naive-ui';

const props = defineProps<{
  eyebrow: string;
  title: string;
  placeholder: string;
  modelValue: string;
  count: string;
  helperText: string;
  inputId?: string;
  name?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const value = computed({
  get: () => props.modelValue,
  set: (next: string) => emit('update:modelValue', next),
});

const resolvedInputId = computed(() => props.inputId || 'auto-reverse-url-list');
const hintId = computed(() => `${resolvedInputId.value}-hint`);
</script>

<style scoped>
.url-card {
  display: grid;
  gap: 12px;
  padding: 20px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out, box-shadow 200ms ease-out;
}

.url-card:focus-within {
  border-color: rgba(var(--accent-rgb), 0.32);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.08), var(--shadow-xs);
}

.url-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.url-card__label {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary);
  cursor: text;
}

.url-card__count-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent-500);
  font-size: 0.74rem;
  flex-shrink: 0;
}

.url-card__count-pill strong {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.url-card__editor {
  border-radius: 14px;
  overflow: hidden;
}

.url-card__textarea :deep(textarea) {
  font-family: var(--font-mono);
  font-size: 0.86rem;
  line-height: 1.72;
}

.url-card__hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.76rem;
  line-height: 1.5;
}

@media (max-width: 680px) {
  .url-card {
    padding: 16px;
    border-radius: 16px;
  }

  .url-card__hint {
    display: none;
  }
}
</style>
