<template>
  <section class="home-view">
    <WorkspacePageHeader
      :title="t('home.title')"
      :tags="homeHeaderTags"
    >
      <template #actions>
        <n-space :size="8">
          <WorkspaceRefreshButton
            :label="t('home.actions.refresh')"
            :loading-label="t('common.status.syncing')"
            :aria-label="t('home.actions.refresh')"
            :loading="isLoading"
            @click="loadDashboard"
          />
          <n-button quaternary circle :aria-label="t('home.recent.debug.title')" @click="openDebugPanel">
            <template #icon>
              <n-icon>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              </n-icon>
            </template>
          </n-button>
        </n-space>
      </template>
    </WorkspacePageHeader>

    <div class="home-shell">
      <div class="home-shell__main">
        <div class="home-health-bar">
          <div class="home-health-bar__lead">
            <span class="home-health-bar__dot" :class="getHealthTagType(stats.health) === 'success' ? 'home-health-bar__dot--ok' : 'home-health-bar__dot--err'"></span>
            <strong>{{ getHealthStatusLabel(stats.health) }}</strong>
          </div>
          <span class="home-health-bar__time">{{ dashboardSnapshotLabel || '--' }}</span>
        </div>

        <WorkspaceSectionCard
          :title="t('home.recent.title')"
          :description="dashboardSnapshotLabel || undefined"
          class="tasks-panel"
        >
          <template #actions>
            <button
              v-if="isHomeMobile"
              type="button"
              class="tasks-collapse-btn"
              :aria-expanded="String(!recentTasksCollapsed)"
              :aria-label="recentTasksCollapsed ? '展开任务列表' : '折叠任务列表'"
              @click="recentTasksCollapsed = !recentTasksCollapsed"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                width="14"
                height="14"
                :style="{ transform: recentTasksCollapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform var(--transition-base)' }"
              >
                <path d="M18 15l-6-6-6 6" />
              </svg>
            </button>
            <span class="soft-badge">{{ tasks.length }}</span>
          </template>

          <div v-show="!recentTasksCollapsed" class="tasks-panel__body">
            <n-skeleton v-if="isLoading" text :repeat="6" size="large" />
            <template v-else>
              <n-data-table
                class="desktop-only"
                :columns="taskColumns"
                :data="paginatedTasks"
                :bordered="false"
                :pagination="false"
              />
              <n-empty v-if="tasks.length === 0" class="desktop-only" />
            </template>

            <div class="mobile-only task-list-mobile">
              <div v-for="task in paginatedTasks" :key="task.taskId" class="task-item-mobile" @click="navigateToTask(task.taskId)">
                <div class="task-item-mobile__status" :class="`is-${taskStatusType(task.status)}`"></div>
                <div class="task-item-mobile__content">
                  <div class="task-item-mobile__header">
                    <span class="task-item-mobile__id">#{{ task.taskId.slice(0, 8) }}</span>
                    <span class="task-item-mobile__time">{{ toDisplayTime(task.updatedAt) }}</span>
                  </div>
                  <div class="task-item-mobile__url">{{ task.url }}</div>
                  <div class="task-item-mobile__footer">
                    <n-tag :bordered="false" size="small" :type="taskStatusType(task.status)" round>
                      {{ getTaskStatusLabel(task.status) }}
                    </n-tag>
                    <span class="task-item-mobile__agent" v-if="task.agentTag">{{ task.agentTag }}</span>
                  </div>
                </div>
              </div>
              <n-empty v-if="tasks.length === 0 && !isLoading" />
            </div>

            <div v-if="tasks.length > RECENT_TASK_PAGE_SIZE" class="tasks-pagination-wrap">
              <n-pagination
                v-model:page="recentTaskPage"
                :page-size="RECENT_TASK_PAGE_SIZE"
                :item-count="tasks.length"
                simple
              />
            </div>
          </div>
        </WorkspaceSectionCard>
      </div>

      <aside class="home-shell__side">
        <div class="home-metrics-row">
          <article
            v-for="card in summaryCards"
            :key="card.key"
            class="home-metric-card"
            :style="{ '--metric-color': card.color }"
          >
            <div class="home-metric-card__icon" :style="{ background: card.bgColor }">
              <n-icon :color="card.color" size="18">
                <component :is="card.icon" />
              </n-icon>
            </div>
            <div class="home-metric-card__body">
              <strong>{{ card.value }}</strong>
              <span>{{ card.label }}</span>
            </div>
          </article>
        </div>

        <WorkspaceSectionCard
          :title="t('home.trend.title')"
          :description="dashboardSnapshotLabel"
          class="chart-panel"
        >
          <n-skeleton v-if="isLoading" height="300px" />
          <div v-else ref="chartRef" class="chart-container"></div>
        </WorkspaceSectionCard>
      </aside>
    </div>

    <n-drawer v-model:show="debugPanelOpen" :width="isHomeMobile ? '100%' : 380" :placement="isHomeMobile ? 'bottom' : 'right'">
      <n-drawer-content :title="t('home.recent.debug.title')" closable>
        <n-space vertical size="large">
          <n-alert :show-icon="false" :type="debugMode ? 'warning' : 'info'">
            {{ t('home.recent.debug.copy') }}
          </n-alert>

          <div class="drawer-action-group">
            <n-button block size="large" :type="debugMode ? 'warning' : 'default'" @click="toggleDebugMode">
              {{ debugMode ? t('home.recent.actions.exitDebug') : t('home.recent.actions.enterDebug') }}
            </n-button>
          </div>

          <template v-if="debugMode">
            <n-divider title-placement="left">{{ t('home.recent.debug.failedTasks') }}</n-divider>
            <n-button block secondary type="error" :disabled="!canClearFailedTasks" @click="toggleDebugActionConfirmation('clearFailed')">
              {{ t('home.recent.actions.clearFailed') }}
            </n-button>
            <n-button block quaternary type="error" :disabled="!canClearAllTasks" @click="toggleDebugActionConfirmation('clearAll')">
              {{ t('home.recent.actions.clearAllTasks') }}
            </n-button>
          </template>
        </n-space>

        <template #footer v-if="confirmingDebugAction">
          <n-card size="small" :title="debugConfirmationCopy" :bordered="false" class="confirm-card">
            <n-space justify="end">
              <n-button size="small" @click="cancelDebugActionConfirmation">{{ t('home.recent.actions.cancel') }}</n-button>
              <n-button size="small" type="error" :loading="debugBusy" @click="confirmDebugAction">{{ t('home.recent.actions.confirmExecute') }}</n-button>
            </n-space>
          </n-card>
        </template>
      </n-drawer-content>
    </n-drawer>
  </section>
