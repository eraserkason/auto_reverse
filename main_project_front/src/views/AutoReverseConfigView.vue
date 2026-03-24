<template>
  <section class="config-view">
    <WorkspacePageHeader :title="t('autoReverseConfig.title')">
      <template #actions>
        <div class="config-view__header-actions">
          <WorkspaceRefreshButton
            :label="t('autoReverse.actions.reloadOptions')"
            :loading-label="t('autoReverse.actions.reloadOptionsLoading')"
            :aria-label="t('autoReverse.actions.reloadOptions')"
            :loading="loading"
            @click="loadConfig"
          />
          <n-button type="primary" :loading="saving" @click="saveConfig">
            {{ t('autoReverseConfig.actions.save') }}
          </n-button>
        </div>
      </template>
    </WorkspacePageHeader>

    <div class="config-nav-container">
      <n-tabs v-model:value="configActiveSection" type="segment" animated class="pro-tabs">
        <n-tab v-for="item in configSectionOptions" :key="item.key" :name="item.key">
          <template #default>
            <span class="config-tab-content">
              <span>{{ item.label }}</span>
              <span v-if="item.count" class="config-tab-count">{{ item.count }}</span>
            </span>
          </template>
        </n-tab>
      </n-tabs>
    </div>

    <n-alert v-if="message" :type="isError ? 'error' : 'success'" closable @after-leave="messageKey = ''">
      {{ message }}
    </n-alert>

    <!-- MCP -->
    <div v-if="configActiveSection === 'mcp'" class="config-workspace config-workspace--split">
      <WorkspaceSectionCard title="JSON Draft">
        <n-form-item label="JSON" label-placement="top">
          <n-input
            v-model:value="mcpJsonDraft"
            type="textarea"
            :autosize="{ minRows: 8, maxRows: 14 }"
            placeholder='{"mcpServers": { ... }}'
            class="code-input"
          />
        </n-form-item>
      </WorkspaceSectionCard>

      <WorkspaceSectionCard :title="t('autoReverseConfig.mcp.registryTitle')" :description="`${mcpEntries.length} ${t('autoReverseConfig.mcp.entriesUnit')}`">
        <div v-if="mcpEntries.length > 0" class="config-entry-list">
          <article v-for="entry in mcpEntries" :key="entry.name" class="config-entry-card">
            <div class="config-entry-card__head">
              <n-tag :type="entry.locked ? 'primary' : 'default'" size="tiny" round>
                {{ entry.locked ? 'Built-in' : 'Custom' }}
              </n-tag>
              <strong class="config-entry-card__name">{{ entry.name }}</strong>
              <button
                v-if="!entry.locked"
                type="button"
                class="config-entry-card__remove"
                @click="removeMcpEntry(entry.name)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                </svg>
              </button>
            </div>
            <div class="config-entry-card__details">
              <span class="config-entry-card__label">cmd</span>
              <code>{{ entry.command }} {{ entry.args.join(' ') }}</code>
            </div>
          </article>
        </div>
        <n-empty v-else />
      </WorkspaceSectionCard>
    </div>

    <!-- Skills -->
    <div v-else-if="configActiveSection === 'skills'" class="config-workspace config-workspace--single">
      <WorkspaceSectionCard :title="t('autoReverseConfig.skillsTab.title')">
        <div class="config-skills-head">
          <div class="config-skills-status">
            <n-tag :type="skillsEnabled ? 'success' : 'default'" size="small" round>
              {{ skillsEnabled ? t('autoReverseConfig.skillsTab.enabled') : t('autoReverseConfig.skillsTab.disabled') }}
            </n-tag>
            <span class="config-skills-count">{{ configSkills.length }}</span>
          </div>
          <n-switch v-model:value="skillsEnabled" size="medium" />
        </div>

        <div v-if="configSkills.length > 0" class="config-skills-grid">
          <article v-for="skill in configSkills" :key="skill" class="config-skill-chip">
            <span class="config-skill-chip__dot"></span>
            <span class="config-skill-chip__name">{{ skill }}</span>
            <button type="button" class="config-skill-chip__remove" @click="removeSkill(skill)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </article>
        </div>
        <n-empty v-else :description="t('autoReverseConfig.skillsTab.empty')" />

        <div class="config-skills-add">
          <n-input
            v-model:value="newSkillName"
            :placeholder="t('autoReverseConfig.skillsTab.addPlaceholder')"
            size="small"
            @keydown.enter="addSkill"
          />
          <n-button size="small" secondary :disabled="!newSkillName.trim()" @click="addSkill">
            {{ t('autoReverseConfig.skillsTab.addAction') }}
          </n-button>
        </div>
      </WorkspaceSectionCard>
    </div>

    <!-- Generator -->
    <div v-else-if="configActiveSection === 'generator'" class="config-workspace config-workspace--split">
      <WorkspaceSectionCard :title="t('autoReverseConfig.generator.title')">
        <div class="config-form-stack">
          <div class="config-form-head">
            <n-switch v-model:value="skillGenerator.enabled" size="medium">
              <template #checked>ON</template>
              <template #unchecked>OFF</template>
            </n-switch>
          </div>

          <n-form-item :label="t('autoReverseConfig.generator.nameLabel')">
            <n-input v-model:value="skillGeneratorTargetName" :placeholder="t('autoReverseConfig.generator.namePlaceholder')" />
          </n-form-item>

          <n-form-item :label="t('autoReverseConfig.generator.modelLabel')">
            <n-select v-model:value="skillGenerator.modelProfileKey" :options="generatorModelOptions" />
          </n-form-item>

          <n-form-item :label="t('autoReverseConfig.generator.promptLabel')">
            <n-input
              v-model:value="skillGeneratorPrompt"
              type="textarea"
              :autosize="{ minRows: 5, maxRows: 9 }"
              :placeholder="t('autoReverseConfig.generator.promptPlaceholder')"
            />
          </n-form-item>

          <n-button type="primary" block size="large" :loading="generatingSkill" @click="runSkillGeneration">
            {{ generatingSkill ? t('autoReverseConfig.generator.generating') : t('autoReverseConfig.generator.generate') }}
          </n-button>
        </div>
      </WorkspaceSectionCard>

      <WorkspaceSectionCard :title="t('autoReverseConfig.generator.previewTitle')">
        <div v-if="generatedSkillDraft" class="config-preview">
          <article v-for="skill in generatedSkillDraft.generatedSkills" :key="skill.path" class="config-preview__item">
            <strong>{{ skill.path }}</strong>
            <p>{{ skill.description }}</p>
          </article>
          <n-button type="primary" secondary block :disabled="!generatedSkillDraft.draftId" @click="applyGeneratedSkillDraft">
            {{ t('autoReverseConfig.generator.applyResult') }}
          </n-button>
        </div>
        <n-empty v-else :description="t('autoReverseConfig.generator.emptyPreview')" />
      </WorkspaceSectionCard>
    </div>

    <!-- Model Pool -->
    <div v-else-if="configActiveSection === 'model'" class="config-workspace config-workspace--single">
      <WorkspaceSectionCard :title="t('autoReverseConfig.model.title')" :description="t('autoReverseConfig.model.syncHint')">
        <div class="config-model-grid">
          <article v-for="card in providerCards" :key="card.provider" class="config-model-card">
            <div class="config-model-card__head">
              <strong>{{ card.label }}</strong>
              <div class="config-model-card__badges">
                <n-tag v-if="card.primary.hasApiKey" type="success" size="tiny" round>
                  {{ t('autoReverse.fields.profileConfigured') }}
                </n-tag>
                <n-tag :type="getModelSyncTagType(card.primary.syncStatus)" size="tiny" round>
                  {{ getModelSyncLabel(card.primary.syncStatus) }}
                </n-tag>
              </div>
            </div>
            <div class="config-model-card__fields">
              <n-form-item label="Base URL" :show-feedback="false">
                <n-input v-model:value="card.primary.baseUrl" placeholder="https://..." size="small" />
              </n-form-item>
              <n-form-item label="API Key" :show-feedback="false">
                <n-input
                  v-model:value="card.primary.apiKey"
                  type="password"
                  show-password-on="mousedown"
                  :placeholder="card.primary.hasApiKey ? '********' : 'Enter Key'"
                  size="small"
                />
              </n-form-item>
            </div>
            <div class="config-model-card__sync">
              <span class="config-model-card__sync-label">{{ t('autoReverseConfig.model.syncLabel') }}</span>
              <p>{{ getModelSyncMessage(card.primary.syncStatus, card.primary.syncMessage) }}</p>
            </div>
            <div class="config-model-card__model-list">
              <div class="config-model-card__model-summary">
                <div class="config-model-card__model-summary-copy">
                  <span class="config-model-card__model-summary-label">{{ t('autoReverseConfig.model.modelsLabel') }}</span>
                  <p>
                    {{
                      card.availableModels.length > 0
                        ? t('autoReverseConfig.model.modelsDiscovered', { count: card.availableModels.length })
                        : t('autoReverseConfig.model.modelsEmptySummary')
                    }}
                  </p>
                </div>
                <button
                  v-if="card.availableModels.length > 0"
                  type="button"
                  class="config-model-card__model-summary-action"
                  :aria-expanded="isProviderModelsExpanded(card.provider)"
                  @click="toggleProviderModels(card.provider)"
                >
                  <span>
                    {{
                      isProviderModelsExpanded(card.provider)
                        ? t('autoReverseConfig.model.collapseModels')
                        : t('autoReverseConfig.model.expandModels')
                    }}
                  </span>
                  <svg
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.7"
                    width="14"
                    height="14"
                    class="config-model-card__model-summary-icon"
                    :class="{ 'config-model-card__model-summary-icon--expanded': isProviderModelsExpanded(card.provider) }"
                  >
                    <path d="M4 6.5 8 10l4-3.5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
              <div v-if="card.availableModels.length > 0 && isProviderModelsExpanded(card.provider)" class="config-model-card__models">
                <n-tag v-for="m in card.availableModels" :key="m" size="tiny" round class="config-model-tag">{{ m }}</n-tag>
              </div>
            </div>
          </article>
        </div>
      </WorkspaceSectionCard>
    </div>

    <!-- Prompt -->
    <div v-else class="config-workspace config-workspace--single">
      <WorkspaceSectionCard :title="t('autoReverseConfig.prompt.title')">
        <div class="config-prompt-mode-switch">
          <button
            type="button"
            class="config-prompt-mode-btn"
            :class="{ 'config-prompt-mode-btn--active': promptBrowserMode === 'roxy' }"
            @click="promptBrowserMode = 'roxy'"
          >
            {{ t('autoReverseConfig.prompt.roxyMode') }}
          </button>
          <button
            type="button"
            class="config-prompt-mode-btn"
            :class="{ 'config-prompt-mode-btn--active': promptBrowserMode === 'standalone' }"
            @click="promptBrowserMode = 'standalone'"
          >
            {{ t('autoReverseConfig.prompt.standaloneMode') }}
          </button>
        </div>

        <n-tabs v-model:value="promptPane" type="segment" class="config-prompt-tabs">
          <n-tab-pane name="browser" tab="Browser Agent">
            <n-form-item :label="currentBrowserSystemPromptLabel">
              <n-input
                v-if="promptBrowserMode === 'roxy'"
                v-model:value="browserAgentSystemPrompt"
                type="textarea"
                :autosize="{ minRows: 12, maxRows: 20 }"
                :placeholder="currentBrowserSystemPromptPlaceholder"
                class="code-input"
              />
              <n-input
                v-else
                v-model:value="standaloneBrowserAgentSystemPrompt"
                type="textarea"
                :autosize="{ minRows: 12, maxRows: 20 }"
                :placeholder="currentBrowserSystemPromptPlaceholder"
                class="code-input"
              />
            </n-form-item>
            <n-form-item :label="currentBrowserUserPromptLabel">
              <n-input
                v-if="promptBrowserMode === 'roxy'"
                v-model:value="browserPrompt"
                type="textarea"
                :autosize="{ minRows: 8, maxRows: 16 }"
                :placeholder="currentBrowserUserPromptPlaceholder"
                class="code-input"
              />
              <n-input
                v-else
                v-model:value="standaloneBrowserPrompt"
                type="textarea"
                :autosize="{ minRows: 8, maxRows: 16 }"
                :placeholder="currentBrowserUserPromptPlaceholder"
                class="code-input"
              />
            </n-form-item>
          </n-tab-pane>
          <n-tab-pane name="analyse" tab="Analyse Agent">
            <n-form-item :label="t('autoReverseConfig.fields.analysePromptLabel')">
              <n-input
                v-model:value="analysePrompt"
                type="textarea"
                :autosize="{ minRows: 12, maxRows: 20 }"
                class="code-input"
              />
            </n-form-item>
          </n-tab-pane>
        </n-tabs>
      </WorkspaceSectionCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import {
  NButton,
  NTabs,
  NTab,
  NTabPane,
  NAlert,
  NFormItem,
  NInput,
  NTag,
  NSwitch,
  NSelect,
  NEmpty,
} from 'naive-ui';

