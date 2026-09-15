<script setup lang="ts">
import { ref } from 'vue'
import { useEditorStore } from '@/stores/editor'
import { useRouter } from 'vue-router'
import AddFieldDialog from './AddFieldDialog.vue'

const editor = useEditorStore()
const router = useRouter()
const showAddField = ref(false)

const ZOOM_STEPS = [0.33, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
function zoomIn() {
  const next = ZOOM_STEPS.find(z => z > editor.zoom)
  if (next) editor.zoom = next
}
function zoomOut() {
  const prev = [...ZOOM_STEPS].reverse().find(z => z < editor.zoom)
  if (prev) editor.zoom = prev
}
function fitPage() {
  // Try to auto-detect the editor pane width; fallback to a reasonable value
  const paneWidth = document.querySelector('.editor-canvas-pane')?.clientWidth ?? 700
  editor.zoom = Math.min(1.5, parseFloat(((paneWidth - 80) / (editor.layout?.page_width ?? 595)).toFixed(2)))
}

async function save() {
  await editor.saveLayout()
}

function goBack() {
  if (editor.isDirty && !confirm('¿Salir sin guardar los cambios?')) return
  router.push({ name: 'templates' })
}
</script>

<template>
  <div
    class="flex h-12 shrink-0 items-center gap-1 border-b border-gray-200 bg-white px-3 dark:border-gray-800 dark:bg-gray-900"
  >
    <!-- Back -->
    <button class="btn-ghost" title="Volver a plantillas" @click="goBack">← Plantillas</button>

    <div class="mx-1 h-6 w-px bg-gray-200 dark:bg-gray-700" />

    <!-- Template name -->
    <span class="truncate text-sm font-semibold text-gray-700 dark:text-gray-200" style="max-width:200px">
      {{ editor.template?.name ?? '…' }}
    </span>
    <span
      v-if="editor.isDirty"
      class="ml-1 rounded bg-yellow-100 px-1.5 py-0.5 text-[10px] font-bold text-yellow-700"
    >NO GUARDADO</span>

    <div class="mx-1 h-6 w-px bg-gray-200 dark:bg-gray-700" />

    <!-- Add field -->
    <button
      class="btn-primary h-8 text-xs"
      title="Agregar campo (A)"
      @click="showAddField = true"
    >
      + Campo
    </button>

    <div class="mx-1 h-6 w-px bg-gray-200 dark:bg-gray-700" />

    <!-- Undo / Redo -->
    <button class="btn-ghost h-8 w-8 p-0 text-base disabled:opacity-30" title="Deshacer (Ctrl+Z)" :disabled="!editor.canUndo" @click="editor.undo">↩</button>
    <button class="btn-ghost h-8 w-8 p-0 text-base disabled:opacity-30" title="Rehacer (Ctrl+Y)" :disabled="!editor.canRedo" @click="editor.redo">↪</button>

    <div class="mx-1 h-6 w-px bg-gray-200 dark:bg-gray-700" />

    <!-- Zoom controls -->
    <button class="btn-ghost h-8 w-8 p-0 text-base" title="Alejar" @click="zoomOut">−</button>
    <span class="w-12 text-center text-xs font-mono">{{ Math.round(editor.zoom * 100) }}%</span>
    <button class="btn-ghost h-8 w-8 p-0 text-base" title="Acercar" @click="zoomIn">+</button>
    <button class="btn-ghost h-8 text-xs" title="Ajustar página" @click="fitPage">⊞ Ajustar</button>

    <div class="mx-1 h-6 w-px bg-gray-200 dark:bg-gray-700" />

    <!-- Grid & Snap -->
    <label class="flex cursor-pointer items-center gap-1 text-xs select-none">
      <input v-model="editor.showGrid" type="checkbox" class="rounded" />
      Cuadrícula
    </label>
    <label class="flex cursor-pointer items-center gap-1 text-xs select-none">
      <input v-model="editor.snapToGrid" type="checkbox" class="rounded" />
      Snap
    </label>
    <select v-model.number="editor.gridSize" class="input h-7 w-16 text-xs">
      <option :value="5">5 px</option>
      <option :value="10">10 px</option>
      <option :value="20">20 px</option>
      <option :value="50">50 px</option>
    </select>

    <div class="flex-1" />

    <!-- Save -->
    <button
      class="btn-primary h-8 px-5 text-xs"
      :disabled="editor.saving"
      @click="save"
    >
      {{ editor.saving ? 'Guardando…' : '💾 Guardar' }}
    </button>
  </div>

  <AddFieldDialog :open="showAddField" @close="showAddField = false" />
</template>