</template>

<script setup lang="ts">
import { h, computed, ref, onMounted, onBeforeUnmount, watch, defineComponent } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import {
  NSpace,
  NButton,
  NIcon,
  NDataTable,
  NSkeleton,
  NEmpty,
  NPagination,
  NDrawer,
  NDrawerContent,
  NAlert,
  NTag,
  NDivider,
  NCard,
  type DataTableColumns,
} from 'naive-ui';
import { init, use, type EChartsType } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';

import WorkspacePageHeader from '@/components/WorkspacePageHeader.vue';
import WorkspaceSectionCard from '@/components/WorkspaceSectionCard.vue';
import WorkspaceRefreshButton from '@/components/WorkspaceRefreshButton.vue';
import { useLocale } from '@/composables/useLocale';
import { useTheme } from '@/composables/useTheme';
import { useWorkspaceData } from '@/composables/useWorkspaceData';
import { ROUTE_PATHS } from '@/constants/routes';
import {
  clearAllAutoReverseTasksByApi,
  clearFailedAutoReverseTasksByApi,
  type AutoReverseTaskItem,
} from '@/views/api';

use([CanvasRenderer, LineChart, GridComponent, LegendComponent, TooltipComponent]);

const IconTotal = defineComponent({ render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [h('path', { d: 'M22 12h-4l-3 9L9 3l-3 9H2' })]) });
const IconSuccess = defineComponent({ render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [h('path', { d: 'M22 11.08V12a10 10 0 1 1-5.93-9.14' }), h('polyline', { points: '22 4 12 14.01 9 11.01' })]) });
const IconError = defineComponent({ render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [h('circle', { cx: '12', cy: '12', r: '10' }), h('line', { x1: '15', y1: '9', x2: '9', y2: '15' }), h('line', { x1: '9', y1: '9', x2: '15', y2: '15' })]) });
const IconQueue = defineComponent({ render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [h('circle', { cx: '12', cy: '12', r: '10' }), h('polyline', { points: '12 6 12 12 16 14' })]) });

