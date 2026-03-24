<template>
  <div class="arv">
    <header class="arv-hero">
      <div class="arv-hero__lead">
        <h1 class="arv-hero__title">{{ t('autoReverse.title') }}</h1>
        <p class="arv-hero__subtitle">{{ currentTaskId ? t('autoReverse.workspace.leadRuntime') : t('autoReverse.workspace.leadCompose') }}</p>
      </div>
      <div class="arv-hero__meta">
        <n-tag
          v-for="tag in taskStatusTags"
          :key="`${tag.label}-${tag.type || 'default'}`"
          :bordered="false"
          size="small"
          :type="tag.type || 'default'"
          round
        >{{ tag.label }}</n-tag>
        <WorkspaceRefreshButton
          :label="t('home.actions.refresh')"
          :loading-label="t('common.status.syncing')"
          :aria-label="t('home.actions.refresh')"
          :loading="heroRefreshLoading"
          compact
          @click="handleRefresh"
        />
      </div>
    </header>

    <n-alert v-if="resourcesErrorDetail" type="error" :show-icon="false" class="arv-alert">
      {{ t('autoReverse.errors.loadOptions', { message: resourcesErrorDetail }) }}
    </n-alert>
    <n-alert v-else-if="submitErrorDetail" type="error" :show-icon="false" class="arv-alert">
      {{ submitErrorDetail }}
    </n-alert>
    <n-alert v-else-if="taskErrorDetail" type="error" :show-icon="false" class="arv-alert">
      {{ taskErrorDetail }}
    </n-alert>

    <div v-if="isMobile" class="arv-switcher">
      <n-tabs v-model:value="activeMobilePanel" type="segment" size="small">
        <n-tab name="compose">{{ t('autoReverse.workspace.viewCompose') }}</n-tab>
        <n-tab name="runtime">{{ t('autoReverse.workspace.viewRuntime') }}</n-tab>
        <n-tab name="archives">{{ t('autoReverse.successArchives.title') }}</n-tab>
      </n-tabs>
    </div>

    <div class="arv-workspace" :class="{ 'arv-workspace--mobile': isMobile }">
      <aside v-show="!isMobile || activeMobilePanel === 'compose'" class="arv-compose">
        <div class="arv-compose__surface">
          <details class="arv-fold" open>
            <summary class="arv-fold__toggle">
              <span class="arv-fold__label">{{ t('autoReverse.fields.urlListLabel') }}</span>
              <span class="arv-fold__chevron" aria-hidden="true"></span>
            </summary>
            <div class="arv-fold__body">
              <AutoReverseUrlInputCard
                v-model="urlDraft"
                eyebrow=""
                title=""
                :placeholder="t('autoReverse.fields.urlListPlaceholder')"
                :count="urlCountLabel"
                helper-text=""
              />
            </div>
          </details>

          <hr class="arv-divider" />

          <details class="arv-fold">
            <summary class="arv-fold__toggle">
              <span class="arv-fold__label">{{ t('autoReverse.compose.browserModeTitle') }}</span>
              <span class="arv-fold__badge">{{ browserMode }}</span>
              <span class="arv-fold__chevron" aria-hidden="true"></span>
            </summary>
            <div class="arv-fold__body">
              <ModeSegmentControl
                v-model="browserMode"
                :options="browserModeOptions"
              />
              <div class="arv-run-params">
                <div class="arv-run-param-row">
                  <span class="arv-run-param-row__label">{{ t('autoReverse.compose.maxConcurrentLabel') }}</span>
                  <n-input-number
                    v-model:value="maxConcurrent"
                    :min="1"
                    :max="20"
                    size="small"
                    class="arv-run-param-row__input"
                  />
                </div>
                <div v-if="browserMode === 'standalone'" class="arv-run-param-row">
                  <span class="arv-run-param-row__label">{{ t('autoReverse.compose.headlessModeLabel') }}</span>
                  <n-switch v-model:value="headlessMode" size="small" />
                </div>
              </div>
            </div>
          </details>

          <hr class="arv-divider" />

          <div class="arv-compose__agents">
            <div class="arv-agent-switcher">
              <button
                type="button"
                class="arv-agent-tab arv-agent-tab--browser"
                :class="{ 'arv-agent-tab--active': activeAgentTab === 'browser' }"
                @click="activeAgentTab = 'browser'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />
                </svg>
                {{ t('autoReverse.compose.browserAgentTitle') }}
                <span v-if="browserModelProfileKey" class="arv-agent-tab__indicator"></span>
              </button>
              <button
                type="button"
                class="arv-agent-tab arv-agent-tab--analyse"
                :class="{ 'arv-agent-tab--active': activeAgentTab === 'analyse' }"
                @click="activeAgentTab = 'analyse'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                </svg>
                {{ t('autoReverse.compose.analyseAgentTitle') }}
                <span v-if="analyseModelProfileKey" class="arv-agent-tab__indicator"></span>
              </button>
            </div>

            <AutoReverseAgentConfigCard
              v-show="activeAgentTab === 'browser'"
              accent="browser"
              agent-id="browser"
              :eyebrow="t('autoReverse.compose.browserAgentTitle')"
              :title="selectedBrowserProfileLabel"
              :selected-model-profile-key="browserModelProfileKey"
              :selected-model-label="selectedBrowserProfileLabel"
              :model-profiles="availableModelProfiles"
              :model-placeholder="t('autoReverse.fields.modelProfilePlaceholder')"
              :model-disabled="availableModelProfiles.length === 0"
              :model-label="t('autoReverse.compose.agentModelLabel')"
              :mcp-label="t('autoReverse.compose.agentMcpLabel')"
              :skills-label="t('autoReverse.compose.agentSkillsLabel')"
              :mcp-items="browserMcpItems"
              :mcp-count="browserSelectedMcp.length"
              :mcp-total="availableMcpTools.length"
              :mcp-hint="t('autoReverse.fields.lockedMcpHint')"
              :mcp-empty-text="t('autoReverse.fields.noMcpTools')"
              :skill-items="browserSkillItems"
              :skill-count="browserSelectedSkills.length"
              :skill-total="availableSkills.length"
              :skill-empty-text="skillEmptyText"
              :active="Boolean(browserModelProfileKey)"
              @update:model-profile-key="browserModelProfileKey = $event"
              @toggle-mcp="toggleBrowserMcp"
              @toggle-skill="toggleBrowserSkill"
            />
            <AutoReverseAgentConfigCard
              v-show="activeAgentTab === 'analyse'"
              accent="analyse"
              agent-id="analyse"
              :eyebrow="t('autoReverse.compose.analyseAgentTitle')"
              :title="selectedAnalyseProfileLabel"
              :selected-model-profile-key="analyseModelProfileKey"
              :selected-model-label="selectedAnalyseProfileLabel"
              :model-profiles="availableModelProfiles"
              :model-placeholder="t('autoReverse.fields.modelProfilePlaceholder')"
              :model-disabled="availableModelProfiles.length === 0"
              :model-label="t('autoReverse.compose.agentModelLabel')"
              :mcp-label="t('autoReverse.compose.agentMcpLabel')"
              :skills-label="t('autoReverse.compose.agentSkillsLabel')"
              :mcp-items="analyseMcpItems"
              :mcp-count="analyseSelectedMcp.length"
              :mcp-total="availableMcpTools.length"
              :mcp-hint="''"
              :mcp-empty-text="t('autoReverse.fields.noMcpTools')"
              :skill-items="analyseSkillItems"
              :skill-count="analyseSelectedSkills.length"
              :skill-total="availableSkills.length"
              :skill-empty-text="skillEmptyText"
              :active="Boolean(analyseModelProfileKey)"
              @update:model-profile-key="analyseModelProfileKey = $event"
              @toggle-mcp="toggleAnalyseMcp"
              @toggle-skill="toggleAnalyseSkill"
            />
          </div>

          <n-button type="primary" size="large" block :loading="submitLoading" class="arv-compose__submit" @click="handleSubmit">
            {{ submitLoading ? t('autoReverse.actions.submitTaskLoading') : t('autoReverse.actions.submitTask') }}
          </n-button>
        </div>
      </aside>

      <main v-show="!isMobile || activeMobilePanel === 'runtime'" class="arv-runtime">
        <section class="arv-runtime-fold arv-runtime-fold--dashboard" :class="{ 'arv-runtime-fold--open': true }">
          <n-spin v-if="taskLoading && !taskStatus" size="small" style="padding: 24px 0;" />
          <n-empty v-else-if="!taskStatus" :description="t('autoReverse.workspace.runtimeEmpty')" />
          <template v-else>
            <div class="arv-dash-bar">
              <div class="arv-dash-bar__lead">
                <span class="arv-dash-bar__id" :title="taskStatus.taskId">#{{ taskStatus.taskId.slice(0, 8) }}</span>
                <span class="status-tag" :class="resolveStatusClass(taskStatus.status)">{{ getTaskStatusLabel(taskStatus.status) }}</span>
                <span class="arv-dash-bar__stat">{{ taskStatus.urls.length }} URLs</span>
              </div>
              <span class="arv-dash-bar__time">{{ formatDateTime(taskStatus.updatedAt) }}</span>
            </div>

            <div v-if="taskStatus.steps.length > 0" class="arv-step-summary">
              <div
                v-for="step in taskStatus.steps"
                :key="step.key"
                class="arv-step-row"
                :class="stepRowClass(step.status)"
              >
                <div class="arv-step-row__head">
                  <span class="arv-step-row__label">{{ t(`autoReverse.progress.steps.${step.key}`) }}</span>
                  <span class="arv-step-row__counts">{{ stepCountLabel(step) }}</span>
                </div>
              </div>
            </div>

            <div class="arv-runtime__grid">
              <section class="arv-panel arv-panel--inspector">
                <n-empty v-if="runtimeExecutionItems.length === 0" :description="t('autoReverse.parallel.empty')" />
                <div v-else class="arv-stack">
                  <AutoReverseRuntimeInspector
                    v-for="(item, index) in runtimeExecutionItems"
                    :key="runtimeItemKey(item)"
                    :item="item"
                    :initially-open="index === 0"
                    :title="t('autoReverse.results.title')"
                    :subtitle="t('autoReverse.results.inspectorTitle')"
                    :empty-copy="t('autoReverse.results.inspectorEmpty')"
                    :browser-label="t('autoReverse.progress.steps.browser_agent')"
                    :analyse-label="t('autoReverse.progress.steps.analyse_agent')"
                    :is-mobile="isMobile"
                    :mcp-tools-label="t('autoReverse.compose.agentMcpLabel')"
                    :no-mcp-tools-text="t('autoReverse.fields.noMcpTools')"
                    :final-label="t('autoReverse.parallel.finalLabel')"
                    :session-label="t('autoReverse.results.sessionLabel')"
                    :updated-label="t('autoReverse.results.updatedAt')"
                    :report-label="t('autoReverse.results.reportLabel')"
                    :error-label="t('autoReverse.results.errorLabel')"
                    :empty-text="t('common.misc.empty')"
                    :no-report="t('autoReverse.results.noReport')"
                    :get-task-status-label="getTaskStatusLabel"
                    :format-date-time="formatDateTime"
                    :format-stage-time="formatStageTime"
                  />
                </div>
              </section>
            </div>
          </template>
        </section>
        <details v-show="!isMobile || activeMobilePanel === 'archives'" class="arv-runtime-fold">
          <summary class="arv-runtime-fold__toggle">
            <span class="arv-runtime-fold__label">{{ t('autoReverse.successArchives.title') }}</span>
            <span v-if="successArchives.length" class="arv-fold__badge">{{ successArchives.length }}</span>
            <span class="arv-fold__chevron" aria-hidden="true"></span>
          </summary>
          <div class="arv-runtime-fold__body">
            <n-spin v-if="archivesLoading && successArchives.length === 0" size="small" />
            <n-empty v-else-if="successArchives.length === 0" :description="archiveEmptyText" />
            <div v-else class="arv-stack">
              <AutoReverseReportDisclosure
                v-for="archive in successArchives"
                :key="String(archive.id)"
                :title="archive.url"
                :meta="`${t('autoReverse.labels.taskId')} · ${archive.taskId}`"
                :status-label="t('autoReverse.successArchives.archivedStatus')"
                status-class="status-tag--success"
                :content="archive.reportText"
                :timestamp="formatDateTime(archive.createdAt)"
                archive
              />
            </div>
          </div>
        </details>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { NAlert, NButton, NEmpty, NInputNumber, NSpin, NSwitch, NTab, NTabs, NTag } from 'naive-ui';

