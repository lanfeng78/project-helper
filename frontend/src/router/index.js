import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginPage.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterPage.vue') },
  { path: '/analyze/:id', name: 'Analyze', component: () => import('@/views/AnalyzePage.vue') },
  { path: '/report/:id', name: 'Report', component: () => import('@/views/ReportPage.vue') },
  { path: '/qa/:id', name: 'QA', component: () => import('@/views/QAPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const PUBLIC_ROUTES = new Set(['Home', 'Login', 'Register'])

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && auth.refreshToken) {
    await auth.tryRestoreSession()
  }

  if (!PUBLIC_ROUTES.has(to.name) && !auth.user) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (auth.user && (to.name === 'Login' || to.name === 'Register')) {
    return { name: 'Home' }
  }
})

export default router
