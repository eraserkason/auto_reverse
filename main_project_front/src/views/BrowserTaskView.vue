<template>
  <section class="browser-task-view">
    <div class="browser-task-view__ambient" aria-hidden="true">
      <span class="browser-task-view__orb browser-task-view__orb--one"></span>
      <span class="browser-task-view__orb browser-task-view__orb--two"></span>
      <span class="browser-task-view__grid"></span>
    </div>

    <BrowserTaskSkeleton v-if="session.loadingBootstrap.value && !session.sessionState.value" />

    <template v-else>
      <BrowserTaskTopbar
        ref="topbarRef"
        :loading-bootstrap="session.loadingBootstrap.value"
        :creating-session="session.creatingSession.value"
        :observer-open="observer.observerOpen.value"
        :is-inline-task-system="observer.isInlineTaskSystem.value"
        :status-badge-class="ui.statusBadgeClass.value"
        :session-status-label="ui.sessionStatusLabel.value"
        :observer-toggle-label="ui.observerToggleLabel.value"
        :task-system-panel-id="taskSystemPanelId"
        @reload="session.reloadBootstrap"
        @toggle-observer="observer.toggleObserverPanel"
        @new-session="session.createFreshSession"
      />

      <p class="sr-only" aria-live="polite" aria-atomic="true">{{ ui.liveRegionMessage.value }}</p>
      <p
        v-if="session.errorMessage.value"
        :id="errorMessageId"
        class="status-text status-text--danger browser-task-error"
        role="alert"
        aria-live="assertive"
      >
        {{ session.errorMessage.value }}
      </p>

      <section class="browser-task-workspace motion-enter-soft">
        <section class="browser-task-stage">
          <BrowserTaskChatShell
            :messages="msgApi.messages.value"
            :show-live-strip="ui.showLiveStrip.value"
            :live-strip-tone="ui.liveStripTone.value"
            :live-strip-title="ui.liveStripTitle.value"
            :live-strip-label="ui.liveStripLabel.value"
            :chat-assistive-hint="ui.chatAssistiveHint.value"
            :empty-state-title="ui.emptyStateTitle.value"
            :empty-state-copy="ui.emptyStateCopy.value"
            :empty-state-facts="ui.emptyStateFacts.value"
            :quick-prompts="ui.quickPrompts.value"
            :expanded-message-ids="msgApi.expandedMessageIds.value"
            :copied-message-id="msgApi.copiedMessageId.value"
            :get-message-tone-class="msgApi.getMessageToneClass"
            :format-message-role="msgApi.formatMessageRole"
            :format-message-status="msgApi.formatMessageStatus"
            :format-timeline-time="ui.formatTimelineTime"
            :get-message-display-content="msgApi.getMessageDisplayContent"
            :should-show-message-actions="msgApi.shouldShowMessageActions"
            :can-expand-message="msgApi.canExpandMessage"
            :can-copy-message-link="msgApi.canCopyMessageLink"
            :is-message-expanded="msgApi.isMessageExpanded"
            @toggle-expand="msgApi.toggleMessageExpanded"
            @copy-link="msgApi.copyMessagePrimaryUrl"
            @apply-prompt="(p) => session.applyPromptSuggestion(p, observer.observerOpen)"
          >
            <template #inline-activity>
              <div v-if="ui.toolChips.value.length > 0 || ui.agentTimelineItems.value.length > 0" class="browser-task-inline-activity">
                <BrowserTaskToolCalls
                  v-if="ui.toolChips.value.length > 0"
                  class="browser-task-inline-activity__tools"
                  :tool-chips="ui.toolChips.value"
                  :tool-feed-items="ui.toolFeedItems.value"
                  :selected-tool-filter="runtime.selectedToolFilter.value"
                  @filter="runtime.toggleToolFilter"
                />

                <BrowserTaskTimeline
                  v-if="ui.agentTimelineItems.value.length > 0"
                  ref="timelineComponentRef"
                  class="browser-task-inline-activity__timeline"
                  :agent-timeline-items="ui.agentTimelineItems.value"
                  @scroll="handleTimelineScroll"
                />
              </div>
            </template>
          </BrowserTaskChatShell>

          <BrowserTaskComposer
            v-model="session.draftMessage.value"
            :is-busy="ui.isBusy.value"
            :reset-session-disabled="!session.sessionState.value || session.sessionState.value?.status === 'closed'"
            :primary-action-disabled="ui.primaryActionDisabled.value"
            :primary-action-label="ui.primaryActionLabel.value"
            :composer-meta-hint="ui.composerMetaHint.value"
            :draft-character-count="ui.draftCharacterCount.value"
            :prompt-field-id="promptFieldId"
            :prompt-hint-id="promptHintId"
            :prompt-count-id="promptCountId"
            ref="composerRef"
            @insert-example="session.applyPromptExample(t('browserTask.fields.insertExampleText'))"
            @reset-session="session.resetSession"
            @primary-action="session.handlePrimaryAction"
            @submit="session.handlePrimaryAction"
          />
        </section>

      </section>

      <BrowserTaskTaskSystem
        ref="taskSystemRef"
        v-model="session.selectedModelProfileKey.value"
        :observer-open="observer.observerOpen.value"
        :is-inline-task-system="observer.isInlineTaskSystem.value"
        :task-system-panel-id="taskSystemPanelId"
        :task-system-title-id="taskSystemTitleId"
        :task-system-desc-id="taskSystemDescId"
        :model-field-id="modelFieldId"
        :model-hint-id="modelHintId"
        :task-system-facts="ui.taskSystemFacts.value"
        :quick-prompts="ui.quickPrompts.value"
        :session-locked="ui.sessionLocked.value"
        :locked-setup-facts="ui.lockedSetupFacts.value"
        :bootstrap="session.bootstrap"
        :skill-items="ui.skillItems.value"
        :selected-skills-count="session.selectedSkills.value.length"
        @close="observer.closeObserverPanel"
        @apply-prompt="(p) => session.applyPromptSuggestion(p, observer.observerOpen)"
        @toggle-skill="session.toggleSkill"
        @keydown="observer.handleObserverPanelKeydown"
      />

      <button
        v-if="observer.observerOpen.value && !observer.isInlineTaskSystem.value"
        type="button"
        class="browser-task-task-system__backdrop"
        aria-hidden="true"
        tabindex="-1"
        @click="observer.closeObserverPanel()"
      ></button>
    </template>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, watch, onMounted, onBeforeUnmount } from 'vue';