import ModeSegmentControl, { type ModeSegmentOption } from '@/components/ModeSegmentControl.vue';
import type { WorkspaceHeaderTag } from '@/components/WorkspacePageHeader.vue';
import AutoReverseAgentConfigCard from '@/components/auto-reverse/AutoReverseAgentConfigCard.vue';
import type { AutoReverseCapabilityItem } from '@/components/auto-reverse/AutoReverseCapabilityGroup.vue';
import AutoReverseReportDisclosure from '@/components/auto-reverse/AutoReverseReportDisclosure.vue';
import AutoReverseRuntimeInspector from '@/components/auto-reverse/AutoReverseRuntimeInspector.vue';
import AutoReverseUrlInputCard from '@/components/auto-reverse/AutoReverseUrlInputCard.vue';
import WorkspaceRefreshButton from '@/components/WorkspaceRefreshButton.vue';
import { useLocale } from '@/composables/useLocale';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { ROUTE_PATHS } from '@/constants/routes';
import { readJsonStorage, writeJsonStorage } from '@/utils/storage';
import {
  fetchAutoReverseTaskResults,
  fetchAutoReverseTaskStatus,
  fetchSuccessResultArchives,
  submitAutoReverseTask,
  type AgentResourceSelection,
  type AnalysisResultItem,
  type AutoReverseTaskStatus,
  type BrowserMode,
  type ModelProfileOption,
  type SuccessResultArchiveItem,
  type TaskExecutionItem,
} from '@/views/api';

