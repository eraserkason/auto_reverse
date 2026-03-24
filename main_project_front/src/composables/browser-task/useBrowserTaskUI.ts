import { computed } from 'vue';

import type { AutoReverseCapabilityItem } from '@/components/auto-reverse/AutoReverseCapabilityGroup.vue';
import type { TimelineTone, ToolChipItem, AgentTimelineItem, ExecutionPhase } from '@/components/browser-task/types';
import { summarizeText } from '@/components/browser-task/utils';
import type { RuntimeEventStatus } from '@/components/browser-task/types';
import type { BrowserTaskRuntimeApi } from './useBrowserTaskRuntime';
import type { BrowserTaskMessagesApi } from './useBrowserTaskMessages';
import type { BrowserTaskStreamApi } from './useBrowserTaskStream';
import type { BrowserTaskSessionApi } from './useBrowserTaskSession';
import type { BrowserTaskObserverApi } from './useBrowserTaskObserver';

export interface BrowserTaskUIOptions {
  runtime: BrowserTaskRuntimeApi;
  messages: BrowserTaskMessagesApi;
  stream: BrowserTaskStreamApi;
  session: BrowserTaskSessionApi;
  observer: BrowserTaskObserverApi;
  t: (key: string, params?: Record<string, unknown>) => string;
  formatDateTime: (value: string, opts?: Intl.DateTimeFormatOptions) => string;
}

