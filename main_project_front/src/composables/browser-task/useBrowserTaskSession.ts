import { reactive, ref, watch } from 'vue';

import {
  closeBrowserTaskSession,
  createBrowserTaskSession,
  fetchBrowserTaskBootstrap,
  sendBrowserTaskMessage,
  stopBrowserTaskSession,
  type BrowserTaskBootstrapPayload,
  type BrowserTaskSessionState,
} from '@/views/api';
import { readJsonStorage, writeJsonStorage } from '@/utils/storage';
import type { BrowserTaskRuntimeApi } from './useBrowserTaskRuntime';
import type { BrowserTaskMessagesApi } from './useBrowserTaskMessages';
import type { BrowserTaskStreamApi } from './useBrowserTaskStream';

const BROWSER_TASK_SELECTION_STORAGE_KEY = 'browser-task:selection-preferences';

interface BrowserTaskSelectionPreferences {
  selectedModelProfileKey: string;
  selectedSkills: string[];
}

function normalizeSelectedSkills(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return Array.from(new Set(value.map((item) => String(item ?? '').trim()).filter(Boolean)));
}

function collapseSelectedSkillsToVisibleSelections(selected: string[], available: string[]): string[] {
  return Array.from(
    new Set(
      selected
        .map((value) => {
          const normalized = String(value ?? '').trim();
          if (!normalized) {
            return '';
          }
          if (available.includes(normalized)) {
            return normalized;
          }
          const candidates = available
            .filter((item) => normalized === item || normalized.startsWith(`${item}/`))
            .sort((left, right) => right.length - left.length);
          return candidates[0] ?? '';
        })
        .filter(Boolean),
    ),
  );
}

function getStoredBrowserTaskSelectionPreferences(): BrowserTaskSelectionPreferences {
  const fallback: BrowserTaskSelectionPreferences = {
    selectedModelProfileKey: '',
    selectedSkills: [],
  };
  const raw = readJsonStorage<Partial<BrowserTaskSelectionPreferences> | null>(BROWSER_TASK_SELECTION_STORAGE_KEY, null);
  if (!raw) {
    return fallback;
  }
  return {
    selectedModelProfileKey: String(raw.selectedModelProfileKey ?? '').trim(),
    selectedSkills: normalizeSelectedSkills(raw.selectedSkills),
  };
}

function persistBrowserTaskSelectionPreferences(value: BrowserTaskSelectionPreferences): void {
  writeJsonStorage(BROWSER_TASK_SELECTION_STORAGE_KEY, {
    selectedModelProfileKey: String(value.selectedModelProfileKey ?? '').trim(),
    selectedSkills: normalizeSelectedSkills(value.selectedSkills),
  });
}

export interface BrowserTaskSessionOptions {
  runtime: BrowserTaskRuntimeApi;
  messages: BrowserTaskMessagesApi;
  stream: BrowserTaskStreamApi;
  t: (key: string, params?: Record<string, unknown>) => string;
  openObserverPanel: () => void;
  closeObserverPanel: (returnFocus?: boolean) => void;
  isInlineTaskSystem: { value: boolean };
  focusPromptComposer: () => void;
  focusModelSelection: () => void;
}