const AUTO_REVERSE_COMPOSE_STORAGE_KEY = 'auto-reverse:compose-preferences';

type AgentTab = 'browser' | 'analyse';

interface AutoReverseComposePreferences {
  browserMode: BrowserMode;
  headlessMode: boolean;
  maxConcurrent: number;
  browserModelProfileKey: string;
  analyseModelProfileKey: string;
  browserSelectedMcp: string[];
  analyseSelectedMcp: string[];
  browserSelectedSkills: string[];
  analyseSelectedSkills: string[];
  activeAgentTab: AgentTab;
}

function normalizePersistedStrings(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return Array.from(new Set(value.map((item) => String(item ?? '').trim()).filter(Boolean)));
}

function getStoredAutoReverseComposePreferences(): AutoReverseComposePreferences {
  const fallback: AutoReverseComposePreferences = {
    browserMode: 'roxy',
    headlessMode: false,
    maxConcurrent: 3,
    browserModelProfileKey: '',
    analyseModelProfileKey: '',
    browserSelectedMcp: [],
    analyseSelectedMcp: [],
    browserSelectedSkills: [],
    analyseSelectedSkills: [],
    activeAgentTab: 'browser',
  };
  const raw = readJsonStorage<Partial<AutoReverseComposePreferences> | null>(AUTO_REVERSE_COMPOSE_STORAGE_KEY, null);
  if (!raw) {
    return fallback;
  }
  const rawMaxConcurrent = Number(raw.maxConcurrent);
  return {
    browserMode: raw.browserMode === 'standalone' ? 'standalone' : fallback.browserMode,
    headlessMode: Boolean(raw.headlessMode),
    maxConcurrent: Number.isFinite(rawMaxConcurrent) && rawMaxConcurrent >= 1 ? Math.min(20, Math.max(1, rawMaxConcurrent)) : fallback.maxConcurrent,
    browserModelProfileKey: String(raw.browserModelProfileKey ?? '').trim(),
    analyseModelProfileKey: String(raw.analyseModelProfileKey ?? '').trim(),
    browserSelectedMcp: normalizePersistedStrings(raw.browserSelectedMcp),
    analyseSelectedMcp: normalizePersistedStrings(raw.analyseSelectedMcp),
    browserSelectedSkills: normalizePersistedStrings(raw.browserSelectedSkills),
    analyseSelectedSkills: normalizePersistedStrings(raw.analyseSelectedSkills),
    activeAgentTab: raw.activeAgentTab === 'analyse' ? 'analyse' : 'browser',
  };
}

function persistAutoReverseComposePreferences(value: AutoReverseComposePreferences): void {
  writeJsonStorage(AUTO_REVERSE_COMPOSE_STORAGE_KEY, {
    browserMode: value.browserMode === 'standalone' ? 'standalone' : 'roxy',
    headlessMode: Boolean(value.headlessMode),
    maxConcurrent: Math.min(20, Math.max(1, Number(value.maxConcurrent) || 3)),
    browserModelProfileKey: String(value.browserModelProfileKey ?? '').trim(),
    analyseModelProfileKey: String(value.analyseModelProfileKey ?? '').trim(),
    browserSelectedMcp: normalizePersistedStrings(value.browserSelectedMcp),
    analyseSelectedMcp: normalizePersistedStrings(value.analyseSelectedMcp),
    browserSelectedSkills: normalizePersistedStrings(value.browserSelectedSkills),
    analyseSelectedSkills: normalizePersistedStrings(value.analyseSelectedSkills),
    activeAgentTab: value.activeAgentTab === 'analyse' ? 'analyse' : 'browser',
  });
}

