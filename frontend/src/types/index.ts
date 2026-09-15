// Tipos compartidos del dominio (espejo de los schemas del backend)

export type UserRole = 'admin' | 'operator' | 'auditor'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export type TemplateType = 'word' | 'pdf'
export type TemplateStatus = 'draft' | 'active' | 'archived'

export interface Template {
  id: number
  name: string
  description: string | null
  category: string | null
  type: TemplateType
  status: TemplateStatus
  original_filename: string
  file_size: number
  variables: string[]
  layout: TemplateLayout | null
  qr_config: QRConfig | null
  current_version: number
  owner_id: number
  created_at: string
  updated_at: string
}

export type FieldType =
  | 'text'
  | 'variable'
  | 'qr'
  | 'image'
  | 'signature'
  | 'date'
  | 'number'
  | 'barcode'

export interface LayoutField {
  name: string
  type: FieldType
  page: number
  x: number
  y: number
  width?: number | null
  height?: number | null
  font: string
  font_size: number
  color: string
  bold: boolean
  italic: boolean
  align: 'left' | 'center' | 'right'
  rotation: number
  value?: string | null
}

export interface TemplateLayout {
  page_width: number
  page_height: number
  fields: LayoutField[]
}

export interface QRConfig {
  content_type: 'text' | 'url' | 'uuid' | 'code'
  content_template: string
  size: number
  margin: number
  error_correction: 'L' | 'M' | 'Q' | 'H'
  fill_color: string
  back_color: string
}

export type GenerationStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface Generation {
  id: number
  name: string
  status: GenerationStatus
  template_id: number
  owner_id: number
  total_rows: number
  processed_rows: number
  failed_rows: number
  zip_path: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DatasetPreview {
  columns: string[]
  rows: Record<string, string>[]
  total_rows: number
  errors: string[]
}

export interface DashboardStats {
  total_templates: number
  total_generations: number
  total_certificates: number
  total_errors: number
  by_status: Record<string, number>
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}