export function useBrowserTaskSession(opts: BrowserTaskSessionOptions) {
  const { runtime, messages, stream, t, openObserverPanel, closeObserverPanel, isInlineTaskSystem, focusPromptComposer, focusModelSelection } = opts;
  void openObserverPanel;
  const storedPreferences = getStoredBrowserTaskSelectionPreferences();

  const bootstrap = reactive<BrowserTaskBootstrapPayload>({
    skills: [],
    skillsEnabled: false,
    modelProfiles: [],
    runtimeMode: 'standalone',
    persistenceMode: 'memory_only',
    mcpSelectorHidden: true,
    systemPromptSource: 'browser_agent_system_prompt',
  });

  const selectedSkills = ref<string[]>(storedPreferences.selectedSkills);
  const hasCustomizedSkills = ref(storedPreferences.selectedSkills.length > 0);
  const selectedModelProfileKey = ref(storedPreferences.selectedModelProfileKey);
  const draftMessage = ref('');
  const loadingBootstrap = ref(false);
  const creatingSession = ref(false);
  const submittingMessage = ref(false);
  const stoppingRun = ref(false);
  const errorMessage = ref('');
  const sessionState = ref<BrowserTaskSessionState | null>(null);
  const shouldStickToBottom = ref(true);

  watch(
    [selectedModelProfileKey, selectedSkills],
    ([nextModelProfileKey, nextSelectedSkills]) => {
      persistBrowserTaskSelectionPreferences({
        selectedModelProfileKey: nextModelProfileKey,
        selectedSkills: nextSelectedSkills,
      });
    },
    { deep: true },
  );

  function toggleSkill(value: string, checked: boolean): void {
    hasCustomizedSkills.value = true;
    const next = new Set(selectedSkills.value);
    if (checked) {
      next.add(value);
    } else {
      next.delete(value);
    }
    selectedSkills.value = Array.from(next);
  }

  function applyPromptSuggestion(prompt: string, observerOpen?: { value: boolean }): void {
    draftMessage.value = prompt;
    if (!isInlineTaskSystem.value && observerOpen?.value) {
      closeObserverPanel(false);
    }
    focusPromptComposer();
  }

  function applyPromptExample(exampleText: string): void {
    const currentDraft = draftMessage.value;
    if (currentDraft.trim().length === 0) {
      draftMessage.value = exampleText;
      focusPromptComposer();
      return;
    }
    const separator = currentDraft.endsWith('\n') ? '' : '\n';
    draftMessage.value = currentDraft + separator + exampleText;
    focusPromptComposer();
  }

  async function reloadBootstrap(): Promise<void> {
    loadingBootstrap.value = true;
    errorMessage.value = '';
    try {
      const payload = await fetchBrowserTaskBootstrap();
      const previousSelectedSkills = [...selectedSkills.value];
      bootstrap.skills = payload.skills;
      bootstrap.skillsEnabled = payload.skillsEnabled;
      bootstrap.modelProfiles = payload.modelProfiles;
      bootstrap.runtimeMode = payload.runtimeMode;
      bootstrap.persistenceMode = payload.persistenceMode;
      bootstrap.mcpSelectorHidden = payload.mcpSelectorHidden;
      bootstrap.systemPromptSource = payload.systemPromptSource;
      if (!payload.skillsEnabled) {
        selectedSkills.value = [];
        hasCustomizedSkills.value = false;
      } else if (!hasCustomizedSkills.value) {
        selectedSkills.value = [];
      } else {
        selectedSkills.value = collapseSelectedSkillsToVisibleSelections(previousSelectedSkills, payload.skills);
      }
      if (!selectedModelProfileKey.value || !payload.modelProfiles.find((item) => item.key === selectedModelProfileKey.value)) {
        selectedModelProfileKey.value = payload.modelProfiles[0]?.key ?? '';
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : String(error);
    } finally {
      loadingBootstrap.value = false;
    }
  }

  async function ensureSession(): Promise<string> {
    if (sessionState.value?.sessionId && sessionState.value.status !== 'closed') {
      return sessionState.value.sessionId;
    }
    const result = await createBrowserTaskSession({
      skills: selectedSkills.value,
      modelProfileKey: selectedModelProfileKey.value,
    });
    sessionState.value = result.sessionState;
    messages.resetMessages();
    runtime.resetRuntimeState();
    stream.connectStream(result.sessionId);
    if (result.bootstrapStarted) {
      runtime.appendRuntimeEvent({
        kind: 'session',
        rawType: 'bootstrap.started',
        label: t('browserTask.activity.bootstrapLabel'),
        summary: t('browserTask.activity.bootstrapSummary'),
        status: 'running',
        tone: 'accent',
        runId: 0,
      });
    }
    return result.sessionId;
  }

  async function createFreshSession(): Promise<void> {
    if (!selectedModelProfileKey.value) {
      errorMessage.value = t('browserTask.hints.selectModel');
      focusModelSelection();
      return;
    }
    creatingSession.value = true;
    errorMessage.value = '';
    try {
      if (sessionState.value?.sessionId) {
        await closeBrowserTaskSession(sessionState.value.sessionId);
      }
      stream.closeStream();
      sessionState.value = null;
      messages.resetMessages();
      runtime.resetRuntimeState();
      await ensureSession();
      if (!isInlineTaskSystem.value) {
        closeObserverPanel(false);
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : String(error);
    } finally {
      creatingSession.value = false;
    }
  }

  async function resetSession(): Promise<void> {
    try {
      if (sessionState.value?.sessionId) {
        await closeBrowserTaskSession(sessionState.value.sessionId);
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : String(error);
    } finally {
      stream.closeStream();
      sessionState.value = null;
      messages.resetMessages();
      runtime.resetRuntimeState();
      stoppingRun.value = false;
    }
  }

  async function sendMessage(): Promise<void> {
    const content = draftMessage.value.trim();
    const isBusy = sessionState.value?.status === 'running' || sessionState.value?.status === 'bootstrapping' || stoppingRun.value || sessionState.value?.status === 'stopping';
    if (!content || isBusy) {
      return;
    }
    if (!selectedModelProfileKey.value) {
      errorMessage.value = t('browserTask.hints.selectModel');
      focusModelSelection();
      return;
    }
    submittingMessage.value = true;
    errorMessage.value = '';
    try {
      const sessionId = await ensureSession();
      const result = await sendBrowserTaskMessage(sessionId, content);
      messages.upsertMessage({
        id: result.messageId,
        role: 'user',
        content,
        status: 'done',
        createdAt: new Date().toISOString(),
      });
      draftMessage.value = '';
      shouldStickToBottom.value = true;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : String(error);
    } finally {
      submittingMessage.value = false;
    }
  }

  async function stopRun(): Promise<void> {
    if (!sessionState.value?.sessionId || stoppingRun.value || sessionState.value?.status === 'stopping') {
      return;
    }
    stoppingRun.value = true;
    errorMessage.value = '';
    try {
      const result = await stopBrowserTaskSession(sessionState.value.sessionId);
      sessionState.value = result.sessionState;
    } catch (error) {
      stoppingRun.value = false;
      errorMessage.value = error instanceof Error ? error.message : String(error);
    }
  }

  function handlePrimaryAction(): void {
    const isRunning = sessionState.value?.status === 'running' || sessionState.value?.status === 'bootstrapping';
    const isStopping = stoppingRun.value || sessionState.value?.status === 'stopping';
    if (isRunning || isStopping) {
      void stopRun();
      return;
    }
    void sendMessage();
  }

  return {
    bootstrap,
    selectedSkills,
    hasCustomizedSkills,
    selectedModelProfileKey,
    draftMessage,
    loadingBootstrap,
    creatingSession,
    submittingMessage,
    stoppingRun,
    errorMessage,
    sessionState,
    shouldStickToBottom,
    toggleSkill,
    applyPromptSuggestion,
    applyPromptExample,
    reloadBootstrap,
    ensureSession,
    createFreshSession,
    resetSession,
    sendMessage,
    stopRun,
    handlePrimaryAction,
  };
}

export type BrowserTaskSessionApi = ReturnType<typeof useBrowserTaskSession>;
