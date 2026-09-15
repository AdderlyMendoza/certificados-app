<script setup lang="ts">
import { ref, watch } from 'vue'
import { useEditorStore } from '@/stores/editor'
import type { FieldType } from '@/types'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

const editor = useEditorStore()

const FIELD_TYPES: { type: FieldType; label: string; icon: string; desc: string }[] = [
  { type: 'text',      label: 'Texto fijo',  icon: 'T',  desc: 'Texto estático que no varía' },
  { type: 'variable',  label: 'Variable',    icon: '{}', desc: 'Dato del Excel: {{nombre}}' },
  { type: 'qr',        label: 'Código QR',   icon: '⊡', desc: 'QR generado automáticamente' },
  { type: 'date',      label: 'Fecha',       icon: '📅', desc: 'Fecha dinámica del dataset' },
  { type: 'number',    label: 'Número',      icon: '#',  desc: 'Campo numérico del dataset' },
  { type: 'image',     label: 'Imagen',      icon: '🖼',  desc: 'Imagen por nombre de columna' },
  { type: 'signature', label: 'Firma',       icon: '✍',  desc: 'Imagen de firma' },
  { type: 'barcode',   label: 'Código barra',icon: '▐▌', desc: 'Código de barras (próximamente)' },
]

const step = ref<1 | 2>(1)
const selectedType = ref<FieldType>('variable')
const fieldName = ref('')
const nameError = ref('')

// Template variables (for suggestions)
const suggestions = ref<string[]>([])
watch(() => props.open, (v) => {
  if (!v) return
  step.value = 1
  fieldName.value = ''
  nameError.value = ''
  suggestions.value = editor.template?.variables ?? []
})

function selectType(type: FieldType) {
  selectedType.value = type
  step.value = 2
  // Default name
  if (type === 'text') fieldName.value = 'texto_' + (Date.now() % 1000)
  else if (type === 'qr') fieldName.value = 'qr'
  else if (type === 'date') fieldName.value = 'fecha'
  else fieldName.value = ''
}

function confirm() {
  if (!fieldName.value.trim()) { nameError.value = 'Escribe un nombre'; return }
  nameError.value = ''
  // Place field in center of the current page
  const cx = (editor.layout?.page_width ?? 595) / 2
  const cy = (editor.layout?.page_height ?? 842) / 2
  editor.addField(selectedType.value, fieldName.value.trim(), cx, cy)
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="$emit('close')"
    >
      <div class="card w-[520px] max-h-[90vh] overflow-y-auto">
        <!-- Step 1: choose type -->
        <template v-if="step === 1">
          <h3 class="mb-4 text-base font-bold">Agregar campo — elegir tipo</h3>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="ft in FIELD_TYPES"
              :key="ft.type"
              class="flex items-start gap-3 rounded-lg border border-gray-200 p-3 text-left hover:border-brand-500 hover:bg-brand-50 dark:border-gray-700 dark:hover:border-brand-500 dark:hover:bg-brand-900/20"
              @click="selectType(ft.type)"
            >
              <span class="mt-0.5 text-xl">{{ ft.icon }}</span>
              <div>
                <div class="text-sm font-semibold">{{ ft.label }}</div>
                <div class="text-xs text-gray-500">{{ ft.desc }}</div>
              </div>
            </button>
          </div>
          <div class="mt-4 flex justify-end">
            <button class="btn-ghost" @click="$emit('close')">Cancelar</button>
          </div>
        </template>

        <!-- Step 2: configure name -->
        <template v-else>
          <button class="mb-3 text-sm text-gray-500 hover:text-gray-800" @click="step = 1">← Volver</button>
          <h3 class="mb-4 text-base font-bold">
            Agregar campo: {{ FIELD_TYPES.find(f => f.type === selectedType)?.label }}
          </h3>

          <label class="mb-1 block text-sm font-medium">
            {{ selectedType === 'text' ? 'ID del campo' : 'Nombre de variable / columna Excel' }}
          </label>
          <input v-model="fieldName" class="input" placeholder="ej: nombre" @keydown.enter="confirm" />
          <p v-if="nameError" class="mt-1 text-xs text-red-500">{{ nameError }}</p>

          <!-- Suggestions from detected variables -->
          <div v-if="suggestions.length && selectedType !== 'text'" class="mt-2">
            <p class="mb-1 text-xs text-gray-500">Variables detectadas en la plantilla:</p>
            <div class="flex flex-wrap gap-1">
              <button
                v-for="v in suggestions"
                :key="v"
                class="rounded border border-green-300 bg-green-50 px-2 py-0.5 text-xs text-green-700 hover:bg-green-100"
                @click="fieldName = v"
              >
                {{ v }}
              </button>
            </div>
          </div>

          <div class="mt-5 flex justify-end gap-2">
            <button class="btn-ghost" @click="$emit('close')">Cancelar</button>
            <button class="btn-primary" @click="confirm">Agregar</button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>
