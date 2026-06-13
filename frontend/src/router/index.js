import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/analyze/:id', name: 'Analyze', component: () => import('@/views/AnalyzePage.vue') },
  { path: '/report/:id', name: 'Report', component: () => import('@/views/ReportPage.vue') },
  { path: '/qa/:id', name: 'QA', component: () => import('@/views/QAPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
