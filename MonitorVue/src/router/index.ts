import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/website',
      name: 'Website',
      component: () => import('../views/WebsiteView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/website/:id/:ip?',
      name: 'WebsiteDetail',
      component: () => import('../views/WebDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ip_list',
      name: 'IpList',
      component: () => import('../views/IpListView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/spider',
      name: 'Spider',
      component: () => import('../views/SpiderView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/total',
      name: 'Total',
      component: () => import('../views/TotalView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/RegisterView.vue')
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    // 假设使用localStorage存储认证令牌
    const isAuthenticated = localStorage.getItem('authToken')
    if (!isAuthenticated) {
      // 未认证则重定向到登录页面
      next({ name: 'Login' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
