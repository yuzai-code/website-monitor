import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/website',
      name: 'Website',
      component: () => import('../views/WebsiteView.vue')
    },
    {
      path: '/website/:id',
      name: 'WebsiteDetail',
      component: () => import('../views/WebDetailView.vue')
    }
  ]
})

export default router