const router = useRouter();
const { t, formatDateTime, getTaskStatusLabel, getHealthStatusLabel } = useLocale();
const { isLightMode } = useTheme();
const { dashboardPayload, dashboardLoading, reloadDashboard, bootstrapWorkspaceData } = useWorkspaceData();

const chartRef = ref<HTMLElement | null>(null);
const chartInstance = ref<EChartsType | null>(null);
const debugPanelOpen = ref(false);
const debugMode = ref(false);
const isHomeMobile = ref(false);
const confirmingDebugAction = ref<'' | 'clearAll' | 'clearFailed'>('');
const debugBusy = ref(false);
const RECENT_TASK_PAGE_SIZE = 5;
const recentTaskPage = ref(1);
const recentTasksCollapsed = ref(false);

const stats = computed(() => dashboardPayload.value?.stats ?? { health: 'unknown', requestTotal: 0, processing: 0, queued: 0, completed: 0, failed: 0, snapshotAt: null });
const tasks = computed<AutoReverseTaskItem[]>(() => [...(dashboardPayload.value?.tasks ?? [])]);
const paginatedTasks = computed<AutoReverseTaskItem[]>(() => {
  const start = (recentTaskPage.value - 1) * RECENT_TASK_PAGE_SIZE;
  return tasks.value.slice(start, start + RECENT_TASK_PAGE_SIZE);
});
const isLoading = computed(() => dashboardLoading.value && !dashboardPayload.value);

const homeHeaderTags = computed(() => [
  { label: getHealthStatusLabel(stats.value.health), type: getHealthTagType(stats.value.health) as 'success' | 'error' },
]);

const summaryCards = computed(() => [
  { key: 'total', label: t('home.stats.requestTotal'), value: stats.value.requestTotal, icon: IconTotal, color: 'var(--n-primary-color)', bgColor: 'color-mix(in srgb, var(--n-primary-color) 12%, transparent)' },
  { key: 'completed', label: t('home.stats.completed'), value: stats.value.completed, icon: IconSuccess, color: 'var(--n-success-color)', bgColor: 'color-mix(in srgb, var(--n-success-color) 12%, transparent)' },
  { key: 'failed', label: t('home.stats.failed'), value: stats.value.failed, icon: IconError, color: 'var(--n-error-color)', bgColor: 'color-mix(in srgb, var(--n-error-color) 12%, transparent)' },
  { key: 'queued', label: t('home.stats.queued'), value: stats.value.queued, icon: IconQueue, color: 'var(--n-warning-color)', bgColor: 'color-mix(in srgb, var(--n-warning-color) 14%, transparent)' },
]);

const taskColumns = computed<DataTableColumns<AutoReverseTaskItem>>(() => [
  {
    title: 'ID',
    key: 'taskId',
    width: 100,
    render: (row) => h(RouterLink, { to: { path: ROUTE_PATHS.AUTO_REVERSE, query: { taskId: row.taskId } }, class: 'task-id-link' }, { default: () => row.taskId.slice(0, 8) }),
  },
  { title: t('home.recent.table.url'), key: 'url', ellipsis: { tooltip: true } },
  {
    title: t('home.recent.table.status'),
    key: 'status',
    width: 120,
    render: (row) => h(NTag, { bordered: false, round: true, size: 'small', type: taskStatusType(row.status) }, { default: () => getTaskStatusLabel(row.status) }),
  },
  { title: t('home.recent.table.updatedAt'), key: 'updatedAt', width: 160, render: (row) => h('span', { class: 'text-muted small' }, toDisplayTime(row.updatedAt)) },
]);

const dashboardSnapshotLabel = computed(() => stats.value.snapshotAt ? formatDateTime(stats.value.snapshotAt) : '');