import BrowserTaskChatShell from '@/components/browser-task/BrowserTaskChatShell.vue';
import BrowserTaskComposer from '@/components/browser-task/BrowserTaskComposer.vue';
import BrowserTaskSkeleton from '@/components/browser-task/BrowserTaskSkeleton.vue';
import BrowserTaskTaskSystem from '@/components/browser-task/BrowserTaskTaskSystem.vue';
import BrowserTaskTimeline from '@/components/browser-task/BrowserTaskTimeline.vue';
import BrowserTaskTopbar from '@/components/browser-task/BrowserTaskTopbar.vue';
import BrowserTaskToolCalls from '@/components/browser-task/BrowserTaskToolCalls.vue';
import { useLocale } from '@/composables/useLocale';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { closeBrowserTaskSession } from '@/views/api';

import { useBrowserTaskRuntime } from '@/composables/browser-task/useBrowserTaskRuntime';
import { useBrowserTaskMessages } from '@/composables/browser-task/useBrowserTaskMessages';
import { useBrowserTaskStream } from '@/composables/browser-task/useBrowserTaskStream';
import { useBrowserTaskSession } from '@/composables/browser-task/useBrowserTaskSession';
import { useBrowserTaskObserver } from '@/composables/browser-task/useBrowserTaskObserver';
import { useBrowserTaskUI } from '@/composables/browser-task/useBrowserTaskUI';