import WorkspacePageHeader from '@/components/WorkspacePageHeader.vue';
import WorkspaceSectionCard from '@/components/WorkspaceSectionCard.vue';
import WorkspaceRefreshButton from '@/components/WorkspaceRefreshButton.vue';
import { useLocale } from '@/composables/useLocale';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { readJsonStorage, writeJsonStorage } from '@/utils/storage';
import {
  FRONTEND_DEFAULT_ANALYSE_PROMPT,
  saveAutoReverseConfig,
  applySkillDraftByApi,
  generateSkillByApi,
  type McpEntry,
  type ModelPoolEntry,
  type ModelProvider,
  type SkillGeneratorConfig,
  type SkillGenerationResult,
} from '@/views/api';

const { t } = useLocale();
const { autoReverseConfig, bootstrapWorkspaceData, reloadAutoReverseResources } = useWorkspaceData();

const CONFIG_SECTION_STORAGE_KEY = 'auto-reverse-config-active-section';
const PROMPT_PANE_STORAGE_KEY = 'auto-reverse-config-prompt-pane';
const PROMPT_BROWSER_MODE_STORAGE_KEY = 'auto-reverse-config-prompt-browser-mode';
const GENERATOR_MODEL_PROFILE_STORAGE_KEY = 'auto-reverse-config-generator-model-profile-key';

