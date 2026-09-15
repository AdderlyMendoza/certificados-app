import { api } from './api'
import type { DatasetPreview, Generation, Page } from '@/types'

export const generationService = {
  async list(page = 1, size = 20): Promise<Page<Generation>> {
    const { data } = await api.get<Page<Generation>>('/generations', { params: { page, size } })
    return data
  },

  async get(id: number): Promise<Generation> {
    const { data } = await api.get<Generation>(`/generations/${id}`)
    return data
  },

  async previewDataset(file: File): Promise<DatasetPreview> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<DatasetPreview>('/generations/preview-dataset', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async create(payload: { name: string; templateId: number; file: File }): Promise<Generation> {
    const form = new FormData()
    form.append('name', payload.name)
    form.append('template_id', String(payload.templateId))
    form.append('file', payload.file)
    const { data } = await api.post<Generation>('/generations', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async start(id: number): Promise<Generation> {
    const { data } = await api.post<Generation>(`/generations/${id}/start`)
    return data
  },

  async cancel(id: number): Promise<Generation> {
    const { data } = await api.post<Generation>(`/generations/${id}/cancel`)
    return data
  },

  async downloadZip(id: number, fileName: string): Promise<void> {
    const { data } = await api.get(`/generations/${id}/download`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
  },
}
