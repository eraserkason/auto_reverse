<template>
  <section class="browser-task-stage-card browser-task-chat-shell">
    <p class="sr-only">{{ chatAssistiveHint }}</p>

    <div v-if="showLiveStrip" class="browser-task-chat-shell__context">
      <div
        class="browser-task-live-strip"
        :class="`browser-task-live-strip--${liveStripTone}`"
      >
        <div class="browser-task-live-strip__main">
          <span class="browser-task-live-strip__dot" aria-hidden="true"></span>
          <strong>{{ liveStripTitle }}</strong>
        </div>
      </div>
    </div>

    <div class="browser-task-chat-shell__timeline">
      <template v-if="messages.length > 0">
        <article
          v-for="message in messages"
          :key="message.id"
          class="browser-task-message"
          :class="getMessageToneClass(message)"
        >
          <div class="browser-task-message__inner">
            <div class="browser-task-message__meta">
              <span class="browser-task-message__role">{{ formatMessageRole(message.role) }}</span>
              <span class="browser-task-message__meta-tail">
                <span class="browser-task-message__status" :class="`browser-task-message__status--${message.status}`">
                  {{ formatMessageStatus(message.status) }}
                </span>
                <span>{{ formatTimelineTime(message.createdAt) }}</span>
              </span>
            </div>

            <div class="browser-task-message__bubble">
              <p v-if="getMessageDisplayContent(message)" class="browser-task-message__content">
                {{ getMessageDisplayContent(message) }}
              </p>
              <div
                v-else-if="message.status === 'streaming'"
                class="browser-task-message__typing"
                :aria-label="t('browserTask.chat.streamingPlaceholder')"
              >
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p v-else class="browser-task-message__content">{{ t('common.misc.empty') }}</p>

              <div v-if="shouldShowMessageActions(message)" class="browser-task-message__actions">
                <n-button
                  v-if="canExpandMessage(message)"
                  tertiary
                  size="small"
                  class="browser-task-message__action"
                  :aria-label="isMessageExpanded(message.id) ? t('browserTask.message.collapse') : t('browserTask.message.expand')"
                  @click="$emit('toggle-expand', message.id)"
                >
                  {{ isMessageExpanded(message.id) ? t('browserTask.message.collapse') : t('browserTask.message.expand') }}
                </n-button>
                <n-button
                  v-if="canCopyMessageLink(message)"
                  tertiary
                  size="small"
                  class="browser-task-message__action"
                  :aria-label="t('browserTask.message.copyLinkAria')"
                  @click="$emit('copy-link', message)"
                >
                  {{ copiedMessageId === message.id ? t('browserTask.message.copied') : t('browserTask.message.copyLink') }}
                </n-button>
              </div>
            </div>
          </div>
        </article>
      </template>
      <div v-else class="browser-task-empty">
        <p class="browser-task-empty__hint">{{ emptyStateCopy }}</p>
      </div>
    </div>

    <slot name="inline-activity" />
  </section>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui';

import { useLocale } from '@/composables/useLocale';

import type { BrowserTaskMessage, FactItem } from './types';

defineProps<{
  messages: BrowserTaskMessage[];
  showLiveStrip: boolean;
  liveStripTone: string;
  liveStripTitle: string;
  liveStripLabel: string;
  chatAssistiveHint: string;
  emptyStateTitle: string;
  emptyStateCopy: string;
  emptyStateFacts: FactItem[];
  quickPrompts: string[];
  expandedMessageIds: string[];
  copiedMessageId: string;
  getMessageToneClass: (message: BrowserTaskMessage) => string;
  formatMessageRole: (role: string) => string;
  formatMessageStatus: (status: string) => string;
  formatTimelineTime: (value: string) => string;
  getMessageDisplayContent: (message: BrowserTaskMessage) => string;
  shouldShowMessageActions: (message: BrowserTaskMessage) => boolean;
  canExpandMessage: (message: BrowserTaskMessage) => boolean;
  canCopyMessageLink: (message: BrowserTaskMessage) => boolean;
  isMessageExpanded: (messageId: string) => boolean;
}>();

defineEmits<{
  'toggle-expand': [messageId: string];
  'copy-link': [message: BrowserTaskMessage];
  'apply-prompt': [prompt: string];
}>();

const { t } = useLocale();
</script>

<style scoped>
.browser-task-chat-shell {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: clamp(480px, 60vh, 660px);
  padding: 16px;
  border-radius: 22px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--panel-shadow);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.browser-task-chat-shell:hover {
  border-color: var(--panel-border-strong);
}

.browser-task-stage-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.browser-task-chat-shell__copy {
  display: grid;
  gap: 4px;
}

.browser-task-chat-shell__copy h4 {
  margin: 0;
}

