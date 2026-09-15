<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import type { DashboardStats } from '@/types'

const stats = ref<DashboardStats | null>(null)
const loading = ref(true)

const cards = [
  { key: 'total_certificates', label: 'Certificados generados', icon: '🏅' },
  { key: 'total_templates', label: 'Plantillas', icon: '📄' },
  { key: 'total_generations', label: 'Generaciones', icon: '⚙️' },
  { key: 'total_errors', label: 'Errores', icon: '⚠️' },
] as const

onMounted(async () => {
  try {
    const { data } = await api.get<DashboardStats>('/dashboard/stats')
    stats.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h2 class="mb-6 text-2xl font-bold">Dashboard</h2>

    <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="card h-24 animate-pulse" />
    </div>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="c in cards" :key="c.key" class="card">
        <div class="text-2xl">{{ c.icon }}</div>
        <div class="mt-2 text-3xl font-bold">{{ stats?.[c.key] ?? 0 }}</div>
        <div class="text-sm text-gray-500">{{ c.label }}</div>
      </div>
    </div>
  </div>
</template>
