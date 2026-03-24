<template>
  <n-menu
    :value="activePath"
    :options="menuOptions"
    :indent="18"
    class="app-nav"
    @update:value="handleSelect"
  />
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { NMenu, type MenuOption } from 'naive-ui';
import { useRoute, useRouter } from 'vue-router';

import { useLocale } from '@/composables/useLocale';
import { ROUTE_PATHS } from '@/constants/routes';

interface NavItem {
  label: string;
  to: string;
  iconSvg: string;
}

const emit = defineEmits<{
  navigate: [];
}>();

const route = useRoute();
const router = useRouter();
const { t } = useLocale();

const ICONS = {
  home: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
  autoReverse: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>',
  config: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
  browserTask: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>',
  setting: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
};

function renderNavLabel(item: NavItem) {
  return () =>
    h('div', { class: 'app-nav__option' }, [
      h('div', { class: 'app-nav__option-head' }, [h('span', { class: 'app-nav__option-label' }, item.label)]),
    ]);
}

function renderNavIcon(svgStr: string) {
  return () => h('span', { class: 'app-nav__icon-svg', innerHTML: svgStr });
}

function makeOption(item: NavItem): MenuOption {
  return {
    key: item.to,
    label: renderNavLabel(item),
    icon: renderNavIcon(item.iconSvg),
  };
}

const menuOptions = computed<MenuOption[]>(() => [
  {
    type: 'group',
    key: 'group-overview',
    label: t('nav.groups.overview'),
    children: [
      makeOption({
        label: t('nav.items.home.label'),
        to: ROUTE_PATHS.HOME,
        iconSvg: ICONS.home,
      }),
    ],
  },
  {
    type: 'group',
    key: 'group-tasks',
    label: t('nav.groups.tasks'),
    children: [
      makeOption({
        label: t('nav.items.autoReverse.label'),
        to: ROUTE_PATHS.AUTO_REVERSE,
        iconSvg: ICONS.autoReverse,
      }),
      makeOption({
        label: t('nav.items.config.label'),
        to: ROUTE_PATHS.AUTO_REVERSE_CONFIG,
        iconSvg: ICONS.config,
      }),
      makeOption({
        label: t('nav.items.browserTask.label'),
        to: ROUTE_PATHS.BROWSER_TASK,
        iconSvg: ICONS.browserTask,
      }),
    ],
  },
  {
    type: 'group',
    key: 'group-system',
    label: t('nav.groups.system'),
    children: [
      makeOption({
        label: t('nav.items.setting.label'),
        to: ROUTE_PATHS.SETTING,
        iconSvg: ICONS.setting,
      }),
    ],
  },
]);

const activePath = computed(() => {
  const knownPaths = [
    ROUTE_PATHS.HOME,
    ROUTE_PATHS.AUTO_REVERSE,
    ROUTE_PATHS.AUTO_REVERSE_CONFIG,
    ROUTE_PATHS.BROWSER_TASK,
    ROUTE_PATHS.SETTING,
  ];

  return knownPaths.find((path) => route.path === path || route.path.startsWith(`${path}/`)) ?? ROUTE_PATHS.HOME;
});

const handleSelect = async (key: string) => {
  if (key === route.path) {
    emit('navigate');
    return;
  }
  await router.push(key);
  emit('navigate');
};
</script>

<style scoped>
.app-nav {
  background: transparent;
}

:deep(.n-menu-item-group-title) {
  padding-inline: 10px 12px;
  color: var(--text-muted);
  font-size: 0.73rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

:deep(.n-menu-item-content),
:deep(.n-menu-item-content::before) {
  border-radius: 14px;
}

:deep(.n-menu-item-content) {
  min-height: 44px;
  border: 1px solid transparent;
  transition:
    border-color var(--transition-base),
    background-color var(--transition-base),
    box-shadow var(--transition-base);
}

:deep(.n-menu-item-content:hover) {
  background: rgba(var(--accent-rgb), 0.04);
  border-color: rgba(var(--accent-rgb), 0.1);
}

:deep(.n-menu-item-content-header) {
  min-width: 0;
  width: 100%;
}

:deep(.n-menu-item) {
  margin-bottom: 4px;
}

:deep(.n-menu-item-content__icon) {
  margin-right: 12px;
}

:deep(.n-menu-item-content--selected) {
  background: linear-gradient(135deg, rgba(var(--accent-rgb), 0.12), rgba(var(--accent-rgb), 0.06));
  border-color: rgba(var(--accent-rgb), 0.2);
  box-shadow:
    inset 3px 0 0 var(--accent-500),
    0 1px 3px rgba(var(--accent-rgb), 0.08);
}

:deep(.n-menu-item-content--selected)::before {
  background: transparent !important;
}

:deep(.n-menu-item-content--selected) .app-nav__option-label {
  color: var(--accent-500);
}

.app-nav__option {
  min-width: 0;
  display: flex;
  align-items: center;
  min-height: 30px;
}

.app-nav__option-head {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  gap: 8px;
}

.app-nav__option-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
  line-height: 1.2;
}

.app-nav__icon-svg {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: color var(--transition-base);
}

:deep(.n-menu-item-content:hover) .app-nav__icon-svg {
  color: var(--accent-400);
}

:deep(.n-menu-item-content--selected) .app-nav__icon-svg {
  color: var(--accent-500);
}
</style>
