import { useUserStore } from '@/store/userStore'
import { useToast } from 'primevue/usetoast'
import { createRouter, createWebHistory } from 'vue-router'

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
      path: '/website_detail/:ip?/:date?',
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
      path: '/website_data/:domain',
      name: 'WebsiteData',
      component: () => import('../views/WebsiteDataView.vue'),
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
  const userStore = useUserStore()
  const toast = useToast()
  // 检查是否需要登录的页面
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    toast.add({
      severity: 'warn',
      summary: '警告',
      detail: '请先登陆!',
      life: 3000
    }) // 显示提示信息
    next({ name: 'Login' }) // 重定向到登录页面
  } else {
    next() // 继续导航
  }
})

export default router
