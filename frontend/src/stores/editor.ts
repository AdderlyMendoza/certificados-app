import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'
import { templateService } from '@/services/template.service'
import type { Template, TemplateLayout, LayoutField, FieldType } from '@/types'

function defaultField(type: FieldType, name: string, cx: number, cy: number): LayoutField {
  const base: LayoutField = {
    name,
    type,
    page: 0,
    x: cx - 75,
    y: cy - 15,
    font: 'Helvetica',
    font_size: 16,
    color: '#000000',
    bold: false,
    italic: false,
    align: 'left',
    rotation: 0,
    value: null,
  }
  if (type === 'qr') {
    return { ...base, x: cx - 50, y: cy - 50, width: 100, height: 100 }
  }
  if (type === 'image' || type === 'signature') {
    return { ...base, x: cx - 60, y: cy - 40, width: 120, height: 80 }
  }
  return { ...base, width: 200, height: 30 }
}

export const useEditorStore = defineStore('editor', () => {
  const template = ref<Template | null>(null)
  const layout = ref<TemplateLayout | null>(null)
  const previewUrl = ref<string | null>(null)

  const selectedIndex = ref<number | null>(null)
  const zoom = ref(1.0)
  const showGrid = ref(true)
  const snapToGrid = ref(true)
  const gridSize = ref(10)
  const loading = ref(false)
  const saving = ref(false)
  const isDirty = ref(false)

  // History for undo
  const history = ref<TemplateLayout[]>([])
  const historyIndex = ref(-1)

  const selectedField = computed<LayoutField | null>(() => {
    if (selectedIndex.value === null || !layout.value) return null
    return layout.value.fields[selectedIndex.value] ?? null
  })

  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  async function loadTemplate(id: number) {
    loading.value = true
    try {
      template.value = await templateService.get(id)
      layout.value = template.value.layout
        ? JSON.parse(JSON.stringify(template.value.layout))
        : { page_width: 595, page_height: 842, fields: [] }

      // Load PDF preview as blob → object URL (avoids auth header issues with <img>)
      const resp = await api.get(`/templates/${id}/preview?page=0`, { responseType: 'blob' })
      if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = URL.createObjectURL(resp.data)

      pushHistory()
    } finally {
      loading.value = false
    }
  }

  function selectField(index: number | null) {
    selectedIndex.value = index
  }

  function addField(type: FieldType, name: string, cx: number, cy: number) {
    if (!layout.value) return
    const field = defaultField(type, name, cx, cy)
    layout.value.fields.push(field)
    selectedIndex.value = layout.value.fields.length - 1
    isDirty.value = true
    pushHistory()
  }

  function updateSelectedField(patch: Partial<LayoutField>) {
    if (selectedIndex.value === null || !layout.value) return
    Object.assign(layout.value.fields[selectedIndex.value], patch)
    isDirty.value = true
  }

  function commitFieldUpdate() {
    pushHistory()
  }

  function removeField(index: number) {
    if (!layout.value) return
    layout.value.fields.splice(index, 1)
    if (selectedIndex.value !== null) {
      if (selectedIndex.value >= layout.value.fields.length) {
        selectedIndex.value = layout.value.fields.length - 1
      }
      if (selectedIndex.value < 0) selectedIndex.value = null
    }
    isDirty.value = true
    pushHistory()
  }

  function duplicateField(index: number) {
    if (!layout.value) return
    const src = layout.value.fields[index]
    const copy: LayoutField = { ...JSON.parse(JSON.stringify(src)), x: src.x + 15, y: src.y + 15 }
    layout.value.fields.splice(index + 1, 0, copy)
    selectedIndex.value = index + 1
    isDirty.value = true
    pushHistory()
  }

  function moveLayer(fromIndex: number, toIndex: number) {
    if (!layout.value) return
    const [item] = layout.value.fields.splice(fromIndex, 1)
    layout.value.fields.splice(toIndex, 0, item)
    selectedIndex.value = toIndex
    isDirty.value = true
    pushHistory()
  }

  async function saveLayout() {
    if (!template.value || !layout.value) return
    saving.value = true
    try {
      await templateService.update(template.value.id, { layout: layout.value })
      isDirty.value = false
    } finally {
      saving.value = false
    }
  }

  function undo() {
    if (!canUndo.value) return
    historyIndex.value--
    layout.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
    isDirty.value = true
    selectedIndex.value = null
  }

  function redo() {
    if (!canRedo.value) return
    historyIndex.value++
    layout.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
    isDirty.value = true
    selectedIndex.value = null
  }

  function pushHistory() {
    if (!layout.value) return
    history.value = history.value.slice(0, historyIndex.value + 1)
    history.value.push(JSON.parse(JSON.stringify(layout.value)))
    historyIndex.value = history.value.length - 1
  }

  function snap(value: number): number {
    if (!snapToGrid.value) return value
    return Math.round(value / gridSize.value) * gridSize.value
  }

  function reset() {
    template.value = null
    layout.value = null
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
    selectedIndex.value = null
    zoom.value = 1.0
    isDirty.value = false
    history.value = []
    historyIndex.value = -1
  }

  return {
    template, layout, previewUrl, selectedIndex, selectedField,
    zoom, showGrid, snapToGrid, gridSize,
    loading, saving, isDirty, canUndo, canRedo,
    loadTemplate, selectField, addField, updateSelectedField, commitFieldUpdate,
    removeField, duplicateField, moveLayer, saveLayout, undo, redo, snap, reset,
  }
})
