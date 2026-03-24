<template>
  <section class="settings-view">
    <WorkspacePageHeader
      :title="t('setting.title')"
      :tags="settingsTags"
    />

    <div class="settings-shell">
      <WorkspaceSectionCard>
        <template #header>
          <button
            type="button"
            class="settings-section-header"
            :aria-expanded="String(preferencesOpen)"
            @click="isSettingsMobile && (preferencesOpen = !preferencesOpen)"
          >
            <span class="settings-section-header__title">{{ t('setting.preferences.title') }}</span>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              width="16"
              height="16"
              class="settings-section-header__chevron"
              :class="{ 'is-collapsed': !preferencesOpen }"
            >
              <path d="M18 15l-6-6-6 6" />
            </svg>
          </button>
        </template>
        <div v-show="preferencesOpen" class="settings-preferences-grid">
          <article class="settings-choice-card">
            <div class="settings-choice-card__head">
              <span class="settings-choice-card__eyebrow">{{ t('setting.fields.themeLabel') }}</span>
              <strong>{{ isLightMode ? t('setting.preferences.lightWorkspace') : t('setting.preferences.darkWorkspace') }}</strong>
            </div>

            <div class="settings-theme-grid">
              <button
                type="button"
                class="settings-theme-option"
                :class="{ 'is-active': isLightMode }"
                @click="setTheme(true)"
              >
                <span class="settings-theme-option__preview settings-theme-option__preview--light">
                  <span class="settings-theme-option__preview-bar"></span>
                  <span class="settings-theme-option__preview-bar settings-theme-option__preview-bar--short"></span>
                </span>
                <span class="settings-theme-option__label">{{ t('setting.preferences.lightLabel') }}</span>
              </button>
              <button
                type="button"
                class="settings-theme-option"
                :class="{ 'is-active': !isLightMode }"
                @click="setTheme(false)"
              >
                <span class="settings-theme-option__preview settings-theme-option__preview--dark">
                  <span class="settings-theme-option__preview-bar"></span>
                  <span class="settings-theme-option__preview-bar settings-theme-option__preview-bar--short"></span>
                </span>
                <span class="settings-theme-option__label">{{ t('setting.preferences.darkLabel') }}</span>
              </button>
            </div>
          </article>

          <article class="settings-choice-card">
            <div class="settings-choice-card__head">
              <span class="settings-choice-card__eyebrow">{{ t('setting.fields.localeLabel') }}</span>
              <strong>{{ locale === 'zh-CN' ? '简体中文' : 'English' }}</strong>
            </div>

            <div class="settings-locale-grid">
              <button
                type="button"
                class="settings-locale-option"
                :class="{ 'is-active': locale === option.value }"
                v-for="option in localeOptions"
                :key="option.value"
                @click="setLocale(option.value)"
              >
                <span class="settings-locale-option__label">{{ option.label }}</span>
                <span class="settings-locale-option__short">{{ option.shortLabel }}</span>
              </button>
            </div>
          </article>
        </div>
      </WorkspaceSectionCard>

      <div class="settings-secondary-grid">
        <WorkspaceSectionCard>
          <template #header>
            <button
              type="button"
              class="settings-section-header"
              :aria-expanded="String(accountOpen)"
              @click="isSettingsMobile && (accountOpen = !accountOpen)"
            >
              <span class="settings-section-header__title">{{ t('setting.account.title') }}</span>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                width="16"
                height="16"
                class="settings-section-header__chevron"
                :class="{ 'is-collapsed': !accountOpen }"
              >
                <path d="M18 15l-6-6-6 6" />
              </svg>
            </button>
          </template>
          <div v-show="accountOpen" class="settings-info-stack">
            <div class="settings-info-row">
              <div>
                <span class="settings-info-row__label">{{ t('setting.account.currentUser') }}</span>
                <strong class="settings-info-row__value">{{ currentUser?.displayName || currentUser?.username || 'Guest' }}</strong>
              </div>
              <n-button size="small" quaternary type="error" @click="handleLogout">{{ t('setting.account.logout') }}</n-button>
            </div>

            <div class="settings-password-form">
              <button
                type="button"
                class="settings-password-toggle"
                :aria-expanded="String(showPasswordForm)"
                @click="showPasswordForm = !showPasswordForm"
              >
                <span>{{ t('setting.account.changePassword') }}</span>
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  width="14"
                  height="14"
                  class="settings-section-header__chevron"
                  :class="{ 'is-collapsed': !showPasswordForm }"
                >
                  <path d="M18 15l-6-6-6 6" />
                </svg>
              </button>
              <template v-if="showPasswordForm">
                <n-input
                  v-model:value="newPassword"
                  type="password"
                  name="new-password"
                  autocomplete="new-password"
                  show-password-on="mousedown"
                  :placeholder="t('setting.account.newPasswordPlaceholder')"
                  size="small"
                />
                <n-input
                  v-model:value="confirmPassword"
                  type="password"
                  name="confirm-password"
                  autocomplete="new-password"
                  show-password-on="mousedown"
                  :placeholder="t('setting.account.confirmPasswordPlaceholder')"
                  size="small"
                  @keydown.enter="handleChangePassword"
                />
                <n-button
                  size="small"
                  type="primary"
                  :loading="changingPassword"
                  :disabled="!newPassword.trim() || newPassword !== confirmPassword"
                  @click="handleChangePassword"
                >
                  {{ t('setting.account.savePassword') }}
                </n-button>
                <p v-if="passwordMessage" class="settings-password-msg" :class="{ 'settings-password-msg--error': passwordError }">
                  {{ passwordMessage }}
                </p>
              </template>
            </div>
          </div>
        </WorkspaceSectionCard>

        <WorkspaceSectionCard>
          <template #header>
            <button
              type="button"
              class="settings-section-header"
              :aria-expanded="String(systemOpen)"
              @click="isSettingsMobile && (systemOpen = !systemOpen)"
            >
              <span class="settings-section-header__title">{{ t('setting.system.title') }}</span>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                width="16"
                height="16"
                class="settings-section-header__chevron"
                :class="{ 'is-collapsed': !systemOpen }"
              >
                <path d="M18 15l-6-6-6 6" />
              </svg>
            </button>
          </template>
          <div v-show="systemOpen" class="settings-system-card">
            <div class="settings-system-card__head">
              <span class="settings-system-card__title">{{ t('setting.system.appName') }}</span>
              <n-tag size="small" type="primary" round>v{{ packageMeta.version }}</n-tag>
            </div>
            <p class="settings-system-card__copy">{{ t('setting.system.copy') }}</p>
            <n-button block quaternary size="small">{{ t('setting.system.checkUpdate') }}</n-button>
          </div>
        </WorkspaceSectionCard>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { NButton, NInput, NTag } from 'naive-ui';