/* ── locale ── */
const { t, formatDateTime } = useLocale();
const { bootstrapWorkspaceData } = useWorkspaceData();

/* ── DOM refs ── */
const topbarRef = ref<InstanceType<typeof BrowserTaskTopbar> | null>(null);
const timelineComponentRef = ref<InstanceType<typeof BrowserTaskTimeline> | null>(null);
const composerRef = ref<InstanceType<typeof BrowserTaskComposer> | null>(null);
const taskSystemRef = ref<InstanceType<typeof BrowserTaskTaskSystem> | null>(null);

/* ── static IDs ── */
const taskSystemPanelId = 'browser-task-task-system-panel';
const taskSystemTitleId = 'browser-task-task-system-title';
const taskSystemDescId = 'browser-task-task-system-desc';
const promptFieldId = 'browser-task-prompt';
const promptHintId = 'browser-task-prompt-hint';
const promptCountId = 'browser-task-prompt-count';
const modelFieldId = 'browser-task-model-profile';
const modelHintId = 'browser-task-model-hint';
const errorMessageId = 'browser-task-error-message';

/* ── observer composable first (provides focus helpers) ── */
const observer = useBrowserTaskObserver({
  topbarRef: topbarRef as Parameters<typeof useBrowserTaskObserver>[0]['topbarRef'],
  taskSystemRef: taskSystemRef as Parameters<typeof useBrowserTaskObserver>[0]['taskSystemRef'],
  composerRef: composerRef as Parameters<typeof useBrowserTaskObserver>[0]['composerRef'],
});

/* ── runtime + messages ── */
const runtime = useBrowserTaskRuntime();
const msgApi = useBrowserTaskMessages(t);

/* ── stream (needs runtime + messages + shared state) ── */
const _stoppingRunRef = ref(false);
const _errorMessageRef = ref('');
const _sessionStateRef = ref<import('@/views/api').BrowserTaskSessionState | null>(null);

const stream = useBrowserTaskStream({
  runtime,
  messages: msgApi,
  sessionState: _sessionStateRef,
  stoppingRun: _stoppingRunRef,
  errorMessage: _errorMessageRef,
  t,
});

/* ── session (orchestrates everything) ── */
const session = useBrowserTaskSession({
  runtime,
  messages: msgApi,
  stream,
  t,
  openObserverPanel: observer.openObserverPanel,
  closeObserverPanel: observer.closeObserverPanel,
  isInlineTaskSystem: observer.isInlineTaskSystem,
  focusPromptComposer: observer.focusPromptComposer,
  focusModelSelection: observer.focusModelSelection,
});

/* ── ui (all computed props) ── */
const ui = useBrowserTaskUI({
  runtime,
  messages: msgApi,
  stream,
  session,
  observer,
  t,
  formatDateTime,
});

/* ── timeline scroll helpers ── */
const shouldStickToBottom = ref(true);

function scrollTimelineToBottom(force = false): void {
  const element = (timelineComponentRef.value?.timelineRef as HTMLElement | null | undefined) ?? null;
  if (!element) return;
  if (!force && !shouldStickToBottom.value) return;
  element.scrollTop = element.scrollHeight;
}

function handleTimelineScroll(): void {
  const element = (timelineComponentRef.value?.timelineRef as HTMLElement | null | undefined) ?? null;
  if (!element) return;
  const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
  shouldStickToBottom.value = distance < 72;
}

/* ── watchers ── */
watch(ui.lastMessageFingerprint, async () => {
  await nextTick();
  scrollTimelineToBottom();
});

watch(
  () => ui.toolChips.value.map((item) => item.key).join('|'),
  (nextKeys) => {
    if (runtime.selectedToolFilter.value === 'all') return;
    if (!nextKeys.split('|').filter(Boolean).includes(runtime.selectedToolFilter.value)) {
      runtime.selectedToolFilter.value = 'all';
    }
  },
);

