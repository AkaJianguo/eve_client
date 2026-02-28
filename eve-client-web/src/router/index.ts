// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/Index.vue')
  },
  {
    path: '/billing',
    name: 'Billing',
    component: () => import('@/views/billing/Index.vue')
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('@/views/market/Index.vue'),
    meta: { requiresPremium: true } // 标记需要订阅的功能
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 全局守卫：处理付费订阅拦截
router.beforeEach((to, from, next) => {
  // 这里暂时写死为 true，后续对接 Pinia 的 userStore
  const isPremium = true; 

  if (to.meta.requiresPremium && !isPremium) {
    next({ name: 'Billing' });
  } else {
    next();
  }
});

export default router;