import axios, { type AxiosInstance } from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export const api: AxiosInstance = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// Inyecta el token de acceso en cada petición
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Manejo global de 401 -> intenta refresh, si falla redirige a login
let isRefreshing = false

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry && !isRefreshing) {
      original._retry = true
      isRefreshing = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (refresh) {
          const { data } = await axios.post(`${baseURL}/auth/refresh`, {
            refresh_token: refresh,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        }
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)