watch(observer.observerOpen, async (nextOpen) => {
  if (observer.isInlineTaskSystem.value) {
    observer.unlockObserverBodyScroll();
    return;
  }
  if (nextOpen) {
    observer.lockObserverBodyScroll();
    await nextTick();
    (taskSystemRef.value?.observerCloseButtonRef as HTMLButtonElement | null | undefined)?.focus();
    return;
  }
  observer.unlockObserverBodyScroll();
});

/* ── lifecycle ── */
onMounted(async () => {
  try {
    await bootstrapWorkspaceData();
  } catch {
    // Browser Task bootstrap keeps its own error surface; global preload failure should not block page mount.
  }
  await session.reloadBootstrap();
  observer.initMediaQuery();
  await nextTick();
  scrollTimelineToBottom(true);
});

onBeforeUnmount(() => {
  observer.unlockObserverBodyScroll();
  if (session.sessionState.value?.sessionId) {
    void closeBrowserTaskSession(session.sessionState.value.sessionId);
  }
  stream.closeStream();
  msgApi.clearCopiedTimer();
  observer.destroyMediaQuery();
});
</script>

<style scoped>
.browser-task-view {
  --bt-accent: var(--accent-500);
  --bt-accent-soft: rgba(var(--accent-rgb), 0.08);
  --bt-accent-border: rgba(var(--accent-rgb), 0.16);
  --bt-success: var(--success-500);
  --bt-warning: #c6841e;
  --bt-danger: #c2413c;
  --bt-chat-width: min(100%, 1360px);
  position: relative;
  display: grid;
  gap: 16px;
}

.browser-task-view__ambient {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  opacity: 0.24;
}

.browser-task-view__orb,
.browser-task-view__grid {
  position: absolute;
}

.browser-task-view__orb {
  border-radius: 999px;
  filter: blur(72px);
  opacity: 0.14;
}

.browser-task-view__orb--one {
  top: -10%;
  left: 8%;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(var(--accent-rgb), 0.12) 0%, transparent 78%);
}

.browser-task-view__orb--two {
  top: 8%;
  right: 4%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, color-mix(in srgb, var(--text-muted) 14%, transparent) 0%, transparent 76%);
}

.browser-task-view__grid {
  inset: 0;
  background-image:
    linear-gradient(color-mix(in srgb, var(--text-muted) 10%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--text-muted) 10%, transparent) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.34), transparent 76%);
}

.browser-task-error {
  position: relative;
  z-index: 1;
  width: var(--bt-chat-width);
  margin: 0 auto;
}

.browser-task-workspace {
  position: relative;
  z-index: 1;
  width: var(--bt-chat-width);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  align-items: start;
}

.browser-task-stage {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.browser-task-inline-activity {
  display: grid;
  gap: 10px;
  padding: 12px 0 0;
  border-top: 1px solid var(--panel-border);
}

.browser-task-inline-activity__tools :deep(.bt-tools-panel) {
  padding: 0;
  border: none;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.browser-task-inline-activity__tools :deep(.bt-tools-panel__head) {
  display: none;
}

.browser-task-inline-activity__timeline :deep(.bt-timeline-panel) {
  padding: 0;
  border: none;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
  max-height: 200px;
}

.browser-task-inline-activity__timeline :deep(.bt-timeline-panel__head) {
  display: none;
}

.browser-task-inline-activity__timeline :deep(.bt-timeline) {
  max-height: 180px;
}

.browser-task-task-system__backdrop {
  position: fixed;
  inset: 0;
  z-index: 1001;
  background: rgba(15, 23, 42, 0.22);
  border: 0;
  padding: 0;
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
}

/* activity is now inline in chat shell */

@media (max-width: 767px) {
  .browser-task-view {
    gap: 12px;
  }

  .browser-task-view__ambient {
    opacity: 0.22;
  }

  .browser-task-view__grid {
    display: none;
  }

  .browser-task-workspace {
    gap: 12px;
  }

  .browser-task-stage {
    gap: 12px;
  }

  .browser-task-stage__activity {
    gap: 10px;
  }
}
</style>
