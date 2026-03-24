import { computed, readonly, ref } from 'vue';

import {
  buildAutoReverseOptionsFromConfigPayload,
  fetchAutoReverseConfig,
  fetchDashboardPayload,
  type AutoReverseConfigPayload,
  type AutoReverseOptions,
  type DashboardPayload,
} from '@/views/api';

const dashboardPayload = ref<DashboardPayload | null>(null);
const autoReverseOptions = ref<AutoReverseOptions | null>(null);
const autoReverseConfig = ref<AutoReverseConfigPayload | null>(null);

const isBootstrapping = ref(false);
const hasBootstrapped = ref(false);
const bootstrapErrorDetail = ref('');
const bootstrapDashboardReady = ref(false);
const bootstrapResourcesReady = ref(false);

const dashboardLoading = ref(false);
const dashboardErrorDetail = ref('');
const resourcesLoading = ref(false);
const resourcesErrorDetail = ref('');

let bootstrapPending: Promise<void> | null = null;
let dashboardPending: Promise<void> | null = null;
let resourcesPending: Promise<void> | null = null;

const isWorkspaceReady = computed(() => Boolean(dashboardPayload.value && autoReverseOptions.value && autoReverseConfig.value));

async function reloadDashboard(options?: { force?: boolean; silent?: boolean }): Promise<void> {
  if (dashboardPending) {
    return dashboardPending;
  }

  const force = options?.force ?? true;
  const silent = options?.silent ?? false;
  dashboardPending = (async () => {
    if (!silent) {
      dashboardLoading.value = true;
    }
    try {
      dashboardPayload.value = await fetchDashboardPayload({ force });
      dashboardErrorDetail.value = '';
    } catch (error) {
      dashboardErrorDetail.value = error instanceof Error ? error.message : '';
      throw error;
    } finally {
      dashboardLoading.value = false;
      dashboardPending = null;
    }
  })();

  return dashboardPending;
}

async function reloadAutoReverseResources(options?: { silent?: boolean; force?: boolean }): Promise<void> {
  if (resourcesPending) {
    return resourcesPending;
  }

  const silent = options?.silent ?? false;
  const force = options?.force ?? false;
  if (!force && autoReverseOptions.value && autoReverseConfig.value) {
    return;
  }

  resourcesPending = (async () => {
    if (!silent) {
      resourcesLoading.value = true;
    }
    try {
      const configPayload = await fetchAutoReverseConfig();
      autoReverseConfig.value = configPayload;
      autoReverseOptions.value = buildAutoReverseOptionsFromConfigPayload(configPayload);
      resourcesErrorDetail.value = '';
    } catch (error) {
      resourcesErrorDetail.value = error instanceof Error ? error.message : '';
      throw error;
    } finally {
      resourcesLoading.value = false;
      resourcesPending = null;
    }
  })();

  return resourcesPending;
}

async function bootstrapWorkspaceData(options?: { force?: boolean }): Promise<void> {
  if (bootstrapPending) {
    return bootstrapPending;
  }

  const force = options?.force ?? false;
  if (hasBootstrapped.value && isWorkspaceReady.value && !force) {
    return;
  }

  bootstrapPending = (async () => {
    isBootstrapping.value = true;
    bootstrapErrorDetail.value = '';
    bootstrapDashboardReady.value = false;
    bootstrapResourcesReady.value = false;
    try {
      await Promise.all([
        reloadDashboard({ force, silent: true }).then(() => {
          bootstrapDashboardReady.value = true;
        }),
        reloadAutoReverseResources({ force, silent: true }).then(() => {
          bootstrapResourcesReady.value = true;
        }),
      ]);
      hasBootstrapped.value = true;
    } catch (error) {
      bootstrapErrorDetail.value = error instanceof Error ? error.message : '';
      throw error;
    } finally {
      isBootstrapping.value = false;
      bootstrapPending = null;
    }
  })();

  return bootstrapPending;
}

function resetWorkspaceData(): void {
  dashboardPayload.value = null;
  autoReverseOptions.value = null;
  autoReverseConfig.value = null;
  isBootstrapping.value = false;
  hasBootstrapped.value = false;
  bootstrapErrorDetail.value = '';
  bootstrapDashboardReady.value = false;
  bootstrapResourcesReady.value = false;
  dashboardLoading.value = false;
  dashboardErrorDetail.value = '';
  resourcesLoading.value = false;
  resourcesErrorDetail.value = '';
  bootstrapPending = null;
  dashboardPending = null;
  resourcesPending = null;
}

export function useWorkspaceData() {
  return {
    dashboardPayload: readonly(dashboardPayload),
    autoReverseOptions: readonly(autoReverseOptions),
    autoReverseConfig: readonly(autoReverseConfig),
    isBootstrapping: readonly(isBootstrapping),
    hasBootstrapped: readonly(hasBootstrapped),
    bootstrapDashboardReady: readonly(bootstrapDashboardReady),
    bootstrapResourcesReady: readonly(bootstrapResourcesReady),
    isWorkspaceReady: readonly(isWorkspaceReady),
    bootstrapErrorDetail: readonly(bootstrapErrorDetail),
    dashboardLoading: readonly(dashboardLoading),
    dashboardErrorDetail: readonly(dashboardErrorDetail),
    resourcesLoading: readonly(resourcesLoading),
    resourcesErrorDetail: readonly(resourcesErrorDetail),
    bootstrapWorkspaceData,
    reloadDashboard,
    reloadAutoReverseResources,
    resetWorkspaceData,
  };
}
