<template>
  <n-layout class="main-layout" has-sider :class="{ 'is-mobile': isMobile }">
    <n-layout-sider
      v-if="!isMobile"
      collapse-mode="width"
      :collapsed-width="76"
      :width="228"
      :collapsed="collapsed"
      bordered
      show-trigger="arrow-circle"
      class="main-layout__sider"
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <div class="main-layout__brand" :class="{ 'is-collapsed': collapsed }">
        <div class="main-layout__brand-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2" />
            <polyline points="2 17 12 22 22 17" />
            <polyline points="2 12 12 17 22 12" />
          </svg>
        </div>
        <div v-if="!collapsed" class="main-layout__brand-copy">
          <strong>AutoReverse</strong>
          <span>{{ t('nav.groups.tasks') }}</span>
        </div>
      </div>

      <div class="main-layout__nav" :class="{ 'main-layout__nav--collapsed': collapsed }">
        <AppNav />
      </div>

      <div class="main-layout__sider-footer" :class="{ 'is-collapsed': collapsed }">
        <button type="button" class="main-layout__action-pill" @click="toggleTheme" :aria-label="t('setting.fields.themeLabel')">
          <svg v-if="isLightMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-11.314l.707.707m11.314 11.314l.707.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </button>
      </div>
    </n-layout-sider>

    <n-layout class="main-layout__shell">
      <n-layout-header bordered class="main-layout__header">
        <div class="main-layout__header-left">
          <button
            v-if="isMobile"
            type="button"
            class="main-layout__header-btn"
            :aria-label="t('nav.aria')"
            @click="drawerOpen = true"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          </button>

          <div class="main-layout__page-meta">
            <span class="main-layout__eyebrow">{{ isMobile ? 'Workspace' : t('nav.groups.overview') }}</span>
            <strong>{{ activeLabel }}</strong>
          </div>
        </div>

        <div class="main-layout__header-actions">
          <button type="button" class="main-layout__header-btn" @click="toggleLocale" :aria-label="t('setting.fields.localeLabel')">
            <span class="main-layout__locale">{{ locale === 'zh-CN' ? 'EN' : '中' }}</span>
          </button>
          <button v-if="isMobile" type="button" class="main-layout__header-btn" @click="toggleTheme" :aria-label="t('setting.fields.themeLabel')">
            <svg v-if="isLightMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-11.314l.707.707m11.314 11.314l.707.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </button>
          <div class="main-layout__avatar">{{ activeLabel.slice(0, 1) }}</div>
        </div>
      </n-layout-header>

      <n-layout-content class="main-layout__content">
        <div class="main-layout__content-inner">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </n-layout-content>
    </n-layout>

    <MobileBottomNav :is-mobile="isMobile" />

    <n-drawer v-model:show="drawerOpen" placement="left" :width="300">
      <n-drawer-content :native-scrollbar="false" closable>
        <template #header>
          <div class="main-layout__drawer-header">
            <div class="main-layout__brand-mark main-layout__brand-mark--small">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
            </div>
            <div class="main-layout__brand-copy">
              <strong>AutoReverse</strong>
              <span>{{ t('nav.groups.tasks') }}</span>
            </div>
          </div>
        </template>

        <div class="main-layout__drawer-body">
          <SidebarContent @navigate="drawerOpen = false" />
        </div>

        <template #footer>
          <div class="main-layout__drawer-footer">
            <n-button quaternary block @click="toggleLocale">
              {{ locale === 'zh-CN' ? 'English' : '中文' }}
            </n-button>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import {
  NButton,
  NDrawer,
  NDrawerContent,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
} from 'naive-ui';

import AppNav from '@/components/AppNav.vue';
import MobileBottomNav from '@/components/MobileBottomNav.vue';
import SidebarContent from '@/components/SidebarContent.vue';
import { ROUTE_PATHS } from '@/constants/routes';
import { useLocale } from '@/composables/useLocale';
import { useTheme } from '@/composables/useTheme';

const { t, locale, setLocale } = useLocale();
const { isLightMode, toggleTheme } = useTheme();
const route = useRoute();

const collapsed = ref(false);
const drawerOpen = ref(false);
const isMobile = ref(false);

const routeLabelMap = computed<Record<string, string>>(() => ({
  [ROUTE_PATHS.HOME]: t('nav.items.home.label'),
  [ROUTE_PATHS.AUTO_REVERSE]: t('nav.items.autoReverse.label'),
  [ROUTE_PATHS.AUTO_REVERSE_CONFIG]: t('nav.items.config.label'),
  [ROUTE_PATHS.BROWSER_TASK]: t('nav.items.browserTask.label'),
  [ROUTE_PATHS.SETTING]: t('nav.items.setting.label'),
}));

