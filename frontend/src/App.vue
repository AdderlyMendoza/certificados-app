<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// Si hay token guardado, recupera el usuario al cargar
onMounted(async () => {
  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
    }
  }
})
</script>

<template>
  <RouterView />
</template>
