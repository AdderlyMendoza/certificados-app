import { api } from './api'
import type { Page, Template, TemplateLayout, QRConfig } from '@/types'

export const templateService = {
  async list(page = 1, size = 20): Promise<Page<Template>> {
    const { data } = await api.get<Page<Template>>('/templates', { params: { page, size } })
    return data
  },

  async get(id: number): Promise<Template> {
    const { data } = await api.get<Template>(`/templates/${id}`)
    return data
  },

  async upload(payload: {
    name: string
    description?: string
    category?: string
    file: File
  }): Promise<Template> {
    const form = new FormData()
    form.append('name', payload.name)
    if (payload.description) form.append('description', payload.description)
    if (payload.category) form.append('category', payload.category)
    form.append('file', payload.file)
    const { data } = await api.post<Template>('/templates', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async update(
    id: number,
    payload: Partial<{ name: string; layout: TemplateLayout; qr_config: QRConfig }>,
  ): Promise<Template> {
    const { data } = await api.patch<Template>(`/templates/${id}`, payload)
    return data
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/templates/${id}`)
  },

  async duplicate(id: number): Promise<Template> {
    const { data } = await api.post<Template>(`/templates/${id}/duplicate`)
    return data
  },

  previewUrl(id: number, page = 0): string {
    return `${api.defaults.baseURL}/templates/${id}/preview?page=${page}`
  },
}
