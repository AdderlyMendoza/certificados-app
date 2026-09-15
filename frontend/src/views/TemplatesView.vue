<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { templateService } from '@/services/template.service'
import type { Template } from '@/types'

const router = useRouter()
const templates = ref<Template[]>([])
const loading = ref(true)
const totalCount = ref(0)

// ── Upload modal state ─────────────────────────────────────────────────────
const showUpload = ref(false)
const uploadName = ref('')
const uploadCategory = ref('')
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const uploadError = ref('')

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadFile.value = file
  if (!uploadName.value) uploadName.value = file.name.replace(/\.[^.]+$/, '')
}

async function doUpload() {
  if (!uploadFile.value || !uploadName.value.trim()) {
    uploadError.value = 'Nombre y archivo son obligatorios'
    return
  }
  uploadError.value = ''
  uploading.value = true
  try {
    const tpl = await templateService.upload({
      name: uploadName.value.trim(),
      category: uploadCategory.value.trim() || undefined,
      file: uploadFile.value,
    })
    templates.value.unshift(tpl)
    totalCount.value++
    showUpload.value = false
    uploadName.value = ''
    uploadCategory.value = ''
    uploadFile.value = null
  } catch (e: any) {
    uploadError.value = e?.response?.data?.message ?? 'Error al subir la plantilla'
  } finally {
    uploading.value = false
  }
}

// ── Load templates ─────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const page = await templateService.list()
    templates.value = page.items
    totalCount.value = page.total
  } finally {
    loading.value = false
  }
}

onMounted(load)

// ── Actions ────────────────────────────────────────────────────────────────
function openEditor(tpl: Template) {
  if (tpl.type !== 'pdf') {
    alert('El editor visual solo aplica a plantillas PDF. Las plantillas Word usan el sistema de variables automático.')
    return
  }
  router.push({ name: 'template-editor', params: { id: tpl.id } })
}

async function duplicate(tpl: Template) {
  const copy = await templateService.duplicate(tpl.id)
  templates.value.unshift(copy)
  totalCount.value++
}

async function remove(tpl: Template, index: number) {
  if (!confirm(`¿Eliminar la plantilla "${tpl.name}"?`)) return
  await templateService.remove(tpl.id)
  templates.value.splice(index, 1)
  totalCount.value--
}

// Type badge helpers
const typeBadge: Record<string, string> = {
  pdf:  'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  word: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
}
const statusBadge: Record<string, string> = {
  draft:    'bg-yellow-100 text-yellow-700',
  active:   'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-500',
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Plantillas</h2>
        <p class="text-sm text-gray-500">{{ totalCount }} plantilla{{ totalCount !== 1 ? 's' : '' }}</p>
      </div>
      <button class="btn-primary" @click="showUpload = true">+ Nueva plantilla</button>
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 4" :key="i" class="card h-14 animate-pulse" />
    </div>

    <!-- Empty -->
    <div v-else-if="templates.length === 0" class="card flex flex-col items-center gap-3 py-12 text-center">
      <span class="text-5xl">📄</span>
      <p class="text-gray-500">Aún no hay plantillas.</p>
      <button class="btn-primary" @click="showUpload = true">Subir primera plantilla</button>
    </div>

    <!-- Table -->
    <div v-else class="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">
      <table class="w-full text-left text-sm">
        <thead class="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-400 dark:bg-gray-900">
          <tr>
            <th class="px-4 py-3">Nombre</th>
            <th class="px-4 py-3">Tipo</th>
            <th class="px-4 py-3">Categoría</th>
            <th class="px-4 py-3">Variables</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(tpl, i) in templates"
            :key="tpl.id"
            class="border-t border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
          >
            <td class="px-4 py-3">
              <div class="font-medium">{{ tpl.name }}</div>
              <div class="text-xs text-gray-400">{{ tpl.original_filename }}</div>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-0.5 text-xs font-semibold uppercase" :class="typeBadge[tpl.type]">
                {{ tpl.type }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-500">{{ tpl.category ?? '—' }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="v in tpl.variables.slice(0, 5)"
                  :key="v"
                  class="rounded bg-green-50 px-1.5 py-0.5 text-[10px] font-mono text-green-700 dark:bg-green-900/20 dark:text-green-400"
                >{{v}}</span>
                <span v-if="tpl.variables.length > 5" class="text-xs text-gray-400">
                  +{{ tpl.variables.length - 5 }} más
                </span>
              </div>
            </td>
            <td class="px-4 py-3">
              <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="statusBadge[tpl.status]">
                {{ tpl.status }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  v-if="tpl.type === 'pdf'"
                  class="btn-ghost h-8 px-2 text-xs text-brand-600"
                  title="Abrir editor visual"
                  @click="openEditor(tpl)"
                >
                  ✏️ Editor
                </button>
                <button class="btn-ghost h-8 px-2 text-xs" title="Duplicar" @click="duplicate(tpl)">⎘</button>
                <button class="btn-ghost h-8 px-2 text-xs text-red-400 hover:text-red-600" title="Eliminar" @click="remove(tpl, i)">🗑</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Upload modal -->
    <Teleport to="body">
      <div
        v-if="showUpload"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showUpload = false"
      >
        <div class="card w-full max-w-md">
          <h3 class="mb-4 text-base font-bold">Subir nueva plantilla</h3>

          <div class="space-y-3">
            <div>
              <label class="mb-1 block text-sm font-medium">Nombre *</label>
              <input v-model="uploadName" class="input" placeholder="Mi certificado de asistencia" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">Categoría</label>
              <input v-model="uploadCategory" class="input" placeholder="Cursos, Diplomas…" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium">Archivo (.docx o .pdf) *</label>
              <input type="file" accept=".docx,.pdf" class="input" @change="onFileChange" />
              <p class="mt-1 text-xs text-gray-400">
                Word: usa variables <code>&#123;&#123;nombre&#125;&#125;</code>. PDF: posiciona campos en el editor visual.
              </p>
            </div>
          </div>

          <p v-if="uploadError" class="mt-3 text-sm text-red-500">{{ uploadError }}</p>

          <div class="mt-5 flex justify-end gap-2">
            <button class="btn-ghost" @click="showUpload = false">Cancelar</button>
            <button class="btn-primary" :disabled="uploading" @click="doUpload">
              {{ uploading ? 'Subiendo…' : 'Subir plantilla' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