export function useBrowserTaskUI(opts: BrowserTaskUIOptions) {
  const { runtime, messages, stream, session, observer, t, formatDateTime } = opts;

  /* ── helpers ── */

  function formatSessionStatus(status?: string): string {
    if (!status) return t('browserTask.status.idle');
    return t(`browserTask.statusLabels.${status}`);
  }

  function formatRuntimeStatusLabel(status: RuntimeEventStatus): string {
    if (status === 'running') return t('common.status.running');
    if (status === 'completed') return t('common.status.completed');
    if (status === 'failed') return t('common.status.failed');
    if (status === 'stopped') return t('browserTask.chat.status.stopped');
    return t('browserTask.observer.phaseIdle');
  }

  function formatTimelineTime(value: string): string {
    return formatDateTime(value, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  function formatCompactValue(value: string | undefined, max = 40): string {
    if (!value) {
      return t('common.misc.empty');
    }
    return summarizeText(value, max);
  }

  function formatSkillPathLabel(value: string): string {
    const normalized = value.trim();
    if (!normalized) {
      return '';
    }
    const segments = normalized.split('/').filter(Boolean);
    return segments[segments.length - 1] ?? normalized;
  }

  /* ── core derived state ── */

  const isStopping = computed(() => session.stoppingRun.value || session.sessionState.value?.status === 'stopping');
  const isRunning = computed(() => {
    const status = session.sessionState.value?.status ?? '';
    return status === 'running' || status === 'bootstrapping';
  });
  const isBusy = computed(() => isRunning.value || isStopping.value);
  const isCreatingOrSending = computed(() => session.creatingSession.value || session.submittingMessage.value);
  const sessionLocked = computed(() => Boolean(session.sessionState.value && session.sessionState.value.status !== 'closed'));
  const selectedModelProfileLabel = computed(
    () => session.bootstrap.modelProfiles.find((item) => item.key === session.selectedModelProfileKey.value)?.label ?? t('common.misc.empty'),
  );
  const activeSessionUrl = computed(() => session.sessionState.value?.currentUrl || session.sessionState.value?.startUrl || '');

  /* ── skill items ── */

  const skillItems = computed<AutoReverseCapabilityItem[]>(() =>
    (session.bootstrap.skillsEnabled ? session.bootstrap.skills : []).map((item) => ({
      value: item,
      label: formatSkillPathLabel(item),
      meta: item,
      selected: session.selectedSkills.value.includes(item),
      tone: 'soft',
    })),
  );

  /* ── status / topbar ── */

  const statusBadgeClass = computed(() => {
    const status = session.sessionState.value?.status ?? '';
    if (status === 'ready') return 'soft-badge--success';
    if (status === 'running' || status === 'bootstrapping' || status === 'stopping') return 'soft-badge--warning';
    if (status === 'error') return 'soft-badge--danger';
    return '';
  });

  const sessionStatusLabel = computed(() => formatSessionStatus(session.sessionState.value?.status));

  const connectionLabel = computed(() =>
    stream.streamConnected.value ? t('browserTask.status.streamConnected') : t('browserTask.status.streamIdle'),
  );

  const topbarDescription = computed(() => {
    if (!session.sessionState.value) {
      return t('browserTask.sections.session.chatbotLead');
    }
    if (isStopping.value) {
      return t('browserTask.hints.stopping');
    }
    if (isRunning.value) {
      return t('browserTask.hints.running');
    }
    return t('browserTask.sections.chat.readyHint');
  });

  /* ── primary action ── */

  const primaryActionLabel = computed(() => {
    if (isStopping.value) {
      return t('browserTask.actions.stopLoading');
    }
    if (isRunning.value) {
      return t('browserTask.actions.stop');
    }
    return isCreatingOrSending.value ? t('browserTask.actions.sendLoading') : t('browserTask.actions.send');
  });

  const primaryActionDisabled = computed(() => {
    if (isBusy.value) {
      return !session.sessionState.value?.sessionId || isStopping.value;
    }
    return isCreatingOrSending.value || !session.draftMessage.value.trim() || !session.selectedModelProfileKey.value;
  });

  /* ── composer ── */

  const composerMetaHint = computed(() => {
    if (!session.selectedModelProfileKey.value) {
      return t('browserTask.hints.selectModel');
    }
    if (!session.sessionState.value) {
      return t('browserTask.hints.createSession');
    }
    if (isStopping.value) {
      return t('browserTask.hints.stopping');
    }
    if (isRunning.value) {
      return t('browserTask.hints.stopReady');
    }
    return `${t('browserTask.hints.ready')} | ${t('browserTask.sections.chat.enterHint')}`;
  });

  const draftCharacterCount = computed(() =>
    t('browserTask.fields.charCount', { count: session.draftMessage.value.trim().length }),
  );

  /* ── chat shell ── */

  const chatAssistiveHint = computed(() => {
    if (!session.sessionState.value) {
      return t('browserTask.sections.chat.preflightHint');
    }
    if (isStopping.value) {
      return t('browserTask.hints.stopping');
    }
    if (isRunning.value) {
      return t('browserTask.sections.chat.runningHint');
    }
    if (activeSessionUrl.value) {
      return t('browserTask.sections.chat.boundHint', { url: activeSessionUrl.value });
    }
    return t('browserTask.sections.chat.readyHint');
  });

  const lastRunEvent = computed(() => [...runtime.runtimeEvents.value].reverse().find((item) => item.kind === 'run') ?? null);
  const lastUserMessage = computed(() => [...messages.messages.value].reverse().find((item) => item.role === 'user') ?? null);
  const latestAssistantMessage = computed(() => [...messages.messages.value].reverse().find((item) => item.role === 'assistant') ?? null);

  const showLiveStrip = computed(() => Boolean(session.sessionState.value || lastRunEvent.value || isBusy.value));

  const liveStripTone = computed<TimelineTone>(() => {
    if (isStopping.value) return 'warning';
    if (isRunning.value) return 'accent';
    if (lastRunEvent.value?.status === 'failed') return 'danger';
    if (lastRunEvent.value?.status === 'completed') return 'success';
    return 'neutral';
  });

  const liveStripTitle = computed(() => {
    if (isStopping.value) return t('browserTask.actions.stopLoading');
    if (isRunning.value) return t('browserTask.activity.runStartedLabel');
    if (lastRunEvent.value?.status === 'failed') return t('browserTask.activity.runFailedLabel');
    if (lastRunEvent.value?.status === 'completed') return t('browserTask.activity.runCompletedLabel');
    return t('browserTask.sections.chat.title');
  });

  const liveStripLabel = computed(() => {
    const activeTool = [...runtime.runtimeEvents.value].reverse().find((item) => item.kind === 'tool' && item.status === 'running');
    if (isStopping.value) {
      return t('browserTask.hints.stopping');
    }
    if (activeTool?.toolName) {
      return `${t('browserTask.activity.toolStarted')} · ${activeTool.toolName}`;
    }
    if (isRunning.value) {
      return t('browserTask.sections.chat.runningHint');
    }
    if (lastRunEvent.value?.status === 'completed') {
      return t('browserTask.observer.liveStripCompleted');
    }
    if (lastRunEvent.value?.status === 'stopped') {
      return t('browserTask.observer.runStoppedDetail');
    }
    if (lastRunEvent.value?.summary) {
      return summarizeText(lastRunEvent.value.summary, 88);
    }
    if (session.sessionState.value) {
      return t('browserTask.sections.chat.readyHint');
    }
    return t('browserTask.sections.chat.createFirst');
  });

  const emptyStateTitle = computed(() =>
    session.sessionState.value ? t('browserTask.sections.chat.emptyReadyTitle') : t('browserTask.sections.chat.emptySetupTitle'),
  );
  const emptyStateCopy = computed(() =>
    session.sessionState.value ? t('browserTask.sections.chat.emptyReadyCopy') : t('browserTask.sections.chat.emptySetupCopy'),
  );
  const emptyStateFacts = computed(() => [
    { label: t('browserTask.fields.modelLabel'), value: selectedModelProfileLabel.value },
    { label: t('browserTask.fields.skillsLabel'), value: `${session.selectedSkills.value.length}/${session.bootstrap.skills.length}` },
    { label: t('browserTask.observer.phase.session'), value: session.sessionState.value ? sessionStatusLabel.value : t('browserTask.actions.newSession') },
  ]);

  const quickPrompts = computed(() => [
    t('browserTask.sections.chat.suggestions.summary'),
    t('browserTask.sections.chat.suggestions.login'),
    t('browserTask.sections.chat.suggestions.map'),
  ]);

  /* ── browser view ── */

  const latestAssistantExcerpt = computed(() => {
    const content = latestAssistantMessage.value?.content?.trim() ?? '';
    return content ? summarizeText(content.replace(/\s+/g, ' '), 180) : '';
  });

  const stageSteps = computed(() => [
    { title: t('browserTask.stage.steps.describeTitle'), copy: t('browserTask.stage.steps.describeCopy') },
    { title: t('browserTask.stage.steps.observeTitle'), copy: t('browserTask.stage.steps.observeCopy') },
    { title: t('browserTask.stage.steps.iterateTitle'), copy: t('browserTask.stage.steps.iterateCopy') },
  ]);

  const browserStageTitle = computed(() => {
    if (!session.sessionState.value) {
      return t('browserTask.stage.title');
    }
    return session.sessionState.value.pageTitle || activeSessionUrl.value || t('browserTask.stage.previewTitle');
  });

  const browserStageCopy = computed(() => {
    if (!session.sessionState.value) {
      return t('browserTask.stage.description');
    }
    if (isStopping.value) {
      return t('browserTask.hints.stopping');
    }
    if (isRunning.value) {
      return liveStripLabel.value;
    }
    return browserPreviewCopy.value;
  });

  const browserPreviewTitle = computed(() => {
    if (session.sessionState.value?.pageTitle) {
      return session.sessionState.value.pageTitle;
    }
    if (activeSessionUrl.value) {
      return activeSessionUrl.value;
    }
    return t('browserTask.stage.previewTitle');
  });

  const browserPreviewCopy = computed(() => {
    if (session.sessionState.value?.lastToolSummary) {
      return session.sessionState.value.lastToolSummary;
    }
    if (lastRunEvent.value?.summary) {
      return summarizeText(lastRunEvent.value.summary, 180);
    }
    return t('browserTask.stage.previewCopy');
  });

  const browserStageFacts = computed(() => [
    { label: t('browserTask.status.currentUrl'), value: formatCompactValue(activeSessionUrl.value, 56) },
    { label: t('browserTask.status.pageTitle'), value: formatCompactValue(session.sessionState.value?.pageTitle, 40) },
    { label: t('browserTask.status.lastTool'), value: formatCompactValue(session.sessionState.value?.lastToolName, 28) },
    { label: t('browserTask.observer.phase.run'), value: lastRunEvent.value ? formatRuntimeStatusLabel(lastRunEvent.value.status) : sessionStatusLabel.value },
  ]);

  /* ── timeline / tools ── */

  const focusRunId = computed(() => runtime.activeRunId.value ?? runtime.latestRunId.value);

  const toolChips = computed<ToolChipItem[]>(() => {
    const items = runtime.runtimeEvents.value.filter((item) => item.kind === 'tool' && (!focusRunId.value || item.runId === focusRunId.value));
    const summaryMap = new Map<string, ToolChipItem>();

    for (const item of items) {
      if (!item.toolName) {
        continue;
      }
      const current = summaryMap.get(item.toolName);
      const tone: TimelineTone = item.status === 'running' ? 'accent' : item.status === 'failed' ? 'danger' : item.status === 'stopped' ? 'warning' : 'success';
      if (!current) {
        summaryMap.set(item.toolName, {
          key: item.toolName,
          label: item.toolName,
          count: 1,
          active: runtime.selectedToolFilter.value === item.toolName,
          tone,
        });
        continue;
      }
      current.count += 1;
      current.active = runtime.selectedToolFilter.value === item.toolName;
      if (tone === 'accent' || (tone === 'danger' && current.tone !== 'accent')) {
        current.tone = tone;
      } else if (current.tone === 'success') {
        current.tone = tone;
      }
    }

    return Array.from(summaryMap.values()).sort((left, right) => {
      if (left.active !== right.active) {
        return left.active ? -1 : 1;
      }
      return right.count - left.count || left.label.localeCompare(right.label);
    });
  });

  const agentTimelineItems = computed<AgentTimelineItem[]>(() => {
    const messageItems: AgentTimelineItem[] = messages.messages.value.map((message) => ({
      id: `message-${message.id}`,
      title:
        message.role === 'assistant'
          ? t('browserTask.timeline.assistantTitle')
          : message.role === 'user'
            ? t('browserTask.timeline.userTitle')
            : t('browserTask.timeline.systemTitle'),
      summary: summarizeText((messages.getMessageDisplayContent(message) || message.content || '').replace(/\s+/g, ' '), 220),
      time: formatTimelineTime(message.createdAt),
      tone:
        message.role === 'assistant'
          ? message.status === 'error'
            ? 'danger'
            : message.status === 'stopped'
              ? 'warning'
              : 'success'
          : 'accent',
      createdAt: message.createdAt,
    }));

    const eventItems: AgentTimelineItem[] = runtime.runtimeEvents.value.map((item) => ({
      id: `event-${item.id}`,
      title: item.label,
      summary: summarizeText(item.summary, 220),
      time: formatTimelineTime(item.createdAt),
      tone: item.tone,
      createdAt: item.createdAt,
    }));

    return [...messageItems, ...eventItems]
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .slice(0, 12);
  });

  const toolFeedItems = computed(() =>
    [...runtime.runtimeEvents.value]
      .filter((item) => item.kind === 'tool')
      .filter((item) => runtime.selectedToolFilter.value === 'all' || item.toolName === runtime.selectedToolFilter.value)
      .reverse()
      .slice(0, 6)
      .map((item) => ({
        id: item.id,
        title: item.label,
        summary: summarizeText(item.summary, 160),
        time: formatTimelineTime(item.createdAt),
      })),
  );

  /* ── task system ── */

  const taskSystemFacts = computed(() => [
    { label: t('browserTask.taskSystem.currentTaskLabel'), value: lastUserMessage.value ? summarizeText(lastUserMessage.value.content, 72) : t('browserTask.taskSystem.noTask') },
    { label: t('browserTask.observer.phase.session'), value: session.sessionState.value ? sessionStatusLabel.value : t('browserTask.status.idle') },
    { label: t('browserTask.status.lastTool'), value: formatCompactValue(session.sessionState.value?.lastToolName, 32) },
  ]);

  const lockedSetupFacts = computed(() => [
    { label: t('browserTask.fields.modelLabel'), value: selectedModelProfileLabel.value },
    { label: t('browserTask.fields.skillsLabel'), value: `${session.selectedSkills.value.length}/${session.bootstrap.skills.length}` },
    { label: t('browserTask.observer.phase.session'), value: sessionStatusLabel.value },
  ]);

  const executionPhases = computed<ExecutionPhase[]>(() => {
    const latestAssistant = [...messages.messages.value].reverse().find((item) => item.role === 'assistant');
    const activeTool = [...runtime.runtimeEvents.value].reverse().find((item) => item.kind === 'tool' && item.status === 'running');
    const lastTool = [...runtime.runtimeEvents.value].reverse().find((item) => item.kind === 'tool');
    const runEvent = lastRunEvent.value;

    const sessionPhase: ExecutionPhase = !session.sessionState.value
      ? { key: 'session', label: t('browserTask.observer.phase.session'), value: t('browserTask.status.idle'), detail: t('browserTask.sections.chat.createFirst'), tone: 'neutral' }
      : { key: 'session', label: t('browserTask.observer.phase.session'), value: sessionStatusLabel.value, detail: session.sessionState.value.currentUrl || session.sessionState.value.sessionId || t('common.misc.empty'), tone: session.sessionState.value.status === 'error' ? 'danger' : stream.streamConnected.value ? 'success' : 'warning' };

    let runPhase: ExecutionPhase = { key: 'run', label: t('browserTask.observer.phase.run'), value: t('browserTask.status.idle'), detail: t('browserTask.observer.phaseIdle'), tone: 'neutral' };
    if (isStopping.value) {
      runPhase = { key: 'run', label: t('browserTask.observer.phase.run'), value: t('browserTask.statusLabels.stopping'), detail: t('browserTask.hints.stopping'), tone: 'warning' };
    } else if (isRunning.value) {
      runPhase = { key: 'run', label: t('browserTask.observer.phase.run'), value: t('browserTask.statusLabels.running'), detail: activeTool?.toolName || runEvent?.summary || t('browserTask.sections.chat.runningHint'), tone: 'accent' };
    } else if (runEvent) {
      runPhase = {
        key: 'run',
        label: t('browserTask.observer.phase.run'),
        value: formatRuntimeStatusLabel(runEvent.status),
        detail: runEvent.status === 'completed'
          ? lastTool?.toolName || t('browserTask.observer.runCompletedDetail')
          : runEvent.status === 'stopped'
            ? t('browserTask.observer.runStoppedDetail')
            : runEvent.summary || t('browserTask.observer.phaseIdle'),
        tone: runEvent.tone,
      };
    }

    const toolsPhase: ExecutionPhase = toolChips.value.length === 0
      ? { key: 'tools', label: t('browserTask.observer.phase.tools'), value: t('browserTask.observer.phaseIdle'), detail: t('browserTask.observer.toolsEmpty'), tone: 'neutral' }
      : { key: 'tools', label: t('browserTask.observer.phase.tools'), value: `${toolChips.value.length} ${t('browserTask.observer.toolsCountUnit')}`, detail: activeTool?.toolName || lastTool?.toolName || t('common.misc.empty'), tone: activeTool ? 'accent' : toolChips.value.some((item) => item.tone === 'danger') ? 'danger' : 'success' };

    let responseTone: TimelineTone = 'neutral';
    let responseValue = t('browserTask.observer.phaseIdle');
    let responseDetail = t('browserTask.observer.responseEmpty');
    if (latestAssistant) {
      responseValue = messages.formatMessageStatus(latestAssistant.status);
      if (latestAssistant.status === 'streaming') {
        responseDetail = t('browserTask.chat.streamingPlaceholder');
      } else if (latestAssistant.status === 'error') {
        responseDetail = t('browserTask.chat.status.error');
      } else {
        responseDetail = t('browserTask.observer.responseConversation');
      }
      if (latestAssistant.status === 'streaming') {
        responseTone = 'accent';
      } else if (latestAssistant.status === 'error') {
        responseTone = 'danger';
      } else if (latestAssistant.status === 'stopped') {
        responseTone = 'warning';
      } else {
        responseTone = 'success';
      }
    }

    const responsePhase: ExecutionPhase = { key: 'response', label: t('browserTask.observer.phase.response'), value: responseValue, detail: responseDetail, tone: responseTone };

    return [sessionPhase, runPhase, toolsPhase, responsePhase];
  });

  /* ── observer ── */

  const observerToggleLabel = computed(() =>
    observer.observerOpen.value ? t('browserTask.actions.closeDrawer') : t('browserTask.actions.openDrawer'),
  );

  /* ── live region ── */

  const liveRegionMessage = computed(() => {
    if (session.loadingBootstrap.value) {
      return t('browserTask.actions.reloadLoading');
    }
    if (session.creatingSession.value) {
      return t('browserTask.actions.newSessionLoading');
    }
    if (session.submittingMessage.value) {
      return t('browserTask.actions.sendLoading');
    }
    if (isStopping.value) {
      return t('browserTask.actions.stopLoading');
    }
    if (session.errorMessage.value) {
      return session.errorMessage.value;
    }
    if (session.sessionState.value) {
      return `${t('browserTask.observer.phase.session')} · ${sessionStatusLabel.value}`;
    }
    return connectionLabel.value;
  });

  /* ── message fingerprint (for watchers) ── */

  const lastMessageFingerprint = computed(() => {
    const lastMessage = messages.messages.value[messages.messages.value.length - 1];
    if (!lastMessage) {
      return 'empty';
    }
    return `${messages.messages.value.length}:${lastMessage.id}:${lastMessage.status}:${lastMessage.content.length}`;
  });

  return {
    /* helpers exposed for template */
    formatTimelineTime,
    formatCompactValue,
    formatSessionStatus,

    /* core derived state */
    isStopping,
    isRunning,
    isBusy,
    isCreatingOrSending,
    sessionLocked,
    selectedModelProfileLabel,
    activeSessionUrl,
    skillItems,

    /* topbar / status */
    statusBadgeClass,
    sessionStatusLabel,
    connectionLabel,
    topbarDescription,

    /* primary action */
    primaryActionLabel,
    primaryActionDisabled,

    /* composer */
    composerMetaHint,
    draftCharacterCount,

    /* chat shell */
    chatAssistiveHint,
    showLiveStrip,
    liveStripTone,
    liveStripTitle,
    liveStripLabel,
    emptyStateTitle,
    emptyStateCopy,
    emptyStateFacts,
    quickPrompts,

    /* browser view */
    latestAssistantExcerpt,
    stageSteps,
    browserStageTitle,
    browserStageCopy,
    browserPreviewTitle,
    browserPreviewCopy,
    browserStageFacts,

    /* timeline / tools */
    toolChips,
    agentTimelineItems,
    toolFeedItems,

    /* task system */
    taskSystemFacts,
    lockedSetupFacts,
    executionPhases,

    /* observer */
    observerToggleLabel,

    /* live region */
    liveRegionMessage,

    /* watcher keys */
    lastMessageFingerprint,
  };
}

export type BrowserTaskUIApi = ReturnType<typeof useBrowserTaskUI>;
