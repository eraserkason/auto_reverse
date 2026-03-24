<template>
  <Teleport to="body" :disabled="isInlineTaskSystem">
  <aside
      :id="taskSystemPanelId"
      ref="observerPanelRef"
      class="bt-task-system"
      :class="{
        'bt-task-system--open': observerOpen,
        'bt-task-system--drawer': !isInlineTaskSystem,
      }"
      :role="isInlineTaskSystem ? undefined : 'dialog'"
      :aria-modal="isInlineTaskSystem ? undefined : 'true'"
      :aria-labelledby="taskSystemTitleId"
      :aria-describedby="taskSystemDescId"
      :aria-hidden="!isInlineTaskSystem && !observerOpen ? 'true' : undefined"
      :inert="!isInlineTaskSystem && !observerOpen"
      :tabindex="isInlineTaskSystem ? undefined : -1"
      @keydown="$emit('keydown', $event)"
  >
      <section class="bt-task-system__panel">
        <header class="bt-task-system__head">
          <div class="bt-task-system__head-copy">
            <h3 :id="taskSystemTitleId">{{ t('browserTask.taskSystem.title') }}</h3>
          </div>

          <button
            v-if="!isInlineTaskSystem"
            ref="observerCloseButtonRef"
            type="button"
            class="bt-task-system__close"
            :aria-label="t('browserTask.actions.closeDrawer')"
            @click="$emit('close')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </header>

        <section class="bt-task-card">
          <template v-if="sessionLocked">
            <div class="bt-task-facts">
              <article v-for="item in lockedSetupFacts" :key="item.label" class="bt-task-fact">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
            <p class="bt-task-system__hint">{{ t('browserTask.sections.session.reconfigureHint') }}</p>
          </template>
          <template v-else>
            <label class="bt-task-field">
              <span class="bt-task-field__label">{{ t('browserTask.fields.modelLabel') }}</span>
              <n-select
                :id="modelFieldId"
                v-model:value="model"
                ref="modelSelectRef"
                class="bt-task-select"
                :options="modelOptions"
              />
            </label>

            <AutoReverseCapabilityGroup
              :label="t('browserTask.fields.skillsLabel')"
              :count="selectedSkillsCount"
              :total="bootstrap.skills.length"
              :hint="bootstrap.skillsEnabled ? t('browserTask.fields.skillsHint') : t('browserTask.fields.skillsDisabledHint')"
              :items="skillItems"
              :empty-text="bootstrap.skillsEnabled ? t('browserTask.empty.noSkills') : t('browserTask.empty.skillsDisabled')"
              :default-open="false"
              :soft="true"
              variant="assistant"
              @toggle="(value, checked) => $emit('toggle-skill', value, checked)"
            />
          </template>
        </section>
      </section>
  </aside>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { NSelect } from 'naive-ui';

import AutoReverseCapabilityGroup, { type AutoReverseCapabilityItem } from '@/components/auto-reverse/AutoReverseCapabilityGroup.vue';
import { useLocale } from '@/composables/useLocale';
import type { FactItem, BootstrapPayload } from './types';

const model = defineModel<string>({ required: true });

const props = defineProps<{
  observerOpen: boolean;
  isInlineTaskSystem: boolean;
  taskSystemPanelId: string;
  taskSystemTitleId: string;
  taskSystemDescId: string;
  modelFieldId: string;
  modelHintId: string;
  taskSystemFacts: FactItem[];
  quickPrompts: string[];
  sessionLocked: boolean;
  lockedSetupFacts: FactItem[];
  bootstrap: BootstrapPayload;
  skillItems: AutoReverseCapabilityItem[];
  selectedSkillsCount: number;
}>();

defineEmits<{
  close: [];
  'apply-prompt': [prompt: string];
  'toggle-skill': [value: string, checked: boolean];
  keydown: [event: KeyboardEvent];
}>();

const observerPanelRef = ref<HTMLElement | null>(null);
const observerCloseButtonRef = ref<HTMLButtonElement | null>(null);
const modelSelectRef = ref<InstanceType<typeof NSelect> | null>(null);

const modelOptions = computed(() =>
  props.bootstrap.modelProfiles.map((profile) => ({
    label: profile.label,
    value: profile.key,
  })),
);

defineExpose({
  observerPanelRef,
  observerCloseButtonRef,
  modelSelectRef,
});

const { t } = useLocale();
</script>

<style scoped>
.bt-task-system {
  min-width: 0;
}

.bt-task-system__panel {
  display: grid;
  gap: 12px;
  overscroll-behavior: contain;
  padding: 14px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-shadow);
}

.bt-task-system__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.bt-task-system__head-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.bt-task-system__head h3 {
  margin: 0;
  font-size: 1rem;
}

.bt-task-system__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-muted);
  cursor: pointer;
  font: inherit;
  padding: 0;
  transition: all var(--transition-base);
}

.bt-task-system__close:hover {
  border-color: var(--panel-border-strong);
  color: var(--danger-500);
  background: color-mix(in srgb, var(--danger-500) 8%, transparent);
}

.bt-task-system__hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.84rem;
  line-height: 1.5;
}

.bt-task-card {
  display: grid;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  transition: border-color var(--transition-base);
}

.bt-task-card:hover {
  border-color: var(--panel-border-strong);
}

.bt-task-card h4 {
  margin: 0;
  font-size: 0.9rem;
}

.bt-task-facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(140px, 100%), 1fr));
  gap: 8px;
}

.bt-task-fact {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-task-fact span {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bt-task-fact strong {
  margin: 0;
  font-size: 0.84rem;
  word-break: break-all;
}

.bt-task-field {
  display: grid;
  gap: 6px;
}

.bt-task-field__label {
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 600;
}

.bt-task-select :deep(.n-base-selection) {
  border-radius: 14px;
}

@media (min-width: 1280px) {
  .bt-task-system__panel {
    position: sticky;
    top: calc(var(--layout-header-height) + 14px);
  }
}

.bt-task-system--drawer {
  position: fixed;
  top: calc(var(--layout-header-height) + 12px);
  left: 50%;
  right: auto;
  bottom: max(12px, env(safe-area-inset-bottom, 0px));
  z-index: 1002;
  width: min(380px, calc(100vw - 24px));
  transform: translate3d(calc(-50% + 44px), 0, 0);
  opacity: 0;
  pointer-events: none;
  transition:
    transform var(--transition-slow),
    opacity var(--transition-fast);
}

.bt-task-system--drawer.bt-task-system--open {
  transform: translate3d(-50%, 0, 0);
  opacity: 1;
  pointer-events: auto;
}

.bt-task-system--drawer .bt-task-system__panel {
  box-sizing: border-box;
  width: 100%;
  max-height: 100%;
  overflow: auto;
  border-radius: 18px;
  box-shadow: var(--panel-shadow-strong);
}

@media (max-width: 767px) {
  .bt-task-system--drawer {
    top: calc(var(--layout-header-height) + 10px);
    left: 50%;
    right: auto;
    bottom: max(10px, env(safe-area-inset-bottom, 0px));
    width: min(360px, calc(100vw - 20px));
    transform: translate3d(calc(-50% + 34px), 0, 0);
  }

  .bt-task-system--drawer.bt-task-system--open {
    transform: translate3d(-50%, 0, 0);
  }

  .bt-task-system__panel {
    border-radius: 14px;
    padding: 12px;
  }

  .bt-task-card {
    border-radius: 12px;
    padding: 10px 12px;
  }

  .bt-task-system__close {
    width: 34px;
    height: 34px;
  }
}

@media (max-width: 640px) {
  .bt-task-system__head {
    gap: 10px;
  }
}
</style>
