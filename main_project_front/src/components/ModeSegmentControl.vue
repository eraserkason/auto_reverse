<template>
  <section class="mode-seg">
    <header v-if="eyebrow || title" class="mode-seg__head">
      <div class="mode-seg__copy">
        <span v-if="eyebrow" class="mode-seg__eyebrow">{{ eyebrow }}</span>
        <h4 v-if="title">{{ title }}</h4>
      </div>
    </header>

    <div class="mode-seg__track" role="radiogroup" :aria-label="title || eyebrow || groupName">
      <label
        v-for="option in options"
        :key="option.value"
        class="mode-seg__option"
        :class="{
          'mode-seg__option--active': modelValue === option.value,
          'mode-seg__option--disabled': option.disabled,
        }"
      >
        <input
          :name="groupName"
          class="mode-seg__input"
          type="radio"
          :value="option.value"
          :checked="modelValue === option.value"
          :disabled="option.disabled"
          @change="emit('update:modelValue', option.value)"
        />
        <span class="mode-seg__body">
          <span v-if="option.badge" class="mode-seg__topline">
            <small class="mode-seg__badge">{{ option.badge }}</small>
          </span>
          <strong class="mode-seg__label">{{ option.label }}</strong>
          <span v-if="option.meta" class="mode-seg__meta">{{ option.meta }}</span>
        </span>
      </label>
    </div>

    <p v-if="resolvedHelper" class="mode-seg__helper">{{ resolvedHelper }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type ModeSegmentOption = {
  value: string;
  label: string;
  badge?: string;
  meta?: string;
  description?: string;
  disabled?: boolean;
};

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: ModeSegmentOption[];
    eyebrow?: string;
    title?: string;
    helper?: string;
    status?: string;
    activeTag?: string;
    name?: string;
  }>(),
  {
    eyebrow: '',
    title: '',
    helper: '',
    status: '',
    activeTag: '',
    name: '',
  },
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const groupName = props.name || `mode-seg-${Math.random().toString(36).slice(2, 10)}`;

const selectedOption = computed(() => props.options.find((option) => option.value === props.modelValue));
const resolvedHelper = computed(() => props.helper || selectedOption.value?.description || '');
</script>

<style scoped>
.mode-seg {
  display: grid;
  gap: 14px;
  padding: 20px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out;
}

.mode-seg:hover {
  border-color: var(--panel-border-strong);
}

.mode-seg__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.mode-seg__copy {
  display: grid;
  gap: 4px;
}

.mode-seg__eyebrow {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.mode-seg__copy h4 {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.96rem;
}

.mode-seg__status-badge,
.mode-seg__badge,
.mode-seg__active-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
}

.mode-seg__status-badge,
.mode-seg__badge {
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-muted);
}

.mode-seg__active-tag {
  border: 1px solid rgba(var(--accent-rgb), 0.22);
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent-500);
}

.mode-seg__track {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 6px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
}

.mode-seg__option {
  position: relative;
  cursor: pointer;
}

.mode-seg__option--disabled {
  cursor: not-allowed;
}

.mode-seg__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: inherit;
}

.mode-seg__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.mode-seg__body {
  display: grid;
  gap: 5px;
  min-height: 68px;
  padding: 12px;
  border-radius: 12px;
  border: 2px solid transparent;
  background: var(--panel-bg);
  overflow: hidden;
  transition: border-color 200ms ease-out, background 200ms ease-out, box-shadow 200ms ease-out;
}

.mode-seg__option:hover .mode-seg__body {
  border-color: var(--panel-border-strong);
}

.mode-seg__option--active .mode-seg__body {
  border-color: var(--accent-500);
  background: var(--panel-accent-bg);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.mode-seg__input:focus-visible + .mode-seg__body {
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.24);
}

.mode-seg__option--disabled .mode-seg__body {
  opacity: 0.56;
}

.mode-seg__label {
  color: var(--text-primary);
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.mode-seg__meta,
.mode-seg__helper {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.78rem;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

@media (max-width: 720px) {
  .mode-seg {
    padding: 16px;
    border-radius: 16px;
  }

  .mode-seg__head {
    flex-direction: column;
  }

  .mode-seg__track {
    grid-template-columns: 1fr;
  }

  .mode-seg__body {
    min-height: auto;
  }
}
</style>
