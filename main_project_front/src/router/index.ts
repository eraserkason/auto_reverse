import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

import { ROUTE_NAMES, ROUTE_PATHS } from '@/constants/routes';
import { setupRouterGuards } from '@/router/guards';
import { getAuthSession } from '@/utils/auth';


const LoginView = () => import('@/views/LoginView.vue');
const MainLayout = () => import('@/layouts/MainLayout.vue');
const HomeView = () => import('@/views/HomeView.vue');
const AutoReverseView = () => import('@/views/AutoReverseView.vue');
const AutoReverseConfigView = () => import('@/views/AutoReverseConfigView.vue');
const BrowserTaskView = () => import('@/views/BrowserTaskView.vue');
const SettingView = () => import('@/views/SettingView.vue');

const routes: RouteRecordRaw[] = [
  {
    path: ROUTE_PATHS.LOGIN,
    name: ROUTE_NAMES.LOGIN,
    component: LoginView,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: ROUTE_PATHS.ROOT,
    name: ROUTE_NAMES.ROOT,
    component: MainLayout,
    meta: {
      requiresAuth: true,
    },
    redirect: ROUTE_PATHS.HOME,
    children: [
      {
        path: ROUTE_PATHS.HOME.slice(1),
        name: ROUTE_NAMES.HOME,
        component: HomeView,
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: ROUTE_PATHS.AUTO_REVERSE.slice(1),
        name: ROUTE_NAMES.AUTO_REVERSE,
        component: AutoReverseView,
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: ROUTE_PATHS.AUTO_REVERSE_CONFIG.slice(1),
        name: ROUTE_NAMES.AUTO_REVERSE_CONFIG,
        component: AutoReverseConfigView,
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: ROUTE_PATHS.BROWSER_TASK.slice(1),
        name: ROUTE_NAMES.BROWSER_TASK,
        component: BrowserTaskView,
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: ROUTE_PATHS.SETTING.slice(1),
        name: ROUTE_NAMES.SETTING,
        component: SettingView,
        meta: {
          requiresAuth: true,
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: () => (getAuthSession() ? ROUTE_PATHS.HOME : ROUTE_PATHS.LOGIN),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

setupRouterGuards(router);

export default router;