const { t, formatDateTime, getTaskStatusLabel } = useLocale();
const { autoReverseOptions, autoReverseConfig, resourcesLoading, resourcesErrorDetail, reloadAutoReverseResources } = useWorkspaceData();
const route = useRoute();
const router = useRouter();
const storedComposePreferences = getStoredAutoReverseComposePreferences();

const urlDraft = ref('');
const browserMode = ref<BrowserMode>(storedComposePreferences.browserMode);
const headlessMode = ref(storedComposePreferences.headlessMode);
const maxConcurrent = ref(storedComposePreferences.maxConcurrent);
const browserModelProfileKey = ref(storedComposePreferences.browserModelProfileKey);
const analyseModelProfileKey = ref(storedComposePreferences.analyseModelProfileKey);
const browserSelectedMcp = ref<string[]>(storedComposePreferences.browserSelectedMcp);
const analyseSelectedMcp = ref<string[]>(storedComposePreferences.analyseSelectedMcp);
const browserSelectedSkills = ref<string[]>(storedComposePreferences.browserSelectedSkills);
const analyseSelectedSkills = ref<string[]>(storedComposePreferences.analyseSelectedSkills);

const currentTaskId = ref('');
const taskStatus = ref<AutoReverseTaskStatus | null>(null);
const taskResults = ref<AnalysisResultItem[]>([]);
const successArchives = ref<SuccessResultArchiveItem[]>([]);

const submitLoading = ref(false);
const taskLoading = ref(false);
const archivesLoading = ref(false);
const submitErrorDetail = ref('');
const taskErrorDetail = ref('');
const isMobile = ref(false);
const activeMobilePanel = ref<'compose' | 'runtime' | 'archives'>('compose');
const activeAgentTab = ref<AgentTab>(storedComposePreferences.activeAgentTab);

let pollTimer: number | null = null;
let taskRequestVersion = 0;

const normalizedQueryTaskId = computed(() => {
  const raw = route.query.taskId;
  return typeof raw === 'string' ? raw.trim() : '';
});

const availableMcpTools = computed(() => autoReverseOptions.value?.mcpTools ?? []);
const availableSkills = computed(() => autoReverseOptions.value?.skills ?? []);
const availableModelProfiles = computed<ModelProfileOption[]>(() =>
  (autoReverseOptions.value?.modelProfiles ?? []).filter((item) => item.enabled !== false),
);

const currentBrowserLockedMcp = computed(() => {
  const perMode = autoReverseOptions.value?.lockedMcpToolsByMode?.[browserMode.value] ?? [];
  if (perMode.length > 0) {
    return perMode;
  }
  return autoReverseOptions.value?.lockedMcpTools ?? [];
});

const currentAnalyseLockedMcp = computed<string[]>(() =>
  [],
);

const browserModeDisabledMcp = computed(() => {
  const allModeLocked = new Set(Object.values(autoReverseOptions.value?.lockedMcpToolsByMode ?? {}).flat());
  const currentLocked = new Set(currentBrowserLockedMcp.value);
  return new Set([...allModeLocked].filter((item) => !currentLocked.has(item)));
});

const browserModeOptions = computed<ModeSegmentOption[]>(() =>
  (autoReverseOptions.value?.browserModes ?? []).map((mode) => ({
    value: mode,
    label: t(`autoReverse.browserModes.${mode}.label`),
    badge: t(`autoReverse.browserModes.${mode}.badge`),
    meta: t(`autoReverse.browserModes.${mode}.meta`),
    description: t(`autoReverse.browserModes.${mode}.description`),
  })),
);

