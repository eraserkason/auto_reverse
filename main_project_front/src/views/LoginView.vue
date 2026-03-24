<template>
  <section class="login-page">
    <div class="login-page__ambient" aria-hidden="true"></div>

    <div class="login-shell">
      <n-card :bordered="false" size="large" class="login-shell__form-card glass-card">
        <template #header>
          <div class="login-shell__form-head">
            <div class="login-brand">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="login-brand__logo"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            </div>
            <h2>{{ t('login.card.title') }}</h2>
            <p class="login-shell__hint">{{ t('login.hint') }}</p>
          </div>
        </template>

        <n-form label-placement="top" @submit.prevent="handleLogin">
          <n-form-item :label="t('login.fields.username')">
            <n-input
              id="username"
              v-model:value="username"
              autocomplete="username"
              :disabled="isLoading"
              :placeholder="t('login.fields.username')"
              size="large"
            />
          </n-form-item>

          <n-form-item :label="t('login.fields.password')">
            <n-input
              id="password"
              v-model:value="password"
              type="password"
              show-password-on="mousedown"
              autocomplete="current-password"
              :disabled="isLoading"
              :placeholder="t('login.fields.password')"
              size="large"
            />
          </n-form-item>

          <n-alert v-if="errorMessage" type="error" :show-icon="false" class="login-shell__alert">
            {{ errorMessage }}
          </n-alert>

          <div class="login-shell__actions">
            <n-button attr-type="submit" type="primary" size="large" :loading="isLoading" block>
              {{ isLoading ? t('common.actions.loginLoading') : t('common.actions.login') }}
            </n-button>
          </div>
        </n-form>
      </n-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { NAlert, NButton, NCard, NForm, NFormItem, NInput } from 'naive-ui';
import { useRouter } from 'vue-router';

import { useAuth } from '@/composables/useAuth';
import { useLocale } from '@/composables/useLocale';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { ROUTE_PATHS } from '@/constants/routes';

const router = useRouter();
const { isAuthenticated, login } = useAuth();
const { t } = useLocale();
const { resetWorkspaceData } = useWorkspaceData();

const username = ref('');
const password = ref('');
const errorKey = ref<'emptyCredentials' | 'loginFailed' | ''>('');
const isLoading = ref(false);

const errorMessage = computed(() => {
  if (!errorKey.value) {
    return '';
  }
  return t(`login.errors.${errorKey.value}`);
});

async function handleLogin(): Promise<void> {
  errorKey.value = '';

  if (!username.value.trim() || !password.value) {
    errorKey.value = 'emptyCredentials';
    return;
  }

  isLoading.value = true;
  try {
    const success = await login(username.value, password.value);
    if (!success) {
      errorKey.value = 'loginFailed';
      return;
    }
    resetWorkspaceData();
    await router.push(ROUTE_PATHS.HOME);
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  if (isAuthenticated.value) {
    resetWorkspaceData();
    await router.push(ROUTE_PATHS.HOME);
  }
});
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background-color: var(--bg-canvas);
  overflow: hidden;
}

.login-page__ambient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 12% 12%, var(--bg-accent-soft), transparent 28%),
    radial-gradient(circle at 86% 80%, color-mix(in srgb, var(--success-500) 8%, transparent), transparent 30%),
    linear-gradient(color-mix(in srgb, var(--text-muted) 8%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--text-muted) 8%, transparent) 1px, transparent 1px);
  background-size: auto, auto, 34px 34px, 34px 34px;
  mask-image: radial-gradient(circle at center, rgba(0, 0, 0, 1), transparent 90%);
  opacity: 0.6;
}

.login-shell {
  position: relative;
  z-index: 1;
  width: min(420px, 100%);
}

.login-shell__form-card {
  border-radius: 28px;
  padding: 12px;
  box-shadow: var(--shadow-soft);
}

.login-shell__form-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  margin-bottom: 12px;
}

.login-brand__logo {
  color: var(--accent-500);
  margin-bottom: 8px;
  filter: drop-shadow(0 6px 12px rgba(var(--accent-rgb), 0.16));
}

.login-shell__form-head h2 {
  margin: 0;
  font-size: 1.8rem;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.login-shell__hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.login-shell__alert {
  margin-top: 12px;
}

.login-shell__actions {
  margin-top: 24px;
}

@media (max-width: 640px) {
  .login-page {
    padding: 16px;
  }
}
</style>