function readStoredConfigSection(): string {
  if (typeof window === 'undefined') {
    return 'mcp';
  }
  const raw = window.localStorage.getItem(CONFIG_SECTION_STORAGE_KEY)?.trim() ?? '';
  return ['mcp', 'skills', 'generator', 'model', 'prompt'].includes(raw) ? raw : 'mcp';
}

function readStoredPromptPane(): 'browser' | 'analyse' {
  if (typeof window === 'undefined') {
    return 'browser';
  }
  return window.localStorage.getItem(PROMPT_PANE_STORAGE_KEY) === 'analyse' ? 'analyse' : 'browser';
}

function readStoredPromptBrowserMode(): 'roxy' | 'standalone' {
  if (typeof window === 'undefined') {
    return 'roxy';
  }
  return window.localStorage.getItem(PROMPT_BROWSER_MODE_STORAGE_KEY) === 'standalone' ? 'standalone' : 'roxy';
}

function readStoredGeneratorModelProfileKey(): string {
  return String(readJsonStorage<string | null>(GENERATOR_MODEL_PROFILE_STORAGE_KEY, '') ?? '').trim();
}

const configActiveSection = ref(readStoredConfigSection());
const promptPane = ref<'browser' | 'analyse'>(readStoredPromptPane());
const loading = ref(false);
const saving = ref(false);
const isError = ref(false);
const messageKey = ref('');
const messageDetail = ref('');

