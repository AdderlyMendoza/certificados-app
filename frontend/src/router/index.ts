import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/components/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'templates',
          name: 'templates',
          component: () => import('@/views/TemplatesView.vue'),
        },
        {
          path: 'generations',
          name: 'generations',
          component: () => import('@/views/GenerationsView.vue'),
        },
      ],
    },
    // Editor de plantillas: pantalla completa, sin AppLayout
    {
      path: '/templates/:id/editor',
      name: 'template-editor',
      component: () => import('@/views/TemplateEditorView.vue'),
    },
  ],
})

// Guard global de autenticación
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
