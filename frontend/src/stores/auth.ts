import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email: string, password: string): Promise<void> {
    const token = await authService.login(email, password)
    localStorage.setItem('access_token', token.access_token)
    localStorage.setItem('refresh_token', token.refresh_token)
    accessToken.value = token.access_token
    await fetchMe()
  }

  async function fetchMe(): Promise<void> {
    user.value = await authService.me()
  }

  function logout(): void {
    user.value = null
    accessToken.value = null
    localStorage.clear()
  }

  return { user, accessToken, isAuthenticated, isAdmin, login, fetchMe, logout }
})