const chartPalette = computed(() =>
  isLightMode.value
    ? {
        total: '#2563eb',
        success: '#059669',
        axis: '#64748b',
        grid: 'rgba(148, 163, 184, 0.22)',
        tooltipBg: '#ffffff',
        tooltipBorder: '#dbe4f0',
      }
    : {
        total: '#7aa2ff',
        success: '#22c55e',
        axis: '#8da0b8',
        grid: 'rgba(143, 163, 191, 0.22)',
        tooltipBg: '#101a2c',
        tooltipBorder: 'rgba(143, 163, 191, 0.18)',
      },
);

const taskStatusType = (s: string) => {
  const low = s.toLowerCase();
  return low.includes('succ') ? 'success' : low.includes('fail') || low.includes('err') ? 'error' : 'warning';
};

const toDisplayTime = (v?: string) => (v ? formatDateTime(v).split(' ')[1] : '--:--');
const getHealthTagType = (h: string) => (h.toLowerCase().includes('ok') ? 'success' : 'error');
const navigateToTask = (id: string) => router.push({ path: ROUTE_PATHS.AUTO_REVERSE, query: { taskId: id } });

const loadDashboard = () => reloadDashboard({ force: true });
const openDebugPanel = () => {
  debugPanelOpen.value = true;
};
const toggleDebugMode = () => {
  debugMode.value = !debugMode.value;
};

const canClearAllTasks = computed(() => tasks.value.length > 0);
const canClearFailedTasks = computed(() => stats.value.failed > 0);

const debugConfirmationCopy = computed(() =>
  confirmingDebugAction.value === 'clearAll' ? '确定清空所有任务？' : '确定清空失败任务？',
);

const toggleDebugActionConfirmation = (a: 'clearAll' | 'clearFailed') => {
  confirmingDebugAction.value = a;
};
const cancelDebugActionConfirmation = () => {
  confirmingDebugAction.value = '';
};

const confirmDebugAction = async () => {
  debugBusy.value = true;
  try {
    if (confirmingDebugAction.value === 'clearAll') await clearAllAutoReverseTasksByApi();
    else await clearFailedAutoReverseTasksByApi();
    await loadDashboard();
    confirmingDebugAction.value = '';
  } finally {
    debugBusy.value = false;
  }
};

const renderChart = () => {
  if (!chartRef.value || !dashboardPayload.value?.trend) return;
  if (!chartInstance.value) chartInstance.value = init(chartRef.value);

  const trend = dashboardPayload.value.trend;
  const palette = chartPalette.value;
  chartInstance.value.setOption({
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      borderRadius: 12,
      padding: 12,
      backgroundColor: palette.tooltipBg,
      borderColor: palette.tooltipBorder,
      textStyle: {
        color: isLightMode.value ? '#0f172a' : '#f8fbff',
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      axisLabel: { color: palette.axis },
      axisLine: { lineStyle: { color: palette.grid } },
      data: trend.map((i) => i.timestamp.split('T')[1].slice(0, 5)),
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: palette.axis },
      splitLine: { lineStyle: { type: 'dashed', opacity: 1, color: palette.grid } },
    },
    series: [
      { name: 'Total', type: 'line', smooth: true, data: trend.map((i) => i.requestTotal), itemStyle: { color: palette.total }, areaStyle: { opacity: 0.08 } },
      { name: 'Success', type: 'line', smooth: true, data: trend.map((i) => i.completed), itemStyle: { color: palette.success } },
    ],
  });
};

const handleResize = () => {
  const wasMobile = isHomeMobile.value;
  isHomeMobile.value = window.innerWidth < 768;
  if (wasMobile && !isHomeMobile.value) recentTasksCollapsed.value = false;
  chartInstance.value?.resize();
};

onMounted(async () => {
  handleResize();
  window.addEventListener('resize', handleResize);
  if (!dashboardPayload.value) await bootstrapWorkspaceData({ force: true });
  renderChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance.value?.dispose();
});

