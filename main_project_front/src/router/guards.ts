import type { Router } from 'vue-router';

import { ROUTE_PATHS } from '@/constants/routes';
import { getAuthSession } from '@/utils/auth';

const isAuthenticated = (): boolean => Boolean(getAuthSession());

export const setupRouterGuards = (router: Router): void => {
  router.beforeEach((to) => {
    const authed = isAuthenticated();

    if (to.meta.requiresAuth && !authed) {
      return { path: ROUTE_PATHS.LOGIN };
    }

    if (to.path === ROUTE_PATHS.LOGIN && authed) {
      return { path: ROUTE_PATHS.HOME };
    }

    return true;
  });
};