const mcpEntries = ref<McpEntry[]>([]);
const mcpJsonDraft = ref('');
const configSkills = ref<string[]>([]);
const skillsEnabled = ref(false);
const newSkillName = ref('');
const skillGenerator = ref<SkillGeneratorConfig>({} as SkillGeneratorConfig);
const skillGeneratorTargetName = ref('');
const skillGeneratorPrompt = ref('');
const generatedSkillDraft = ref<SkillGenerationResult | null>(null);
const generatingSkill = ref(false);
const browserAgentSystemPrompt = ref('');
const standaloneBrowserAgentSystemPrompt = ref('');
const browserPrompt = ref('');
const standaloneBrowserPrompt = ref('');
const analysePrompt = ref('');
const promptBrowserMode = ref<'roxy' | 'standalone'>(readStoredPromptBrowserMode());
const modelPool = ref<ModelPoolEntry[]>([]);
const expandedModelProviders = ref<Partial<Record<ModelProvider, boolean>>>({});

function resolveGeneratorModelProfileKey(
  cfg: {
    skillGenerator: { modelProfileKey: string };
    modelProfiles: ReadonlyArray<{ key: string; enabled?: boolean }>;
  },
  preferredKey: string,
): string {
  const availableKeys = cfg.modelProfiles
    .filter((item) => item.enabled !== false)
    .map((item) => String(item.key ?? '').trim())
    .filter(Boolean);
  const normalizedPreferredKey = String(preferredKey ?? '').trim();
  if (normalizedPreferredKey && availableKeys.includes(normalizedPreferredKey)) {
    return normalizedPreferredKey;
  }
  const configuredKey = String(cfg.skillGenerator.modelProfileKey ?? '').trim();
  if (configuredKey && availableKeys.includes(configuredKey)) {
    return configuredKey;
  }
  return availableKeys[0] ?? '';
}

const providerOrder: ModelProvider[] = ['deepseek', 'chatgpt', 'newapi', 'claude', 'gemini'];

const configSectionOptions = computed(() => [
  { key: 'mcp', label: 'MCP', count: mcpEntries.value.length },
  { key: 'skills', label: 'Skills', count: configSkills.value.length },
  { key: 'generator', label: t('autoReverseConfig.tabs.generator'), count: generatedSkillDraft.value?.generatedSkills.length ?? 0 },
  { key: 'model', label: t('autoReverseConfig.tabs.model'), count: providerOrder.length },
  { key: 'prompt', label: 'Prompt', count: 2 },
]);

const providerCards = computed(() =>
  providerOrder.map((p) => {
    const primary = modelPool.value.find((item) => item.provider === p) || {
      provider: p,
      label: p.toUpperCase(),
      baseUrl: '',
      apiKey: '',
      apiKeyMasked: '',
      hasApiKey: false,
      availableModels: [],
      defaultModel: '',
      syncStatus: 'idle',
      syncMessage: '',
      enabled: true,
      locked: false,
    };
    return { provider: p, label: p.toUpperCase(), primary, availableModels: primary.availableModels || [] };
  }),
);

function isProviderModelsExpanded(provider: ModelProvider): boolean {
  return Boolean(expandedModelProviders.value[provider]);
}

function toggleProviderModels(provider: ModelProvider): void {
  expandedModelProviders.value = {
    ...expandedModelProviders.value,
    [provider]: !expandedModelProviders.value[provider],
  };
}