.browser-task-chat-shell__desc {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.browser-task-chat-shell__context {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.browser-task-live-strip {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  box-shadow: var(--shadow-xs);
}

.browser-task-live-strip__main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.browser-task-live-strip__main strong,
.browser-task-empty strong,
.browser-task-empty p,
.browser-task-message__content {
  margin: 0;
}

.browser-task-live-strip__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 0 6px currentColor;
  opacity: 0.18;
}

.browser-task-live-strip--accent {
  color: var(--accent-400);
  border-color: rgba(var(--accent-rgb), 0.24);
  background: color-mix(in srgb, rgba(var(--accent-rgb), 0.16) 72%, var(--bg-surface));
}

.browser-task-live-strip--success {
  color: var(--bt-success);
  border-color: rgba(15, 118, 110, 0.16);
  background: color-mix(in srgb, rgba(22, 163, 74, 0.16) 72%, var(--bg-surface));
}

.browser-task-live-strip--warning {
  color: var(--bt-warning);
  border-color: rgba(180, 83, 9, 0.16);
  background: color-mix(in srgb, rgba(217, 119, 6, 0.16) 72%, var(--bg-surface));
}

.browser-task-live-strip--danger {
  color: var(--bt-danger);
  border-color: rgba(180, 35, 24, 0.16);
  background: color-mix(in srgb, rgba(220, 38, 38, 0.16) 72%, var(--bg-surface));
}

.browser-task-live-strip--neutral {
  color: var(--text-secondary);
}

.browser-task-chat-shell__timeline {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 4px 4px 26px;
  display: grid;
  gap: 12px;
  align-content: start;
  scrollbar-gutter: stable;
}

.browser-task-message {
  display: flex;
  width: 100%;
}

.browser-task-message--user {
  justify-content: flex-end;
}

.browser-task-message--assistant,
.browser-task-message--system,
.browser-task-message--error,
.browser-task-message--streaming,
.browser-task-message--done,
.browser-task-message--stopped {
  justify-content: flex-start;
}

.browser-task-message__inner {
  width: min(100%, 840px);
  display: grid;
  gap: 8px;
}

.browser-task-message--user .browser-task-message__inner {
  width: min(82%, 700px);
}

.browser-task-message__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-inline: 2px;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.browser-task-message__meta-tail {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.browser-task-message__role {
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.browser-task-message__bubble {
  position: relative;
  display: grid;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color var(--transition-base);
}

.browser-task-message__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.browser-task-message__action {
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-secondary);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  box-shadow: none;
  cursor: pointer;
  transition:
    border-color 200ms ease,
    background-color 200ms ease,
    color 200ms ease,
    transform 200ms ease;
}

.browser-task-message__action:hover {
  border-color: rgba(var(--accent-rgb), 0.24);
  background: rgba(var(--accent-rgb), 0.16);
  color: var(--accent-500);
  transform: translateY(-1px);
}

.browser-task-message--user .browser-task-message__bubble {
  border-color: transparent;
  background: linear-gradient(135deg, var(--accent-500), color-mix(in srgb, var(--accent-500) 80%, #6366f1));
  color: #fff;
  box-shadow: 0 4px 16px rgba(var(--accent-rgb), 0.2);
}

.browser-task-message--assistant .browser-task-message__bubble,
.browser-task-message--streaming .browser-task-message__bubble,
.browser-task-message--done .browser-task-message__bubble {
  background: var(--panel-bg);
}

.browser-task-message--stopped .browser-task-message__bubble {
  border-color: rgba(180, 83, 9, 0.22);
  background: rgba(180, 83, 9, 0.14);
}

.browser-task-message--error .browser-task-message__bubble {
  border-color: rgba(180, 35, 24, 0.22);
  background: rgba(185, 28, 28, 0.14);
}

.browser-task-message__status {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  border: 1px solid var(--border-soft);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.browser-task-message__status--streaming {
  color: #f0cf98;
  background: rgba(var(--accent-rgb), 0.16);
}

.browser-task-message__status--stopped {
  color: var(--bt-warning);
  background: rgba(180, 83, 9, 0.14);
}

.browser-task-message__status--error {
  color: var(--bt-danger);
  background: rgba(185, 28, 28, 0.14);
}

.browser-task-message__content {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  font: inherit;
  color: var(--text-primary);
  line-height: 1.76;
}

.browser-task-message__typing {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.browser-task-message__typing span {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.72);
  animation: browser-task-dot-pulse 1.1s ease-in-out infinite;
}

.browser-task-message__typing span:nth-child(2) {
  animation-delay: 120ms;
}

.browser-task-message__typing span:nth-child(3) {
  animation-delay: 240ms;
}

.browser-task-empty {
  display: grid;
  place-items: center;
  min-height: 160px;
  padding: 24px;
}

.browser-task-empty__hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.6;
  text-align: center;
  max-width: 48ch;
}

@keyframes browser-task-dot-pulse {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .browser-task-message__typing span {
    animation: none;
  }
}

@media (max-width: 767px) {
  .browser-task-chat-shell {
    border-radius: 14px;
    padding: 12px;
    min-height: clamp(240px, 42vh, 420px);
  }

  .browser-task-chat-shell__timeline {
    padding: 4px 2px 16px;
  }

  .browser-task-message--user .browser-task-message__inner {
    width: min(90%, 700px);
  }
}

@media (max-width: 640px) {
  .browser-task-chat-shell {
    min-height: 0;
  }

  .browser-task-empty {
    min-height: 112px;
    padding: 18px 12px;
  }

  .browser-task-empty__facts {
    grid-template-columns: 1fr;
  }
}
</style>
