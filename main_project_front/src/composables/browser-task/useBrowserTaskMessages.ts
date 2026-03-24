import { ref } from 'vue';

import type { BrowserTaskMessage } from '@/views/api';
import { extractUrls, summarizeText, truncateUrl } from '@/components/browser-task/utils';

export function useBrowserTaskMessages(t: (key: string, params?: Record<string, unknown>) => string) {
  const messages = ref<BrowserTaskMessage[]>([]);
  const expandedMessageIds = ref<string[]>([]);
  const copiedMessageId = ref('');
  let copiedMessageTimer: number | null = null;

  function upsertMessage(next: BrowserTaskMessage): void {
    const index = messages.value.findIndex((item) => item.id === next.id);
    if (index === -1) {
      messages.value = [...messages.value, next];
      return;
    }
    const current = messages.value[index]!;
    const merged: BrowserTaskMessage = {
      ...current,
      ...next,
      content: next.content || current.content,
    };
    messages.value.splice(index, 1, merged);
    messages.value = [...messages.value];
  }

  function isMessageExpanded(messageId: string): boolean {
    return expandedMessageIds.value.includes(messageId);
  }

  function toggleMessageExpanded(messageId: string): void {
    if (isMessageExpanded(messageId)) {
      expandedMessageIds.value = expandedMessageIds.value.filter((item) => item !== messageId);
      return;
    }
    expandedMessageIds.value = [...expandedMessageIds.value, messageId];
  }

  function canExpandMessage(message: BrowserTaskMessage): boolean {
    if (message.role !== 'assistant') {
      return false;
    }
    const urls = extractUrls(message.content);
    return urls.some((item) => item.length > 80) || message.content.length > 320;
  }

  function canCopyMessageLink(message: BrowserTaskMessage): boolean {
    return message.role === 'assistant' && extractUrls(message.content).length > 0;
  }

  function shouldShowMessageActions(message: BrowserTaskMessage): boolean {
    return canExpandMessage(message) || canCopyMessageLink(message);
  }

  function getMessageDisplayContent(message: BrowserTaskMessage): string {
    const content = message.content || '';
    if (!content) {
      return '';
    }
    if (message.role !== 'assistant' || isMessageExpanded(message.id) || !canExpandMessage(message)) {
      return content;
    }
    const compacted = content.replace(/https?:\/\/[^\s<>"']+/gi, (url) => truncateUrl(url));
    return summarizeText(compacted, 360);
  }

  async function copyMessagePrimaryUrl(message: BrowserTaskMessage): Promise<void> {
    const primaryUrl = extractUrls(message.content)[0];
    if (!primaryUrl || !navigator.clipboard?.writeText) {
      return;
    }
    try {
      await navigator.clipboard.writeText(primaryUrl);
      copiedMessageId.value = message.id;
      if (copiedMessageTimer !== null) {
        window.clearTimeout(copiedMessageTimer);
      }
      copiedMessageTimer = window.setTimeout(() => {
        copiedMessageId.value = '';
        copiedMessageTimer = null;
      }, 1800);
    } catch {
      copiedMessageId.value = '';
    }
  }

  function getMessageToneClass(message: BrowserTaskMessage): string {
    if (message.role === 'user') {
      return 'browser-task-message--user';
    }
    if (message.status === 'error') {
      return 'browser-task-message--error';
    }
    if (message.status === 'streaming') {
      return 'browser-task-message--streaming';
    }
    if (message.status === 'stopped') {
      return 'browser-task-message--stopped';
    }
    if (message.status === 'done') {
      return 'browser-task-message--done';
    }
    if (message.role === 'system') {
      return 'browser-task-message--system';
    }
    return 'browser-task-message--assistant';
  }

  function formatMessageRole(role: string): string {
    const normalized = role.trim().toLowerCase();
    if (normalized === 'user') return t('browserTask.chat.roles.user');
    if (normalized === 'assistant') return t('browserTask.chat.roles.assistant');
    return t('browserTask.chat.roles.system');
  }

  function formatMessageStatus(status: string): string {
    const normalized = status.trim().toLowerCase();
    if (normalized === 'streaming') return t('browserTask.chat.status.streaming');
    if (normalized === 'stopped') return t('browserTask.chat.status.stopped');
    if (normalized === 'error') return t('browserTask.chat.status.error');
    return t('browserTask.chat.status.done');
  }

  function resetMessages(): void {
    messages.value = [];
    expandedMessageIds.value = [];
    copiedMessageId.value = '';
    if (copiedMessageTimer !== null) {
      window.clearTimeout(copiedMessageTimer);
      copiedMessageTimer = null;
    }
  }

  function clearCopiedTimer(): void {
    if (copiedMessageTimer !== null) {
      window.clearTimeout(copiedMessageTimer);
      copiedMessageTimer = null;
    }
  }

  return {
    messages,
    expandedMessageIds,
    copiedMessageId,
    upsertMessage,
    isMessageExpanded,
    toggleMessageExpanded,
    canExpandMessage,
    canCopyMessageLink,
    shouldShowMessageActions,
    getMessageDisplayContent,
    copyMessagePrimaryUrl,
    getMessageToneClass,
    formatMessageRole,
    formatMessageStatus,
    resetMessages,
    clearCopiedTimer,
  };
}

export type BrowserTaskMessagesApi = ReturnType<typeof useBrowserTaskMessages>;