const parsedUrls = computed(() =>
  Array.from(
    new Set(
      urlDraft.value
        .split(/\r?\n|,/)
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  ),
);

const urlCountLabel = computed(() => String(parsedUrls.value.length).padStart(2, '0'));

const selectedBrowserProfileLabel = computed(
  () => availableModelProfiles.value.find((item) => item.key === browserModelProfileKey.value)?.label ?? t('autoReverse.compose.browserAgentTitle'),
);

const selectedAnalyseProfileLabel = computed(
  () => availableModelProfiles.value.find((item) => item.key === analyseModelProfileKey.value)?.label ?? t('autoReverse.compose.analyseAgentTitle'),
);

const skillEmptyText = computed(() =>
  autoReverseOptions.value?.skillsEnabled ? t('autoReverse.compose.emptySkills') : t('autoReverse.fields.skillsDisabledTitle'),
);

const taskStatusTags = computed<WorkspaceHeaderTag[]>(() => {
  const tags: WorkspaceHeaderTag[] = [];
  if (currentTaskId.value) {
    tags.push({
      label: getTaskStatusLabel(taskStatus.value?.status ?? 'pending'),
      type: resolveHeaderTagType(taskStatus.value?.status ?? 'pending'),
    });
    tags.push({
      label: `#${currentTaskId.value.slice(0, 8)}`,
      type: 'default',
    });
    return tags;
  }
  tags.push({ label: t('autoReverse.workspace.viewCompose'), type: 'default' });
  return tags;
});

function stepCountLabel(step: { total: number; success: number; failed: number; running: number; queued: number; pending: number; skipped?: number }): string {
  return t('autoReverse.progress.counts', {
    total: step.total,
    success: step.success,
    failed: step.failed,
    running: step.running,
    queued: step.queued,
    pending: step.pending,
    skipped: step.skipped ?? 0,
  });
}

function stepRowClass(status: string): string {
  const lower = status.toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'arv-step-row--success';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'arv-step-row--running';
  if (lower.includes('fail') || lower.includes('error')) return 'arv-step-row--danger';
  return '';
}

const runtimeExecutionItems = computed(() => taskStatus.value?.items ?? []);
const archiveEmptyText = computed(() =>
  currentTaskId.value ? t('autoReverse.successArchives.emptyTask') : t('autoReverse.successArchives.emptyAll'),
);

const heroRefreshLoading = computed(() => resourcesLoading.value || taskLoading.value || archivesLoading.value);

const browserMcpItems = computed<AutoReverseCapabilityItem[]>(() =>
  buildMcpItems(browserSelectedMcp.value, [...currentBrowserLockedMcp.value], browserModeDisabledMcp.value),
);

const analyseMcpItems = computed<AutoReverseCapabilityItem[]>(() =>
  buildMcpItems(analyseSelectedMcp.value, [...currentAnalyseLockedMcp.value], new Set<string>()),
);

const browserSkillItems = computed<AutoReverseCapabilityItem[]>(() =>
  buildSkillItems(browserSelectedSkills.value),
);

const analyseSkillItems = computed<AutoReverseCapabilityItem[]>(() =>
  buildSkillItems(analyseSelectedSkills.value),
);

function uniqueStrings(items: string[]): string[] {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

function collapseSelectedSkillsToVisibleSelections(selected: string[]): string[] {
  const available = availableSkills.value;
  return uniqueStrings(
    selected
      .map((value) => {
        const normalized = value.trim();
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
  );
}

function runtimeItemKey(item: TaskExecutionItem): string {
  return `${item.urlIndex}:${item.url}:${item.sessionId ?? ''}`;
}

function resolveHeaderTagType(status: string): WorkspaceHeaderTag['type'] {
  const lower = status.trim().toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'success';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'warning';
  if (lower.includes('fail') || lower.includes('error')) return 'error';
  return 'default';
}

function resolveStatusClass(status: string): string {
  const lower = status.trim().toLowerCase();
  if (lower.includes('success') || lower.includes('complete')) return 'status-tag--success';
  if (lower.includes('running') || lower.includes('queued') || lower.includes('pending')) return 'status-tag--warning';
  if (lower.includes('skip')) return 'status-tag--skipped';
  if (lower.includes('fail') || lower.includes('error')) return 'status-tag--danger';
  return '';
}

function formatStageTime(startedAt?: string, completedAt?: string): string {
  if (!startedAt && !completedAt) {
    return t('autoReverse.task.stageMessageFallback');
  }
  if (startedAt && completedAt) {
    return `${formatDateTime(startedAt)} → ${formatDateTime(completedAt)}`;
  }
  return formatDateTime(startedAt || completedAt);
}

function isTerminalStatus(status: string): boolean {
  const lower = status.trim().toLowerCase();
  return (
    lower.includes('success') ||
    lower.includes('complete') ||
    lower.includes('fail') ||
    lower.includes('error') ||
    lower.includes('stopped') ||
    lower.includes('cancel')
  );
}

function buildMcpItems(selected: string[], locked: string[], disabled: Set<string>): AutoReverseCapabilityItem[] {
  return availableMcpTools.value.map((value) => {
    const isLocked = locked.includes(value);
    const isDisabled = disabled.has(value);
    return {
      value,
      label: value,
      selected: selected.includes(value),
      disabled: isLocked || isDisabled,
      meta: isLocked ? t('autoReverse.fields.lockedMcpTag') : isDisabled ? t('autoReverse.fields.modeFilteredMcpTag') : '',
      tone: isLocked ? 'locked' : isDisabled ? 'soft' : 'default',
    };
  });
}

function buildSkillItems(selected: string[]): AutoReverseCapabilityItem[] {
  return availableSkills.value.map((value) => ({
    value,
    label: value,
    selected: selected.includes(value),
    disabled: !autoReverseOptions.value?.skillsEnabled,
    meta: '',
    tone: 'soft',
  }));
}

watch(
  [browserMode, headlessMode, maxConcurrent, browserModelProfileKey, analyseModelProfileKey, browserSelectedMcp, analyseSelectedMcp, browserSelectedSkills, analyseSelectedSkills, activeAgentTab],
  ([
    nextBrowserMode,
    nextHeadlessMode,
    nextMaxConcurrent,
    nextBrowserModelProfileKey,
    nextAnalyseModelProfileKey,
    nextBrowserSelectedMcp,
    nextAnalyseSelectedMcp,
    nextBrowserSelectedSkills,
    nextAnalyseSelectedSkills,
    nextActiveAgentTab,
  ]) => {
    persistAutoReverseComposePreferences({
      browserMode: nextBrowserMode,
      headlessMode: nextHeadlessMode,
      maxConcurrent: nextMaxConcurrent,
      browserModelProfileKey: nextBrowserModelProfileKey,
      analyseModelProfileKey: nextAnalyseModelProfileKey,
      browserSelectedMcp: nextBrowserSelectedMcp,
      analyseSelectedMcp: nextAnalyseSelectedMcp,
      browserSelectedSkills: nextBrowserSelectedSkills,
      analyseSelectedSkills: nextAnalyseSelectedSkills,
      activeAgentTab: nextActiveAgentTab,
    });
  },
  { deep: true },
);

function syncBrowserMcpSelection(preserve = true): void {
  const availableSet = new Set(availableMcpTools.value);
  const disabledSet = browserModeDisabledMcp.value;
  const preserved = preserve
    ? browserSelectedMcp.value.filter((item) => availableSet.has(item) && !disabledSet.has(item))
    : [];
  browserSelectedMcp.value = uniqueStrings([
    ...preserved,
    ...currentBrowserLockedMcp.value.filter((item) => availableSet.has(item)),
  ]);
}

function syncAnalyseMcpSelection(preserve = true): void {
  const availableSet = new Set(availableMcpTools.value);
  const preserved = preserve ? analyseSelectedMcp.value.filter((item) => availableSet.has(item)) : [];
  analyseSelectedMcp.value = uniqueStrings([
    ...preserved,
    ...currentAnalyseLockedMcp.value.filter((item) => availableSet.has(item)),
  ]);
}

function ensureComposeDefaults(): void {
  if (!autoReverseOptions.value) {
    return;
  }

  const availableModes = autoReverseOptions.value.browserModes;
  if (!availableModes.includes(browserMode.value)) {
    browserMode.value = autoReverseConfig.value?.browserMode ?? autoReverseOptions.value.browserMode ?? availableModes[0] ?? 'roxy';
  }

  const availableProfileKeys = new Set(availableModelProfiles.value.map((item) => item.key));
  if (!browserModelProfileKey.value || !availableProfileKeys.has(browserModelProfileKey.value)) {
    browserModelProfileKey.value = availableModelProfiles.value[0]?.key ?? '';
  }
  if (!analyseModelProfileKey.value || !availableProfileKeys.has(analyseModelProfileKey.value)) {
    analyseModelProfileKey.value = availableModelProfiles.value[0]?.key ?? '';
  }

  const skillSet = new Set(availableSkills.value);
  browserSelectedSkills.value = collapseSelectedSkillsToVisibleSelections(browserSelectedSkills.value).filter((item) => skillSet.has(item));
  analyseSelectedSkills.value = collapseSelectedSkillsToVisibleSelections(analyseSelectedSkills.value).filter((item) => skillSet.has(item));

  syncBrowserMcpSelection(true);
  syncAnalyseMcpSelection(true);
}

function toggleBrowserMcp(value: string, checked: boolean): void {
  if (currentBrowserLockedMcp.value.includes(value) || browserModeDisabledMcp.value.has(value)) {
    return;
  }
  browserSelectedMcp.value = checked
    ? uniqueStrings([...browserSelectedMcp.value, value])
    : browserSelectedMcp.value.filter((item) => item !== value);
}

function toggleAnalyseMcp(value: string, checked: boolean): void {
  if (currentAnalyseLockedMcp.value.includes(value)) {
    return;
  }
  analyseSelectedMcp.value = checked
    ? uniqueStrings([...analyseSelectedMcp.value, value])
    : analyseSelectedMcp.value.filter((item) => item !== value);
}

function toggleBrowserSkill(value: string, checked: boolean): void {
  if (!autoReverseOptions.value?.skillsEnabled) {
    return;
  }
  browserSelectedSkills.value = checked
    ? uniqueStrings([...browserSelectedSkills.value, value])
    : browserSelectedSkills.value.filter((item) => item !== value);
}

function toggleAnalyseSkill(value: string, checked: boolean): void {
  if (!autoReverseOptions.value?.skillsEnabled) {
    return;
  }
  analyseSelectedSkills.value = checked
    ? uniqueStrings([...analyseSelectedSkills.value, value])
    : analyseSelectedSkills.value.filter((item) => item !== value);
}

function updateViewport(): void {
  isMobile.value = window.innerWidth < 1024;
}

async function loadResources(force = false): Promise<void> {
  submitErrorDetail.value = '';
  await reloadAutoReverseResources({ silent: !force, force });
  ensureComposeDefaults();
}

async function loadArchives(taskId?: string, limit = 20): Promise<void> {
  archivesLoading.value = true;
  try {
    successArchives.value = await fetchSuccessResultArchives({ taskId, limit });
  } finally {
    archivesLoading.value = false;
  }
}

async function refreshTask(taskId: string, options?: { silent?: boolean }): Promise<void> {
  const normalized = taskId.trim();
  if (!normalized) {
    return;
  }
  const requestVersion = ++taskRequestVersion;
  if (!options?.silent) {
    taskLoading.value = true;
  }
  try {
    const [statusPayload, resultsPayload, archivesPayload] = await Promise.all([
      fetchAutoReverseTaskStatus(normalized),
      fetchAutoReverseTaskResults(normalized),
      fetchSuccessResultArchives({ taskId: normalized, limit: 20 }),
    ]);
    if (requestVersion !== taskRequestVersion) {
      return;
    }
    currentTaskId.value = normalized;
    taskStatus.value = statusPayload;
    taskResults.value = resultsPayload;
    successArchives.value = archivesPayload;
    taskErrorDetail.value = '';
    if (normalizedQueryTaskId.value !== normalized) {
      await router.replace({ path: ROUTE_PATHS.AUTO_REVERSE, query: { taskId: normalized } });
    }
    if (isMobile.value) {
      activeMobilePanel.value = 'runtime';
    }
    if (isTerminalStatus(statusPayload.status)) {
      stopPolling();
    } else {
      startPolling(normalized);
    }
  } catch (error) {
    if (requestVersion !== taskRequestVersion) {
      return;
    }
    taskErrorDetail.value = t('autoReverse.errors.loadTask', {
      message: error instanceof Error ? error.message : String(error),
    });
    stopPolling();
  } finally {
    if (requestVersion === taskRequestVersion && !options?.silent) {
      taskLoading.value = false;
    }
  }
}

function startPolling(taskId: string): void {
  stopPolling();
  if (typeof window === 'undefined') {
    return;
  }
  pollTimer = window.setInterval(() => {
    void refreshTask(taskId, { silent: true });
  }, 5000);
}

function stopPolling(): void {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function handleSubmit(): Promise<void> {
  submitErrorDetail.value = '';
  const urls = parsedUrls.value;
  if (urls.length === 0) {
    submitErrorDetail.value = t('autoReverse.errors.emptyUrls');
    return;
  }
  if (!browserModelProfileKey.value || !analyseModelProfileKey.value) {
    submitErrorDetail.value = t('autoReverse.errors.emptyModelProfile');
    return;
  }

  submitLoading.value = true;
  try {
    const browserConfig: AgentResourceSelection = {
      browserMode: browserMode.value,
      mcpTools: browserSelectedMcp.value,
      skills: browserSelectedSkills.value,
      modelProfileKey: browserModelProfileKey.value,
    };
    const analyseConfig: AgentResourceSelection = {
      mcpTools: analyseSelectedMcp.value,
      skills: analyseSelectedSkills.value,
      modelProfileKey: analyseModelProfileKey.value,
    };
    const result = await submitAutoReverseTask({
      urls,
      browserConfig,
      analyseConfig,
      headless: headlessMode.value,
      maxConcurrent: maxConcurrent.value,
    });
    currentTaskId.value = result.taskId;
    await router.replace({ path: ROUTE_PATHS.AUTO_REVERSE, query: { taskId: result.taskId } });
    await refreshTask(result.taskId);
  } catch (error) {
    submitErrorDetail.value = t('autoReverse.errors.submitTask', {
      message: error instanceof Error ? error.message : String(error),
    });
  } finally {
    submitLoading.value = false;
  }
}

async function handleRefresh(): Promise<void> {
  const operations: Promise<unknown>[] = [
    loadResources(true).catch(() => undefined),
  ];

  if (currentTaskId.value) {
    operations.push(refreshTask(currentTaskId.value));
  } else {
    operations.push(
      loadArchives(undefined, 20).catch((error) => {
        taskErrorDetail.value = t('autoReverse.errors.loadTask', {
          message: error instanceof Error ? error.message : String(error),
        });
      }),
    );
  }

  await Promise.all(operations);
}

watch([autoReverseOptions, autoReverseConfig], () => {
  ensureComposeDefaults();
});

watch(browserMode, () => {
  syncBrowserMcpSelection(true);
});

watch(
  normalizedQueryTaskId,
  (nextTaskId) => {
    if (nextTaskId && nextTaskId !== currentTaskId.value) {
      void refreshTask(nextTaskId);
      return;
    }
    if (!nextTaskId && currentTaskId.value) {
      currentTaskId.value = '';
      taskStatus.value = null;
      taskResults.value = [];
      stopPolling();
      void loadArchives(undefined, 20);
    }
  },
);

onMounted(async () => {
  updateViewport();
  window.addEventListener('resize', updateViewport);
  await loadResources();
  const initialTaskId = normalizedQueryTaskId.value;
  if (initialTaskId) {
    await refreshTask(initialTaskId);
    return;
  }
  await loadArchives(undefined, 20);
});

onBeforeUnmount(() => {
  stopPolling();
  window.removeEventListener('resize', updateViewport);
});
</script>

<style scoped>
/* ── Root ── */
.arv {
  display: grid;
  gap: 16px;
}

/* ── Shared label ── */
.arv-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
}

/* ── Divider ── */
.arv-divider {
  border: none;
  height: 1px;
  background: var(--panel-border);
  margin: 8px 0;
}

/* ── Run params ── */
.arv-run-params {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.arv-run-param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.arv-run-param-row__label {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.arv-run-param-row__input {
  width: 88px;
  flex-shrink: 0;
}

/* ── Hero ── */
.arv-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 16px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
}

.arv-hero__lead {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.arv-hero__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--text-primary);
}

.arv-hero__subtitle {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--text-secondary);
  max-width: 56ch;
  word-break: break-word;
  overflow-wrap: break-word;
}

.arv-hero__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* ── Mobile switcher ── */
.arv-switcher {
  display: flex;
  justify-content: flex-start;
}

/* ── Workspace ── */
.arv-workspace {
  display: grid;
  grid-template-columns: minmax(0, 380px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.arv-workspace--mobile {
  grid-template-columns: 1fr;
}

/* ── Compose — unified surface ── */
.arv-compose {
  position: sticky;
  top: calc(var(--layout-header-height) + 16px);
}

.arv-compose__surface {
  display: grid;
  gap: 0;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out;
}

.arv-compose__surface:hover {
  border-color: var(--panel-border-strong);
}

.arv-compose__surface :deep(.url-card),
.arv-compose__surface :deep(.mode-seg) {
  border: none;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
  padding: 0;
}

.arv-compose__surface :deep(.url-card:focus-within) {
  border: none;
  box-shadow: none;
}

.arv-compose__surface :deep(.url-card:hover),
.arv-compose__surface :deep(.mode-seg:hover) {
  border-color: transparent;
}

.arv-compose__surface :deep(.agent-card) {
  border: none;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
  padding: 0;
}

.arv-compose__surface :deep(.agent-card:hover),
.arv-compose__surface :deep(.agent-card--active) {
  border-color: transparent;
  box-shadow: none;
}

/* ── Fold (collapsible sections) ── */
.arv-fold {
  border: none;
}

.arv-fold__toggle {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  cursor: pointer;
  user-select: none;
}

.arv-fold__toggle::-webkit-details-marker {
  display: none;
}

.arv-fold__label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.arv-fold__badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent-500);
  font-size: 0.68rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.arv-fold__chevron {
  margin-left: auto;
  width: 8px;
  height: 8px;
  border-right: 1.5px solid var(--text-muted);
  border-bottom: 1.5px solid var(--text-muted);
  transform: rotate(45deg);
  transition: transform 180ms ease;
  flex-shrink: 0;
}

.arv-fold[open] .arv-fold__chevron {
  transform: rotate(225deg);
}

.arv-fold__body {
  padding-top: 8px;
}

/* ── Agent tab switcher ── */
.arv-compose__agents {
  display: grid;
  gap: 10px;
  padding-top: 2px;
}

.arv-agent-switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 3px;
  border-radius: 12px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--panel-border);
}

.arv-agent-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 180ms ease-out;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.arv-agent-tab:hover {
  color: var(--text-primary);
  background: rgba(var(--accent-rgb), 0.06);
  transform: translateY(-0.5px);
}

.arv-agent-tab--active {
  color: var(--text-primary);
  background: var(--panel-bg);
  border-color: var(--panel-border);
  box-shadow: var(--shadow-xs);
  transform: none;
}

.arv-agent-tab__indicator {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: var(--success-500);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--success-500) 20%, transparent);
  flex-shrink: 0;
}