watch([() => dashboardPayload.value, isLightMode], renderChart, { deep: true });
watch(tasks, (nextTasks) => {
  const pageCount = Math.max(1, Math.ceil(nextTasks.length / RECENT_TASK_PAGE_SIZE));
  if (recentTaskPage.value > pageCount) {
    recentTaskPage.value = pageCount;
  }
  if (recentTaskPage.value < 1) {
    recentTaskPage.value = 1;
  }
});
</script>

<style scoped>
.home-view {
  display: grid;
  gap: 22px;
}

.home-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(460px, 0.92fr);
  gap: 18px;
  align-items: start;
}

.home-shell__main,
.home-shell__side {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.home-shell__side {
  position: sticky;
  top: calc(var(--layout-header-height) + 16px);
}

/* ── Health status bar (right side header) ── */
.home-health-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  box-shadow: var(--shadow-xs);
}

.home-health-bar__lead {
  display: flex;
  align-items: center;
  gap: 8px;
}

.home-health-bar__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.home-health-bar__dot--ok {
  background: var(--success-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--success-500) 18%, transparent);
}

.home-health-bar__dot--err {
  background: var(--danger-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger-500) 18%, transparent);
}

.home-health-bar__lead strong {
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 700;
}

.home-health-bar__time {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* ── Metric cards row (left side, below table) ── */
.home-metrics-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.home-metric-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 10px;
  border-radius: 14px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: var(--shadow-xs);
  transition: border-color 180ms ease-out, transform 100ms ease-out;
}

.home-metric-card:hover {
  border-color: var(--metric-color, var(--accent-500));
  transform: translateY(-1px);
}

.home-metric-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 12px;
  flex-shrink: 0;
}

.home-metric-card__body {
  display: grid;
  gap: 1px;
  min-width: 0;
}

.home-metric-card__body strong {
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.home-metric-card__body span {
  color: var(--text-muted);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


.chart-container {
  height: 300px;
  width: 100%;
}

.task-id-link {
  font-family: var(--font-mono);
  font-weight: 600;
  text-decoration: none;
  color: var(--n-primary-color);
}

.task-list-mobile {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.task-item-mobile {
  display: flex;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: background var(--transition-base), border-color var(--transition-base), transform var(--transition-fast);
}

.task-item-mobile:active {
  background: var(--panel-bg-soft);
  transform: scale(0.99);
}

.task-item-mobile__status {
  width: 4px;
  flex-shrink: 0;
}

.task-item-mobile__status.is-success {
  background: var(--n-success-color);
}

.task-item-mobile__status.is-error {
  background: var(--n-error-color);
}

.task-item-mobile__status.is-warning {
  background: var(--n-warning-color);
}

.task-item-mobile__content {
  padding: 12px;
  flex: 1;
  min-width: 0;
}

.task-item-mobile__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.task-item-mobile__id {
  font-weight: 700;
  font-size: 13px;
  color: var(--n-primary-color);
}

.task-item-mobile__time {
  font-size: 11px;
  color: var(--n-text-color-3);
}

.task-item-mobile__url {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
  color: var(--n-text-color-2);
}

.task-item-mobile__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.task-item-mobile__agent {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--panel-bg-soft);
  border-radius: 999px;
  color: var(--n-text-color-3);
}

.tasks-collapse-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-soft);
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  font: inherit;
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.tasks-collapse-btn:hover {
  border-color: var(--panel-border-strong);
  color: var(--text-primary);
}

.confirm-card {
  margin-top: 12px;
  border: 1px solid var(--n-error-color);
  background: color-mix(in srgb, var(--n-error-color) 5%, transparent);
}

@media (max-width: 1180px) {
  .home-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .home-shell__side {
    position: static;
  }
}

@media (max-width: 900px) {
  .home-metrics-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 768px) {
  .mobile-only {
    display: none;
  }
}

@media (max-width: 767px) {
  .home-view {
    gap: 18px;
  }

  .home-shell,
  .home-shell__main,
  .home-shell__side {
    gap: 16px;
  }

  .desktop-only {
    display: none;
  }
}

.text-muted {
  color: var(--n-text-color-3);
}

.small {
  font-size: 12px;
}

@media (max-width: 480px) {
  .home-metric-card__body strong {
    font-size: 1rem;
  }
}
</style>
