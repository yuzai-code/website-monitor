import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

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
      path: '/website/:id/:ip?',
      name: 'WebsiteDetail',
      component: () => import('../views/WebDetailView.vue')
    },
    {
      path: '/ip_list',
      name: 'IpList',
      component: () => import('../views/IpListView.vue')
    }
  ]
})

export default router