/* ── Submit ── */
.arv-compose__submit {
  margin-top: 10px;
  border-radius: 12px;
  min-height: 40px;
  font-weight: 700;
  font-size: 0.84rem;
}

/* ── Dashboard bar (merged summary) ── */
.arv-dash-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
}

.arv-dash-bar__lead {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  min-width: 0;
}

.arv-dash-bar__id {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-secondary);
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  cursor: default;
  transition: color 150ms ease-out, border-color 150ms ease-out;
}

.arv-dash-bar__id:hover {
  color: var(--accent-500);
  border-color: rgba(var(--accent-rgb), 0.24);
}

.arv-dash-bar__stat {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.arv-dash-bar__stat::before {
  content: '·';
  margin-right: 6px;
  color: var(--panel-border-strong);
}

.arv-dash-bar__time {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* ── Step summary rows ── */
.arv-step-summary {
  display: grid;
  gap: 4px;
}

.arv-step-row {
  display: grid;
  gap: 3px;
  padding: 6px 10px;
  border-radius: 8px;
  border-left: 3px solid var(--panel-border);
  background: var(--panel-bg-soft);
}

.arv-step-row--success {
  border-left-color: var(--success-500);
  background: color-mix(in srgb, var(--success-500) 4%, var(--panel-bg-soft));
}

.arv-step-row--running {
  border-left-color: var(--warning-500);
  background: color-mix(in srgb, var(--warning-500) 4%, var(--panel-bg-soft));
}

.arv-step-row--danger {
  border-left-color: var(--danger-500);
  background: color-mix(in srgb, var(--danger-500) 5%, var(--panel-bg-soft));
}

.arv-step-row__head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.arv-step-row__label {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 0.66rem;
  font-weight: 800;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.arv-step-row--success .arv-step-row__label { color: var(--success-500); }
.arv-step-row--running .arv-step-row__label { color: var(--warning-500); }
.arv-step-row--danger .arv-step-row__label { color: var(--danger-500); }

.arv-step-row__counts {
  color: var(--text-secondary);
  font-size: 0.74rem;
  line-height: 1.45;
}

.arv-step-row__err {
  margin: 0;
  color: var(--danger-500);
  font-size: 0.72rem;
  line-height: 1.45;
  word-break: break-word;
  opacity: 0.9;
}

/* ── Runtime fold ── */
.arv-runtime-fold {
  border: none;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out;
}

.arv-runtime-fold--dashboard {
  display: grid;
  gap: 10px;
}

.arv-runtime-fold:hover {
  border-color: var(--panel-border-strong);
}

.arv-runtime-fold__toggle {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.arv-runtime-fold__toggle::-webkit-details-marker {
  display: none;
}

.arv-runtime-fold__label {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.arv-runtime-fold__body {
  padding-top: 12px;
}

.arv-runtime-fold__body .arv-panel {
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0;
  border-radius: 0;
}

.arv-runtime-fold__body .arv-panel:hover {
  border-color: transparent;
}

/* ── Runtime ── */
.arv-runtime {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.arv-runtime__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

/* ── Shared panel ── */
.arv-panel {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--shadow-xs);
  transition: border-color 200ms ease-out;
}

.arv-panel:hover {
  border-color: var(--panel-border-strong);
}

.arv-panel--inspector {
  padding: 0;
  border: none;
  background: none;
  box-shadow: none;
}

.arv-panel--inspector:hover {
  border-color: transparent;
}

.arv-panel__head {
  display: grid;
  gap: 4px;
}

.arv-panel__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1.25;
}

.arv-panel__title--sm {
  font-size: 0.95rem;
}

.arv-panel__desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--text-secondary);
  max-width: 56ch;
  word-break: break-word;
  overflow-wrap: break-word;
}

.arv-panel__content {
  display: grid;
  gap: 16px;
}

/* ── Shared stack ── */
.arv-stack {
  display: grid;
  gap: 8px;
}

/* ── Responsive ── */
@media (max-width: 1199px) {
  .arv-runtime__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1023px) {
  .arv {
    gap: 12px;
  }

  .arv-workspace {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .arv-compose {
    position: static;
  }

  .arv-compose__surface {
    padding: 12px;
    border-radius: 14px;
  }

  .arv-runtime {
    gap: 10px;
  }

  .arv-hero {
    padding: 10px 14px;
    border-radius: 12px;
  }

  .arv-panel {
    padding: 12px;
    border-radius: 12px;
  }
}

@media (max-width: 767px) {
  .arv {
    gap: 10px;
  }

  .arv-hero {
    flex-direction: column;
    align-items: flex-start;
    padding: 10px 12px;
    border-radius: 12px;
  }

  .arv-hero__meta {
    width: 100%;
  }

  .arv-compose__surface {
    padding: 12px;
    border-radius: 12px;
  }

  .arv-panel {
    padding: 12px;
    border-radius: 12px;
    gap: 8px;
  }

  .arv-runtime__grid {
    gap: 8px;
  }
}
</style>