const activeLabel = computed(() => {
  const knownPaths = Object.keys(routeLabelMap.value);
  const matchedPath = knownPaths.find((path) => route.path === path || route.path.startsWith(`${path}/`));
  return matchedPath ? routeLabelMap.value[matchedPath] : t('nav.items.home.label');
});

function syncViewport(): void {
  if (typeof window === 'undefined') return;
  isMobile.value = window.innerWidth < 960;
  if (!isMobile.value) {
    drawerOpen.value = false;
  }
}

function toggleLocale(): void {
  setLocale(locale.value === 'zh-CN' ? 'en-US' : 'zh-CN');
}

onMounted(() => {
  syncViewport();
  window.addEventListener('resize', syncViewport);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewport);
});
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: transparent;
}

.main-layout__sider {
  position: sticky;
  top: 0;
  height: 100vh;
  border-right: 1px solid var(--n-border-color);
  background: var(--nav-sider-bg);
}

.main-layout__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 18px 10px;
}

.main-layout__brand.is-collapsed {
  justify-content: center;
  padding-inline: 12px;
}

.main-layout__brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 14px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent-500) 14%, var(--bg-surface)), color-mix(in srgb, var(--accent-500) 6%, var(--bg-surface)));
  color: var(--accent-500);
  border: 1px solid color-mix(in srgb, var(--accent-500) 18%, transparent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32);
  flex-shrink: 0;
}

.main-layout__brand-mark svg {
  width: 18px;
  height: 18px;
}

.main-layout__brand-mark--small {
  width: 32px;
  height: 32px;
  border-radius: 12px;
}

.main-layout__brand-mark--small svg {
  width: 16px;
  height: 16px;
}

.main-layout__brand-copy {
  display: grid;
  gap: 2px;
}

.main-layout__brand-copy strong {
  color: var(--text-primary);
  font-size: 1rem;
  letter-spacing: -0.02em;
}

.main-layout__brand-copy span {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.main-layout__nav {
  padding: 6px 12px 18px;
}

.main-layout__nav--collapsed :deep(.n-menu-item-group-title) {
  display: none;
}

.main-layout__nav--collapsed :deep(.n-menu-item-content) {
  justify-content: center;
}

.main-layout__nav--collapsed :deep(.n-menu-item-content__icon) {
  margin-right: 0;
}

.main-layout__sider-footer {
  position: absolute;
  right: 12px;
  bottom: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 16px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow-xs);
}

.main-layout__sider-footer.is-collapsed {
  justify-content: center;
  padding-inline: 8px;
}

.main-layout__action-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-base);
  flex-shrink: 0;
  font: inherit;
  padding: 0;
}

.main-layout__action-pill:hover {
  border-color: var(--panel-border-strong);
  color: var(--accent-500);
  background: var(--bg-accent-soft);
  transform: scale(1.06);
}

.main-layout__shell {
  min-width: 0;
  background: transparent;
}

.main-layout__header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: var(--layout-header-height);
  padding: 0 20px;
  background: var(--nav-header-bg);
  backdrop-filter: blur(14px);
  box-shadow: var(--nav-shadow);
}

.main-layout__header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.main-layout__page-meta {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.main-layout__eyebrow {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.main-layout__page-meta strong {
  min-width: 0;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.2;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.main-layout__header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
}

.main-layout__header-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  padding: 0;
  transition: all var(--transition-base);
}

.main-layout__header-btn:hover {
  border-color: var(--panel-border-strong);
  color: var(--accent-500);
  background: var(--bg-accent-soft);
  box-shadow: var(--shadow-xs);
  transform: translateY(-1px);
}

.main-layout__header-btn:active {
  transform: translateY(0) scale(0.96);
}

.main-layout__header-btn:focus-visible {
  outline: 2px solid var(--accent-500);
  outline-offset: 2px;
}

.main-layout__locale {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.main-layout__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent-500), color-mix(in srgb, var(--accent-500) 72%, var(--success-500)));
  color: #fff;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.24);
}

.main-layout__content {
  background: transparent;
}

.main-layout__content-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 24px 32px;
}

.main-layout__drawer-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-layout__drawer-body {
  min-height: 0;
}

.main-layout__drawer-footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.26s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 959px) {
  .main-layout {
    display: block;
  }

  .main-layout__header {
    padding: 0 14px;
  }

  .main-layout__content-inner {
    padding: 18px 14px calc(var(--mobile-bottom-nav-height) + 18px);
  }

  .main-layout__page-meta strong {
    font-size: 0.98rem;
  }

  .main-layout__drawer-footer {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
