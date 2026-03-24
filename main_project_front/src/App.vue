<template>
  <n-config-provider
    :theme="activeTheme"
    :theme-overrides="currentThemeOverrides"
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
  >
    <n-global-style />
    <n-loading-bar-provider>
      <n-notification-provider>
        <n-dialog-provider>
            <n-message-provider>
              <RouterView />
              <WorkspaceBootstrapOverlay
                v-if="isAuthenticated && isBootstrapping && !hasBootstrapped"
                :dashboard-ready="bootstrapDashboardReady"
                :resources-ready="bootstrapResourcesReady"
              />
            </n-message-provider>
          </n-dialog-provider>
        </n-notification-provider>
      </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import {
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NLoadingBarProvider,
  NMessageProvider,
  NNotificationProvider,
  dateEnUS,
  dateZhCN,
  enUS,
  zhCN,
} from 'naive-ui';

import { useLocale } from '@/composables/useLocale';
import { useAuth } from '@/composables/useAuth';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { lightThemeOverrides, darkThemeOverrides } from '@/theme/themeConfig';
import { useTheme } from '@/composables/useTheme';
import WorkspaceBootstrapOverlay from '@/components/WorkspaceBootstrapOverlay.vue';

const { locale } = useLocale();
const { isAuthenticated } = useAuth();
const { bootstrapWorkspaceData, resetWorkspaceData, isBootstrapping, hasBootstrapped, bootstrapDashboardReady, bootstrapResourcesReady } = useWorkspaceData();
const { activeTheme, isLightMode, initTheme } = useTheme();

const naiveLocale = computed(() => (locale.value === 'zh-CN' ? zhCN : enUS));
const naiveDateLocale = computed(() => (locale.value === 'zh-CN' ? dateZhCN : dateEnUS));

const currentThemeOverrides = computed(() => {
  return isLightMode.value ? lightThemeOverrides : darkThemeOverrides;
});

onMounted(() => {
  initTheme();
});

watch(
  isAuthenticated,
  (authed) => {
    if (authed) {
      void bootstrapWorkspaceData();
      return;
    }
    resetWorkspaceData();
  },
  { immediate: true },
);
</script>