import packageMeta from '../../package.json';
import WorkspacePageHeader, { type WorkspaceHeaderTag } from '@/components/WorkspacePageHeader.vue';
import WorkspaceSectionCard from '@/components/WorkspaceSectionCard.vue';
import { useAuth } from '@/composables/useAuth';
import { useLocale } from '@/composables/useLocale';
import { useTheme } from '@/composables/useTheme';
import { ROUTE_PATHS } from '@/constants/routes';
import { changePassword } from '@/views/api';

const router = useRouter();
const { currentUser, logout } = useAuth();
const { t, locale, localeOptions, setLocale } = useLocale();
const { isLightMode, setTheme } = useTheme();

const newPassword = ref('');
const confirmPassword = ref('');
const changingPassword = ref(false);
const passwordMessage = ref('');
const passwordError = ref(false);
const showPasswordForm = ref(false);

const isSettingsMobile = ref(false);
const preferencesOpen = ref(true);
const accountOpen = ref(true);
const systemOpen = ref(true);

function handleSettingsResize(): void {
  const wasMobile = isSettingsMobile.value;
  isSettingsMobile.value = window.innerWidth <= 860;
  if (wasMobile && !isSettingsMobile.value) {
    // Switching to desktop: expand all
    preferencesOpen.value = true;
    accountOpen.value = true;
    systemOpen.value = true;
    showPasswordForm.value = false;
  } else if (!wasMobile && isSettingsMobile.value) {
    // Switching to mobile (or first mount on mobile): collapse preferences
    preferencesOpen.value = false;
  }
}

onMounted(() => {
  handleSettingsResize();
  window.addEventListener('resize', handleSettingsResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleSettingsResize);
});

const settingsTags = computed<WorkspaceHeaderTag[]>(() => [
  { label: locale.value === 'zh-CN' ? '简体中文' : 'English', type: 'default' },
  { label: isLightMode ? 'Light' : 'Dark', type: 'primary' },
]);

function handleLogout(): void {
  logout();
  router.push(ROUTE_PATHS.LOGIN);
}

