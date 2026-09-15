import { api } from './api'
import type { Token, User } from '@/types'

export const authService = {
  async login(email: string, password: string): Promise<Token> {
    // El backend usa OAuth2PasswordRequestForm (campos username/password)
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const { data } = await api.post<Token>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },
}
