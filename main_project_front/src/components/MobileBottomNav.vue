<template>
  <nav v-if="isMobile" class="mobile-bottom-nav" aria-label="Primary">
    <div class="mobile-bottom-nav__inner">
      <button
        v-for="item in navItems"
        :key="item.path"
        type="button"
        class="mobile-bottom-nav__item"
        :class="{ 'mobile-bottom-nav__item--active': isActive(item.path) }"
        @click="navigate(item.path)"
      >
        <div class="mobile-bottom-nav__icon">
          <svg v-if="item.key === 'home'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
          <svg v-else-if="item.key === 'auto'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>
          <svg v-else-if="item.key === 'tasks'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
          <svg v-else-if="item.key === 'config'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          <svg v-else-if="item.key === 'settings'" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/></svg>
        </div>
        <span class="mobile-bottom-nav__label">{{ item.label }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLocale } from '@/composables/useLocale';
import { ROUTE_PATHS } from '@/constants/routes';

defineProps<{
  isMobile: boolean;
}>();

const route = useRoute();
const router = useRouter();
const { t } = useLocale();

const navItems = computed(() => [
  { key: 'home', label: t('nav.items.home.label'), path: ROUTE_PATHS.HOME },
  { key: 'auto', label: t('nav.items.autoReverse.label'), path: ROUTE_PATHS.AUTO_REVERSE },
  { key: 'tasks', label: t('nav.items.browserTask.label'), path: ROUTE_PATHS.BROWSER_TASK },
  { key: 'config', label: t('nav.items.config.label'), path: ROUTE_PATHS.AUTO_REVERSE_CONFIG },
  { key: 'settings', label: t('nav.items.setting.label'), path: ROUTE_PATHS.SETTING },
]);

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/');
};

const navigate = (path: string) => {
  if (route.path !== path) {
    router.push(path);
  }
};
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--mobile-bottom-nav-height);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--panel-bg) 72%, transparent), color-mix(in srgb, var(--panel-bg) 94%, transparent));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-top: 1px solid var(--border-soft);
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  box-shadow: var(--nav-shadow);
  transition: background-color var(--transition-base), border-color var(--transition-base);
}

.mobile-bottom-nav__inner {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 72px;
  max-width: 600px;
  margin: 0 auto;
  padding: 0 4px;
}

.mobile-bottom-nav__item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  cursor: pointer;
  color: var(--text-muted);
  transition: all var(--transition-base);
  padding: 4px 0;
  border: 0;
  background: transparent;
  font: inherit;
}

.mobile-bottom-nav__item:active {
  transform: scale(0.9);
}

.mobile-bottom-nav__item--active {
  color: var(--accent-500);
}

.mobile-bottom-nav__item::before {
  content: '';
  position: absolute;
  top: 8px;
  width: 48px;
  height: 32px;
  border-radius: 16px;
  background-color: var(--nav-active-pill-bg);
  opacity: 0;
  transform: scaleX(0.5);
  transition: all var(--transition-base);
  z-index: 0;
}

.mobile-bottom-nav__item--active::before {
  opacity: 1;
  transform: scaleX(1);
}

.mobile-bottom-nav__icon {
  position: relative;
  width: 22px;
  height: 22px;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition-base);
  z-index: 1;
}

.mobile-bottom-nav__item--active .mobile-bottom-nav__icon {
  transform: translateY(-3px);
}

.mobile-bottom-nav__icon :deep(svg) {
  width: 100%;
  height: 100%;
}

.mobile-bottom-nav__label {
  position: relative;
  font-size: 10.5px;
  font-weight: 700;
  line-height: 1.2;
  z-index: 1;
  transition: transform var(--transition-base);
  letter-spacing: 0.01em;
}

.mobile-bottom-nav__item--active .mobile-bottom-nav__label {
  transform: translateY(-2px);
}
</style>