async function handleChangePassword(): Promise<void> {
  const pwd = newPassword.value.trim();
  if (!pwd || pwd !== confirmPassword.value) return;
  if (!currentUser.value?.id) {
    passwordError.value = true;
    passwordMessage.value = t('setting.account.noUserError');
    return;
  }
  changingPassword.value = true;
  passwordMessage.value = '';
  passwordError.value = false;
  try {
    await changePassword(currentUser.value.id, pwd);
    passwordMessage.value = t('setting.account.passwordChanged');
    passwordError.value = false;
    newPassword.value = '';
    confirmPassword.value = '';
  } catch (error) {
    passwordError.value = true;
    passwordMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    changingPassword.value = false;
  }
}
</script>

<style scoped>
.settings-view {
  display: grid;
  gap: 18px;
  max-width: 1040px;
  margin: 0 auto;
}

.settings-shell,
.settings-secondary-grid {
  display: grid;
  gap: 18px;
}

.settings-secondary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.settings-preferences-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.settings-choice-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.settings-choice-card:hover {
  border-color: var(--panel-border-strong);
  box-shadow: var(--shadow-xs);
}

.settings-choice-card__head {
  display: grid;
  gap: 4px;
}

.settings-choice-card__eyebrow {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.settings-choice-card__head strong {
  color: var(--text-primary);
  font-size: 1rem;
  letter-spacing: -0.02em;
}

.settings-theme-grid,
.settings-locale-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.settings-theme-option,
.settings-locale-option {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  border: 2px solid var(--panel-border);
  background: var(--panel-bg);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: border-color var(--transition-base), box-shadow var(--transition-base), transform var(--transition-fast), background-color var(--transition-base);
}

.settings-theme-option:hover,
.settings-locale-option:hover {
  border-color: var(--panel-border-strong);
  box-shadow: var(--shadow-xs);
  transform: translateY(-2px);
}

.settings-theme-option.is-active,
.settings-locale-option.is-active {
  border-color: var(--accent-500);
  background: var(--panel-accent-bg);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.settings-theme-option:focus-visible,
.settings-locale-option:focus-visible {
  outline: 2px solid var(--accent-500);
  outline-offset: 2px;
}

.settings-theme-option__preview {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 14px;
  width: 100%;
  height: 64px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  box-sizing: border-box;
}

.settings-theme-option__preview--light {
  background: linear-gradient(160deg, #ffffff, #eef3fb);
}

.settings-theme-option__preview--dark {
  background: linear-gradient(160deg, #1a2438, #0b1220);
}

.settings-theme-option__preview-bar {
  height: 6px;
  width: 70%;
  border-radius: 3px;
  background: rgba(128, 128, 128, 0.2);
}

.settings-theme-option__preview-bar--short {
  width: 45%;
}

.settings-theme-option__preview--dark .settings-theme-option__preview-bar {
  background: rgba(200, 200, 255, 0.15);
}

.settings-theme-option__label,
.settings-locale-option__label {
  color: var(--text-primary);
  font-weight: 700;
}

.settings-locale-option__short {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.settings-info-stack {
  display: grid;
  gap: 12px;
}

.settings-info-row,
.settings-system-card {
  display: grid;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  transition: border-color var(--transition-base);
}

.settings-info-row:hover,
.settings-system-card:hover {
  border-color: var(--panel-border-strong);
}

.settings-info-row {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.settings-info-row__label {
  display: block;
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.settings-info-row__value,
.settings-system-card__title {
  color: var(--text-primary);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.settings-system-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.settings-system-card__copy {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.88rem;
}

.settings-password-form {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  transition: border-color var(--transition-base);
}

.settings-password-form:hover {
  border-color: var(--panel-border-strong);
}

.settings-password-msg {
  margin: 0;
  font-size: 0.82rem;
  color: var(--success-500);
}

.settings-password-msg--error {
  color: var(--danger-500);
}

.settings-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  cursor: pointer;
  color: var(--text-primary);
  text-align: left;
}

.settings-section-header__title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.settings-section-header__chevron {
  flex-shrink: 0;
  color: var(--text-muted);
  transition: transform var(--transition-base);
}

.settings-section-header__chevron.is-collapsed {
  transform: rotate(-90deg);
}

.settings-password-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  cursor: pointer;
  text-align: left;
}

.settings-password-toggle:hover {
  color: var(--text-primary);
}

@media (max-width: 860px) {
  .settings-preferences-grid,
  .settings-secondary-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 861px) {
  .settings-section-header {
    cursor: default;
    pointer-events: none;
  }

  .settings-section-header__chevron {
    display: none;
  }
}

@media (max-width: 640px) {
  .settings-view,
  .settings-shell,
  .settings-secondary-grid {
    gap: 14px;
  }

  .settings-theme-grid,
  .settings-locale-grid {
    grid-template-columns: 1fr;
  }

  .settings-info-row {
    grid-template-columns: 1fr;
    align-items: start;
  }
}
</style>