function getModelSyncTagType(status?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  switch (String(status || '').trim()) {
    case 'ready':
      return 'success';
    case 'sync_failed':
    case 'invalid_config':
      return 'error';
    case 'missing_api_key':
    case 'empty':
    case 'unsupported':
      return 'warning';
    case 'syncing':
      return 'info';
    default:
      return 'default';
  }
}

function getModelSyncLabel(status?: string): string {
  switch (String(status || '').trim()) {
    case 'ready':
      return t('autoReverseConfig.model.statusReady');
    case 'missing_api_key':
      return t('autoReverseConfig.model.statusMissingApiKey');
    case 'sync_failed':
      return t('autoReverseConfig.model.statusSyncFailed');
    case 'invalid_config':
      return t('autoReverseConfig.model.statusInvalidConfig');
    case 'empty':
      return t('autoReverseConfig.model.statusEmpty');
    case 'unsupported':
      return t('autoReverseConfig.model.statusUnsupported');
    case 'syncing':
      return t('common.status.syncing');
    default:
      return t('autoReverseConfig.model.statusIdle');
  }
}

function getModelSyncMessage(status?: string, message?: string): string {
  const normalizedMessage = String(message || '').trim();
  if (normalizedMessage) {
    return normalizedMessage;
  }
  if (String(status || '').trim() === 'idle') {
    return t('autoReverseConfig.model.syncMessageIdle');
  }
  return getModelSyncLabel(status);
}

const generatorModelOptions = computed(() => {
  const cfg = autoReverseConfig.value;
  if (!cfg?.modelProfiles?.length) {
    return modelPool.value
      .filter((entry) => entry.hasApiKey && entry.availableModels.length > 0)
      .flatMap((entry) =>
        entry.availableModels.map((model) => ({
          label: `${entry.label} / ${model}`,
          value: `${entry.provider}:${model}`,
        })),
      );
  }
  return cfg.modelProfiles
    .filter((profile) => profile.enabled !== false)
    .map((profile) => ({
      label: profile.label,
      value: profile.key,
    }));
});

const message = computed(() =>
  messageKey.value ? t(`autoReverseConfig.messages.${messageKey.value}`, { message: messageDetail.value }) : '',
);

const buildStoredGeneratedSkillDraft = (): SkillGenerationResult | null => {
  const targetName = skillGenerator.value.lastTargetName.trim();
  const draftId = skillGenerator.value.lastDraftId.trim();
  const generatedSkills = skillGenerator.value.lastGeneratedSkills.map((item) => ({
    ...item,
    files: { ...item.files },
  }));
  if (generatedSkills.length === 0) {
    return null;
  }
  return {
    draftId,
    rootPath: targetName || generatedSkills[0]?.path || '',
    generatedSkills,
    saved: true,
    usedModel: {
      provider: '',
      model: '',
      profileKey: '',
    },
    warnings: [],
  };
};

const currentBrowserSystemPromptLabel = computed(() =>
  promptBrowserMode.value === 'roxy'
    ? t('autoReverseConfig.fields.browserAgentSystemPromptLabel')
    : t('autoReverseConfig.prompt.standaloneSystemPromptLabel'),
);

const currentBrowserSystemPromptPlaceholder = computed(() =>
  promptBrowserMode.value === 'roxy'
    ? t('autoReverseConfig.fields.browserAgentSystemPromptPlaceholder')
    : t('autoReverseConfig.fields.standaloneBrowserAgentSystemPromptPlaceholder'),
);

const currentBrowserUserPromptLabel = computed(() =>
  promptBrowserMode.value === 'roxy'
    ? t('autoReverseConfig.fields.browserPromptLabel')
    : t('autoReverseConfig.prompt.standaloneUserPromptLabel'),
);

const currentBrowserUserPromptPlaceholder = computed(() =>
  promptBrowserMode.value === 'roxy'
    ? t('autoReverseConfig.fields.browserPromptPlaceholder')
    : t('autoReverseConfig.fields.standaloneBrowserPromptPlaceholder'),
);

const loadConfig = async () => {
  loading.value = true;
  try {
    await bootstrapWorkspaceData({ force: true });
    applyLocalConfig();
  } finally {
    loading.value = false;
  }
};

