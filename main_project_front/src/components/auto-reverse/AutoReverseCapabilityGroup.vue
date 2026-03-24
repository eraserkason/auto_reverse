<template>
  <div class="cap-group" :class="capabilityClasses">
    <button type="button" class="cap-group__toggle" @click="expanded = !expanded">
      <div class="cap-group__toggle-left">
        <span class="cap-group__label">{{ label }}</span>
        <n-tag :bordered="false" round size="tiny" :type="variant === 'assistant' ? 'info' : 'default'">
          {{ count }}/{{ total }}
        </n-tag>
      </div>
      <svg :class="{ 'cap-group__arrow--open': expanded }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
        <path d="m6 9 6 6 6-6" />
      </svg>
    </button>

    <p v-if="hint && expanded" class="cap-group__hint">{{ hint }}</p>

    <transition name="cap-slide">
      <div v-if="expanded" class="cap-group__body">
        <div v-if="items.length > 0" class="cap-group__list">
          <label
            v-for="item in items"
            :key="item.value"
            class="cap-group__chip"
            :class="{
              'cap-group__chip--active': item.selected,
              'cap-group__chip--locked': item.tone === 'locked',
              'cap-group__chip--disabled': item.disabled,
            }"
          >
            <n-checkbox
              :checked="item.selected"
              :disabled="item.disabled"
              size="small"
              @update:checked="(checked) => emit('toggle', item.value, checked)"
            />
            <span class="cap-group__chip-name">{{ item.label || item.value }}</span>
            <span v-if="item.meta" class="cap-group__chip-meta">{{ item.meta }}</span>
          </label>
        </div>
        <p v-else class="cap-group__empty">{{ emptyText }}</p>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { NCheckbox, NTag } from 'naive-ui';

export interface AutoReverseCapabilityItem {
  value: string;
  label?: string;
  selected: boolean;
  disabled?: boolean;
  meta?: string;
  tone?: 'default' | 'soft' | 'locked';
}

const props = withDefaults(
  defineProps<{
    label: string;
    count: number;
    total: number;
    hint?: string;
    items: AutoReverseCapabilityItem[];
    emptyText: string;
    defaultOpen?: boolean;
    soft?: boolean;
    variant?: 'default' | 'assistant';
  }>(),
  {
    hint: '',
    defaultOpen: false,
    soft: false,
    variant: 'default',
  },
);

const emit = defineEmits<{
  (e: 'toggle', value: string, checked: boolean): void;
}>();

const expanded = ref(props.defaultOpen);

const capabilityClasses = computed(() => ({
  'cap-group--soft': props.soft,
  'cap-group--assistant': props.variant === 'assistant',
}));
</script>

<style scoped>
.cap-group {
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  overflow: hidden;
  transition: border-color var(--transition-base);
}

.cap-group:hover {
  border-color: var(--panel-border-strong);
}

.cap-group--assistant {
  border-color: rgba(var(--accent-rgb), 0.18);
}

.cap-group__toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  background: none;
  cursor: pointer;
  font: inherit;
  color: var(--text-primary);
  transition: background-color var(--transition-base);
}

.cap-group__toggle:hover {
  background: rgba(var(--accent-rgb), 0.04);
}

.cap-group__toggle-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.cap-group__label {
  color: var(--text-secondary);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.cap-group__toggle svg {
  color: var(--text-muted);
  transition: transform var(--transition-base);
  flex-shrink: 0;
}

.cap-group__arrow--open {
  transform: rotate(180deg);
}

.cap-group__hint {
  margin: 0;
  padding: 0 14px 8px;
  color: var(--text-muted);
  font-size: 0.78rem;
  line-height: 1.45;
}

.cap-group__body {
  padding: 0 12px 12px;
}

.cap-group__list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cap-group__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  cursor: pointer;
  transition: all var(--transition-base);
}

.cap-group__chip:hover:not(.cap-group__chip--disabled) {
  border-color: var(--panel-border-strong);
}

.cap-group__chip--active {
  border-color: rgba(var(--accent-rgb), 0.28);
  background: rgba(var(--accent-rgb), 0.08);
}

.cap-group__chip--locked {
  border-color: color-mix(in srgb, var(--warning-500) 24%, transparent);
  background: color-mix(in srgb, var(--warning-500) 8%, transparent);
}

.cap-group__chip--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cap-group__chip-name {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

.cap-group__chip-meta {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.cap-group__chip :deep(.n-checkbox) {
  margin-right: 0;
}

.cap-group__empty {
  margin: 0;
  padding: 8px 4px;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.cap-slide-enter-active,
.cap-slide-leave-active {
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.cap-slide-enter-from,
.cap-slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-bottom: 0;
}

.cap-slide-enter-to,
.cap-slide-leave-from {
  opacity: 1;
  max-height: 400px;
}
</style>
