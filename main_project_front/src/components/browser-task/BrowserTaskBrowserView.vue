<template>
  <section class="bt-browser">
    <header class="bt-browser__head">
      <div class="bt-browser__title-group">
        <span class="bt-browser__eyebrow">{{ t('browserTask.status.eyebrow') }}</span>
        <h3>{{ sessionState ? t('browserTask.sections.state.title') : t('browserTask.sections.session.title') }}</h3>
      </div>
      <div class="bt-browser__badges">
        <span class="bt-browser__badge">{{ connectionLabel }}</span>
        <span class="bt-browser__badge bt-browser__badge--mono">{{ modelLabel }}</span>
      </div>
    </header>

    <div class="bt-browser__chrome">
      <div class="bt-browser__chrome-bar">
        <div class="bt-browser__chrome-dots">
          <span></span><span></span><span></span>
        </div>
        <div class="bt-browser__address-input">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <span>{{ activeSessionUrl || t('browserTask.stage.addressPlaceholder') }}</span>
        </div>
      </div>

      <div
        class="bt-browser__viewport"
        :class="{
          'bt-browser__viewport--idle': !sessionState,
          'bt-browser__viewport--running': isBusy,
        }"
      >
        <template v-if="!sessionState">
          <div class="bt-browser__launchpad">
            <div class="bt-browser__launchpad-copy">
              <strong>{{ t('browserTask.sections.chat.emptySetupTitle') }}</strong>
              <p>{{ t('browserTask.sections.chat.emptySetupCopy') }}</p>
            </div>

            <div class="bt-browser__launchpad-steps">
              <article v-for="(step, i) in stageSteps" :key="step.title" class="bt-browser__step">
                <span class="bt-browser__step-num">{{ i + 1 }}</span>
                <div class="bt-browser__step-body">
                  <strong>{{ step.title }}</strong>
                  <p>{{ step.copy }}</p>
                </div>
              </article>
            </div>

            <div class="bt-browser__launchpad-prompts">
              <button
                v-for="prompt in quickPrompts"
                :key="prompt"
                type="button"
                class="bt-browser__prompt-btn"
                @click="$emit('apply-prompt', prompt)"
              >
                {{ prompt }}
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="bt-browser__facts">
            <article v-for="item in browserStageFacts" :key="item.label" class="bt-browser__fact">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>

          <div class="bt-browser__preview">
            <div class="bt-browser__preview-head">
              <strong>{{ browserStageTitle || browserPreviewTitle }}</strong>
              <p>{{ browserPreviewCopy }}</p>
            </div>

            <div v-if="latestAssistantExcerpt" class="bt-browser__excerpt">
              <span>{{ t('browserTask.stage.responseLabel') }}</span>
              <p>{{ latestAssistantExcerpt }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useLocale } from '@/composables/useLocale';
import type { StageStep, FactItem } from './types';

defineProps<{
  sessionState: unknown;
  isBusy: boolean;
  activeSessionUrl: string;
  browserStageTitle: string;
  browserStageCopy: string;
  browserPreviewTitle: string;
  browserPreviewCopy: string;
  latestAssistantExcerpt: string;
  stageSteps: StageStep[];
  browserStageFacts: FactItem[];
  quickPrompts: string[];
  connectionLabel: string;
  modelLabel: string;
}>();

defineEmits<{
  'apply-prompt': [prompt: string];
}>();

const { t } = useLocale();
</script>

<style scoped>
.bt-browser {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-shadow);
  transition: border-color var(--transition-base);
}

.bt-browser:hover {
  border-color: var(--panel-border-strong);
}

.bt-browser__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.bt-browser__title-group {
  display: grid;
  gap: 4px;
}

.bt-browser__eyebrow {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.bt-browser__title-group h3 {
  margin: 0;
  font-size: 1rem;
}

.bt-browser__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.bt-browser__badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-soft);
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.bt-browser__badge--mono {
  font-family: var(--font-mono);
}

.bt-browser__chrome {
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  overflow: hidden;
}

.bt-browser__chrome-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-browser__chrome-dots {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.bt-browser__chrome-dots span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--text-muted) 24%, transparent);
}

.bt-browser__chrome-dots span:first-child {
  background: color-mix(in srgb, var(--danger-500) 50%, transparent);
}

.bt-browser__chrome-dots span:nth-child(2) {
  background: color-mix(in srgb, var(--warning-500) 50%, transparent);
}

.bt-browser__chrome-dots span:nth-child(3) {
  background: color-mix(in srgb, var(--success-500) 50%, transparent);
}

.bt-browser__address-input {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border-radius: 8px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--panel-border);
  color: var(--text-muted);
  font-size: 0.78rem;
  min-width: 0;
}

.bt-browser__address-input span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bt-browser__viewport {
  padding: 14px;
  display: grid;
  gap: 12px;
  min-height: 120px;
}

.bt-browser__viewport--running {
  box-shadow: inset 0 0 0 2px rgba(var(--accent-rgb), 0.2);
}

.bt-browser__launchpad {
  display: grid;
  gap: 14px;
}

.bt-browser__launchpad-copy {
  display: grid;
  gap: 6px;
}

.bt-browser__launchpad-copy strong,
.bt-browser__launchpad-copy p {
  margin: 0;
}

.bt-browser__launchpad-copy p {
  color: var(--text-muted);
  font-size: 0.86rem;
  line-height: 1.55;
}

.bt-browser__launchpad-steps {
  display: grid;
  gap: 8px;
}

.bt-browser__step {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-browser__step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  background: var(--bg-accent-soft);
  color: var(--accent-500);
  font-size: 0.72rem;
  font-weight: 800;
}

.bt-browser__step-body {
  display: grid;
  gap: 2px;
}

.bt-browser__step-body strong {
  margin: 0;
  font-size: 0.84rem;
}

.bt-browser__step-body p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.45;
}

.bt-browser__launchpad-prompts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr));
  gap: 8px;
}

.bt-browser__prompt-btn {
  min-height: 40px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  color: var(--text-primary);
  font: inherit;
  font-size: 0.82rem;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-base);
}

.bt-browser__prompt-btn:hover {
  border-color: rgba(var(--accent-rgb), 0.28);
  background: var(--bg-accent-soft);
  transform: translateY(-1px);
}

.bt-browser__facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.bt-browser__fact {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-browser__fact span {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bt-browser__fact strong {
  margin: 0;
  font-size: 0.86rem;
}

.bt-browser__preview {
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--border-soft);
  background: var(--bg-surface-muted);
}

.bt-browser__preview-head {
  display: grid;
  gap: 6px;
}

.bt-browser__preview-head strong,
.bt-browser__preview-head p {
  margin: 0;
}

.bt-browser__preview-head p {
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.bt-browser__excerpt {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  background: rgba(var(--accent-rgb), 0.08);
}

.bt-browser__excerpt span {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bt-browser__excerpt p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

@media (max-width: 640px) {
  .bt-browser {
    padding: 12px;
  }

  .bt-browser__viewport {
    padding: 12px;
  }

  .bt-browser__facts {
    grid-template-columns: 1fr;
  }

  .bt-browser__launchpad-prompts {
    grid-template-columns: 1fr;
  }
}
</style>
