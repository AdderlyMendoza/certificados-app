<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDarkMode } from '@/composables/useDarkMode'

const auth = useAuthStore()
const router = useRouter()
const { isDark, toggleDark } = useDarkMode()

const nav = [
  { name: 'dashboard', label: 'Dashboard', icon: '📊' },
  { name: 'templates', label: 'Plantillas', icon: '📄' },
  { name: 'generations', label: 'Generaciones', icon: '⚙️' },
]

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <aside
      class="flex w-60 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
    >
      <div class="flex h-16 items-center gap-2 px-5 text-lg font-bold">
        <span>🏅</span> Certificados
      </div>
      <nav class="flex-1 space-y-1 px-3">
        <RouterLink
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          active-class="bg-brand-50 text-brand-700 dark:bg-gray-800 dark:text-brand-500"
        >
          <span>{{ item.icon }}</span> {{ item.label }}
        </RouterLink>
      </nav>
      <div class="border-t border-gray-200 p-3 dark:border-gray-800">
        <button class="btn-ghost w-full justify-start" @click="logout">🚪 Salir</button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <header
        class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-800 dark:bg-gray-900"
      >
        <h1 class="text-sm font-semibold text-gray-500">
          {{ auth.user?.full_name }} · {{ auth.user?.role }}
        </h1>
        <button class="btn-ghost" @click="toggleDark()">
          {{ isDark ? '☀️' : '🌙' }}
        </button>
      </header>
      <main class="flex-1 overflow-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
