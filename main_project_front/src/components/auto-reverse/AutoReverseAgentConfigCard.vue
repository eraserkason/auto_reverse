<template>
  <article class="agent-card" :class="[`agent-card--${accent}`, { 'agent-card--active': active }]">
    <div class="agent-card__head">
      <div class="agent-card__identity">
        <div class="agent-card__icon">
          <svg v-if="accent === 'browser'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <div>
          <span class="agent-card__eyebrow">{{ eyebrow }}</span>
          <h4>{{ title }}</h4>
        </div>
      </div>
      <span class="agent-card__dot" :class="{ 'agent-card__dot--on': active }"></span>
    </div>

    <div class="agent-card__field">
      <span class="agent-card__field-label">{{ modelLabel }}</span>
      <n-select
        :value="selectedModelProfileKey || null"
        :options="modelOptions"
        :placeholder="modelPlaceholder"
        :disabled="isModelFieldDisabled"
        filterable
        clearable
        size="small"
        @update:value="handleModelUpdate"
      />
    </div>

    <AutoReverseCapabilityGroup
      :label="mcpLabel"
      :count="mcpCount"
      :total="mcpTotal"
      :hint="mcpHint"
      :items="mcpItems"
      :empty-text="mcpEmptyText"
      :default-open="false"
      @toggle="(value, checked) => emit('toggleMcp', value, checked)"
    />

    <AutoReverseCapabilityGroup
      :label="skillsLabel"
      :count="skillCount"
      :total="skillTotal"
      :items="skillItems"
      :empty-text="skillEmptyText"
      :soft="true"
      @toggle="(value, checked) => emit('toggleSkill', value, checked)"
    />
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { NSelect } from 'naive-ui';

import type { ModelProfileOption } from '@/views/api';
import AutoReverseCapabilityGroup, { type AutoReverseCapabilityItem } from './AutoReverseCapabilityGroup.vue';

const props = defineProps<{
  accent: 'browser' | 'analyse';
  agentId: string;
  eyebrow: string;
  title: string;
  selectedModelProfileKey: string;
  selectedModelLabel: string;
  modelProfiles: ModelProfileOption[];
  modelPlaceholder: string;
  modelDisabled: boolean;
  modelLabel: string;
  mcpLabel: string;
  skillsLabel: string;
  mcpItems: AutoReverseCapabilityItem[];
  mcpCount: number;
  mcpTotal: number;
  mcpHint?: string;
  mcpEmptyText: string;
  skillItems: AutoReverseCapabilityItem[];
  skillCount: number;
  skillTotal: number;
  skillEmptyText: string;
  active: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelProfileKey', value: string): void;
  (e: 'toggleMcp', value: string, checked: boolean): void;
  (e: 'toggleSkill', value: string, checked: boolean): void;
}>();

const isModelFieldDisabled = computed(() => props.modelDisabled || props.modelProfiles.length === 0);
const modelOptions = computed(() =>
  props.modelProfiles.map((profile) => ({
    label: profile.label,
    value: profile.key,
  })),
);

function handleModelUpdate(value: string | null): void {
  emit('update:modelProfileKey', value ?? '');
}
</script>

<style scoped>
.agent-card {
  --agent-rgb: var(--accent-rgb);
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out, box-shadow 200ms ease-out;
  align-content: start;
}

.agent-card--analyse {
  --agent-rgb: 108, 151, 186;
}

.agent-card:hover {
  border-color: rgba(var(--agent-rgb), 0.24);
}

.agent-card--active {
  border-color: rgba(var(--agent-rgb), 0.32);
  box-shadow: 0 0 0 3px rgba(var(--agent-rgb), 0.08), var(--shadow-xs);
}

.agent-card__head {
  display: none;
}

.agent-card__field {
  display: grid;
  gap: 5px;
}

.agent-card__field-label {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

@media (max-width: 767px) {
  .agent-card {
    padding: 12px;
    border-radius: 12px;
  }
}
</style>
