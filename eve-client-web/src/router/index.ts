import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/profile',
    children: [
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/Profile.vue'),
        meta: { requiresAuth: true, title: '飞行员档案' },
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true, title: '控制台' },
      },
      {
        path: 'industry',
        name: 'industry',
        component: () => import('@/views/Industry.vue'),
        meta: { requiresAuth: true, title: '工业监控' },
      },
      {
        path: 'wallet',
        name: 'wallet',
        component: () => import('@/views/Wallet.vue'),
        meta: { requiresAuth: true, title: '财务中心' },
      },
      {
        path: 'assets',
        name: 'assets',
        component: () => import('@/views/Assets.vue'),
        meta: { requiresAuth: true, title: '资产清单' },
      },
      {
        path: 'market',
        name: 'market',
        component: () => import('@/views/Market.vue'),
        meta: { requiresAuth: true, title: '市场情报' },
      },
      {
        path: 'market-browser',
        name: 'market-browser',
        component: () => import('@/views/MarketBrowser.vue'),
        meta: { requiresAuth: true, title: '市场浏览器' },
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { guestOnly: true, title: '登录' },
  },
  {
    path: '/login/callback',
    name: 'login-callback',
    component: () => import('@/views/LoginCallback.vue'),
    meta: { guestOnly: true, title: '登录回调' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('eve_access_token')

  if (!['/login', '/login/callback'].includes(to.path) && !token) {
    return '/login'
  }

  if (to.meta.guestOnly && token) {
    return '/profile'
  }

  return true
})

export { router }
export default router