const applyLocalConfig = () => {
  const cfg = autoReverseConfig.value;
  if (!cfg) return;
  const resolvedGeneratorModelProfileKey = resolveGeneratorModelProfileKey(
    cfg,
    readStoredGeneratorModelProfileKey(),
  );
  mcpEntries.value = cfg.mcpEntries.map((entry) => ({
    ...entry,
    args: [...entry.args],
    env: { ...entry.env },
  }));
  configSkills.value = [...(cfg.skills ?? [])];
  skillsEnabled.value = cfg.skillsEnabled ?? false;
  skillGenerator.value = {
    ...cfg.skillGenerator,
    modelProfileKey: resolvedGeneratorModelProfileKey,
    referenceSkillNames: [...cfg.skillGenerator.referenceSkillNames],
    lastGeneratedSkills: cfg.skillGenerator.lastGeneratedSkills.map((item) => ({
      ...item,
      files: { ...item.files },
    })),
  };
  skillGeneratorTargetName.value = cfg.skillGenerator.lastTargetName;
  skillGeneratorPrompt.value = cfg.skillGenerator.lastPrompt;
  generatedSkillDraft.value = buildStoredGeneratedSkillDraft();
  browserAgentSystemPrompt.value = cfg.browserAgentSystemPrompt;
  standaloneBrowserAgentSystemPrompt.value = cfg.standaloneBrowserAgentSystemPrompt;
  browserPrompt.value = cfg.browserPrompt;
  standaloneBrowserPrompt.value = cfg.standaloneBrowserPrompt;
  analysePrompt.value = cfg.analysePrompt || FRONTEND_DEFAULT_ANALYSE_PROMPT;
  modelPool.value = cfg.modelPool.map((entry) => ({
    ...entry,
    availableModels: [...entry.availableModels],
  }));
  expandedModelProviders.value = {};
  syncMcpJson();
};

const syncMcpJson = () => {
  mcpJsonDraft.value = JSON.stringify(
    { mcpServers: Object.fromEntries(mcpEntries.value.map((e) => [e.name, { command: e.command, args: e.args, env: e.env }])) },
    null,
    2,
  );
};

const parseMcpJsonDraft = (): McpEntry[] => {
  let parsed: unknown;
  try {
    parsed = JSON.parse(mcpJsonDraft.value || '{}');
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`MCP JSON Draft 不是合法 JSON：${detail}`);
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('MCP JSON Draft 顶层必须是对象，且包含 mcpServers 字段');
  }

  const root = parsed as Record<string, unknown>;
  const mcpServers = root.mcpServers;
  if (!mcpServers || typeof mcpServers !== 'object' || Array.isArray(mcpServers)) {
    throw new Error('MCP JSON Draft 必须包含对象类型的 mcpServers 字段');
  }

  return Object.entries(mcpServers as Record<string, unknown>).map(([name, rawConfig]) => {
    const normalizedName = String(name).trim();
    if (!normalizedName) {
      throw new Error('MCP 名称不能为空');
    }
    if (!rawConfig || typeof rawConfig !== 'object' || Array.isArray(rawConfig)) {
      throw new Error(`MCP ${normalizedName} 的配置必须是对象`);
    }

    const config = rawConfig as Record<string, unknown>;
    const command = typeof config.command === 'string' ? config.command.trim() : '';
    if (!command) {
      throw new Error(`MCP ${normalizedName} 的 command 不能为空`);
    }

    const rawArgs = config.args;
    if (rawArgs !== undefined && !Array.isArray(rawArgs)) {
      throw new Error(`MCP ${normalizedName} 的 args 必须是数组`);
    }
    const args = (Array.isArray(rawArgs) ? rawArgs : [])
      .map((item) => String(item).trim())
      .filter(Boolean);

    const rawEnv = config.env;
    if (rawEnv !== undefined && (!rawEnv || typeof rawEnv !== 'object' || Array.isArray(rawEnv))) {
      throw new Error(`MCP ${normalizedName} 的 env 必须是对象`);
    }
    const env = Object.fromEntries(
      Object.entries((rawEnv as Record<string, unknown>) ?? {})
        .map(([key, value]) => [String(key).trim(), String(value)])
        .filter(([key]) => Boolean(key)),
    );

    return {
      name: normalizedName,
      command,
      args,
      env,
      status: 'configured',
      locked: false,
    };
  });
};

const removeMcpEntry = (name: string) => {
  mcpEntries.value = mcpEntries.value.filter((e) => e.name !== name);
  syncMcpJson();
};

const addSkill = () => {
  const name = newSkillName.value.trim();
  if (!name || configSkills.value.includes(name)) return;
  configSkills.value.push(name);
  newSkillName.value = '';
};

const removeSkill = (name: string) => {
  configSkills.value = configSkills.value.filter((s) => s !== name);
};

const runSkillGeneration = async () => {
  generatingSkill.value = true;
  try {
    const res = await generateSkillByApi({
      targetName: skillGeneratorTargetName.value,
      prompt: skillGeneratorPrompt.value,
      modelProfileKey: skillGenerator.value.modelProfileKey,
      referenceSkillNames: [],
      temperature: 0.2,
    });
    generatedSkillDraft.value = res;
    skillGenerator.value = {
      ...skillGenerator.value,
      lastTargetName: skillGeneratorTargetName.value.trim(),
      lastPrompt: skillGeneratorPrompt.value,
      lastDraftId: res.draftId,
      lastGeneratedSkills: res.generatedSkills.map((item) => ({
        ...item,
        files: { ...item.files },
      })),
    };
  } finally {
    generatingSkill.value = false;
  }
};

const applyGeneratedSkillDraft = async () => {
  if (!generatedSkillDraft.value?.draftId) return;
  await applySkillDraftByApi(generatedSkillDraft.value.draftId);
  await loadConfig();
};

const saveConfig = async () => {
  saving.value = true;
  try {
    const parsedMcpEntries = parseMcpJsonDraft();
    mcpEntries.value = parsedMcpEntries;
    await saveAutoReverseConfig({
      ...autoReverseConfig.value,
      mcpEntries: parsedMcpEntries,
      skills: configSkills.value,
      skillsEnabled: skillsEnabled.value,
      skillGenerator: skillGenerator.value,
      browserAgentSystemPrompt: browserAgentSystemPrompt.value,
      standaloneBrowserAgentSystemPrompt: standaloneBrowserAgentSystemPrompt.value,
      browserPrompt: browserPrompt.value,
      standaloneBrowserPrompt: standaloneBrowserPrompt.value,
      analysePrompt: analysePrompt.value,
      modelPool: modelPool.value,
    } as any);
    await reloadAutoReverseResources({ force: true, silent: true });
    applyLocalConfig();
    isError.value = false;
    messageKey.value = 'saveSuccess';
    messageDetail.value = '';
  } catch (e: unknown) {
    isError.value = true;
    messageKey.value = 'saveFailed';
    messageDetail.value = e instanceof Error ? e.message : String(e);
  } finally {
    saving.value = false;
  }
};

watch(configActiveSection, (value) => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(CONFIG_SECTION_STORAGE_KEY, value);
});

watch(promptPane, (value) => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(PROMPT_PANE_STORAGE_KEY, value);
});

watch(promptBrowserMode, (value) => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(PROMPT_BROWSER_MODE_STORAGE_KEY, value);
});

watch(
  () => skillGenerator.value.modelProfileKey,
  (value) => {
    writeJsonStorage(GENERATOR_MODEL_PROFILE_STORAGE_KEY, String(value ?? '').trim());
  },
);

onMounted(loadConfig);
</script>

<style scoped>
.config-view {
  display: grid;
  gap: 18px;
}

.config-view__header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.config-view__header-actions > * {
  min-width: 0;
}

.config-nav-container {
  background: var(--panel-bg-soft);
  padding: 6px;
  border-radius: 16px;
  border: 1px solid var(--panel-border);
}

.pro-tabs :deep(.n-tabs-rail) {
  background: color-mix(in srgb, var(--bg-canvas) 60%, transparent);
  border-radius: 12px;
  padding: 3px;
}

.pro-tabs :deep(.n-tabs-tab) {
  border-radius: 10px;
  font-weight: 600;
}

.config-tab-content {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.config-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.14);
  color: var(--accent-500);
  font-size: 0.66rem;
  font-weight: 800;
  line-height: 1;
}

.config-workspace {
  display: grid;
  gap: 18px;
}

.config-workspace--split {
  grid-template-columns: minmax(0, 1fr) minmax(300px, 1fr);
}

.config-workspace--single {
  grid-template-columns: 1fr;
}

/* MCP entries */
.config-entry-list {
  display: grid;
  gap: 8px;
}

.config-entry-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  transition: border-color var(--transition-base);
}

.config-entry-card:hover {
  border-color: var(--panel-border-strong);
}

.config-entry-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-entry-card__name {
  font-family: var(--font-mono);
  font-size: 0.86rem;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-entry-card__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  font: inherit;
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.config-entry-card__remove:hover {
  color: var(--danger-500);
  background: color-mix(in srgb, var(--danger-500) 10%, transparent);
  border-color: color-mix(in srgb, var(--danger-500) 20%, transparent);
}

.config-entry-card__details {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.config-entry-card__label {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.config-entry-card__details code {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

/* Skills */
.config-skills-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.config-skills-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-skills-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--bg-accent-soft);
  color: var(--accent-500);
  font-size: 0.72rem;
  font-weight: 800;
}

.config-skills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.config-skill-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px 0 12px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  transition: border-color var(--transition-base);
}

.config-skill-chip:hover {
  border-color: var(--panel-border-strong);
}

.config-skill-chip__dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--accent-500);
}

.config-skill-chip__name {
  font-family: var(--font-mono);
  font-size: 0.78rem;
}

.config-skill-chip__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  font: inherit;
  transition: all var(--transition-base);
}

.config-skill-chip__remove:hover {
  color: var(--danger-500);
  background: color-mix(in srgb, var(--danger-500) 12%, transparent);
}

.config-skills-add {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Generator */
.config-form-stack {
  display: grid;
  gap: 16px;
}

.config-form-head {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
}

.config-preview {
  display: grid;
  gap: 10px;
}

.config-preview__item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.config-preview__item strong {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.84rem;
}

.config-preview__item p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

/* Model */
.config-model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(320px, 100%), 1fr));
  gap: 14px;
}

.config-model-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  transition: border-color var(--transition-base), box-shadow var(--transition-base), transform var(--transition-fast);
}

.config-model-card:hover {
  border-color: var(--panel-border-strong);
  box-shadow: var(--shadow-xs);
  transform: translateY(-1px);
}

.config-model-card__head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 8px 12px;
  min-height: 44px;
}

.config-model-card__head strong {
  font-size: 1rem;
  letter-spacing: -0.02em;
  line-height: 1.35;
  min-width: 0;
}

.config-model-card__badges {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 4px;
  min-height: 44px;
}

.config-model-card__fields {
  display: grid;
  gap: 8px;
}

.config-model-card__sync {
  display: grid;
  gap: 5px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: color-mix(in srgb, var(--panel-bg-soft) 82%, transparent);
}

.config-model-card__sync-label {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.config-model-card__sync p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.55;
}

.config-model-card__model-list {
  display: grid;
  gap: 8px;
}

.config-model-card__model-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px 12px;
  min-height: 54px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: color-mix(in srgb, var(--panel-bg-soft) 90%, transparent);
}

.config-model-card__model-summary-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.config-model-card__model-summary-label {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.config-model-card__model-summary-copy p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
}

.config-model-card__model-summary-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--accent-500);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: color var(--transition-base);
}

.config-model-card__model-summary-action:hover {
  color: var(--accent-400);
}

.config-model-card__model-summary-icon {
  transition: transform var(--transition-base);
}

.config-model-card__model-summary-icon--expanded {
  transform: rotate(180deg);
}

.config-model-card__models {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.config-model-tag {
  font-family: var(--font-mono);
  font-size: 0.72rem;
}

/* Prompt */
.config-prompt-mode-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 3px;
  border-radius: 12px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--panel-border);
  margin-bottom: 12px;
}

.config-prompt-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 7px 12px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 180ms ease-out;
}

.config-prompt-mode-btn:hover {
  color: var(--text-primary);
}

.config-prompt-mode-btn--active {
  color: var(--text-primary);
  background: var(--panel-bg);
  border-color: var(--panel-border);
  box-shadow: var(--shadow-xs);
}

.config-prompt-tabs :deep(.n-tabs-nav) {
  margin-bottom: 18px;
}

.code-input :deep(.n-input-wrapper) {
  background: var(--n-color-embedded);
}

.code-input :deep(.n-input__textarea-el),
.code-input :deep(textarea) {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  background: transparent;
}

@media (max-width: 1100px) {
  .config-workspace--split {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .config-view,
  .config-workspace {
    gap: 14px;
  }

  .config-nav-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    -ms-overflow-style: none;
    padding: 4px;
  }

  .config-nav-container::-webkit-scrollbar {
    display: none;
    height: 0;
  }

  .pro-tabs :deep(.n-tabs-rail) {
    width: max-content !important;
    min-width: 100%;
  }

  .pro-tabs :deep(.n-tabs-tab-wrapper) {
    flex: none !important;
    min-width: 82px;
  }

  .config-model-grid {
    grid-template-columns: 1fr;
  }

  .config-skills-add {
    flex-direction: column;
    align-items: stretch;
  }

  .config-entry-card__head,
  .config-skills-head,
  .config-model-card__head {
    grid-template-columns: minmax(0, 1fr);
    align-items: flex-start;
  }

  .config-model-card__head {
    min-height: unset;
  }

  .config-entry-card__details {
    flex-direction: column;
    align-items: flex-start;
  }

  .config-entry-card__details code {
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .config-prompt-mode-switch {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 540px) {
  .config-view__header-actions {
    width: 100%;
  }

  .config-view__header-actions :deep(.workspace-refresh-btn),
  .config-view__header-actions :deep(.n-button) {
    width: 100%;
  }

  .pro-tabs :deep(.n-tabs-tab-wrapper) {
    min-width: 72px;
  }

  .pro-tabs :deep(.n-tabs-tab) {
    padding: 0 10px !important;
    font-size: 0.75rem !important;
  }

  .config-tab-content {
    gap: 4px;
  }

  .config-tab-count {
    font-size: 0.6rem;
    min-width: 16px;
    height: 16px;
  }

  .config-skill-chip {
    max-width: 100%;
    min-height: 32px;
    height: auto;
    align-items: flex-start;
    padding: 6px 10px 6px 12px;
  }

  .config-skill-chip__name {
    overflow-wrap: anywhere;
  }

  .config-model-card__badges {
    align-items: flex-start;
    min-height: unset;
  }

  .config-model-card__model-summary {
    grid-template-columns: minmax(0, 1fr);
  }

  .config-model-card__model-summary-action {
    justify-self: flex-start;
  }
}
</style>
