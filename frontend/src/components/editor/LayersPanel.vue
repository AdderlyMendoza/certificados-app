<script setup lang="ts">
import { useEditorStore } from '@/stores/editor'
import type { LayoutField } from '@/types'

const editor = useEditorStore()

const typeIcon: Record<string, string> = {
  text: 'T', variable: '{}', qr: '⊡', image: '🖼', signature: '✍', date: '📅', number: '#', barcode: '▐▌',
}
const typeColor: Record<string, string> = {
  text: 'text-blue-600', variable: 'text-green-600', qr: 'text-purple-600',
  image: 'text-orange-600', signature: 'text-orange-500',
  date: 'text-teal-600', number: 'text-teal-700', barcode: 'text-yellow-600',
}

// Drag to reorder
let dragFromIndex: number | null = null

function onDragStart(e: DragEvent, index: number) {
  dragFromIndex = index
  e.dataTransfer!.effectAllowed = 'move'
}
function onDrop(e: DragEvent, toIndex: number) {
  e.preventDefault()
  if (dragFromIndex !== null && dragFromIndex !== toIndex) {
    editor.moveLayer(dragFromIndex, toIndex)
  }
  dragFromIndex = null
}
function onDragOver(e: DragEvent) { e.preventDefault() }
</script>

<template>
  <div class="flex w-44 shrink-0 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
    <div class="flex items-center justify-between border-b border-gray-100 px-3 py-2 dark:border-gray-800">
      <span class="text-xs font-bold uppercase tracking-wide text-gray-500">Capas</span>
      <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600 dark:bg-gray-800">
        {{ editor.layout?.fields.length ?? 0 }}
      </span>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div
        v-if="!editor.layout?.fields.length"
        class="flex h-full items-center justify-center p-4 text-center text-xs text-gray-400"
      >
        Sin campos.<br />Usa "+ Campo" para agregar.
      </div>

      <!-- Reversed: topmost layer first in UI -->
      <div
        v-for="(field, i) in [...(editor.layout?.fields ?? [])].reverse()"
        :key="`layer-${i}`"
        draggable="true"
        :class="[
          'flex cursor-pointer items-center gap-2 border-b border-gray-100 px-3 py-2 text-xs hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800',
          editor.selectedIndex === (editor.layout!.fields.length - 1 - i)
            ? 'bg-blue-50 dark:bg-blue-900/20'
            : '',
        ]"
        @click="editor.selectField(editor.layout!.fields.length - 1 - i)"
        @dragstart="onDragStart($event, editor.layout!.fields.length - 1 - i)"
        @drop="onDrop($event, editor.layout!.fields.length - 1 - i)"
        @dragover="onDragOver"
      >
        <span class="text-sm" :class="typeColor[field.type]">{{ typeIcon[field.type] ?? '?' }}</span>
        <span class="flex-1 truncate font-mono text-[11px]">{{ field.name }}</span>
        <button
          class="ml-auto shrink-0 text-gray-300 hover:text-red-500"
          title="Eliminar"
          @click.stop="editor.removeField(editor.layout!.fields.length - 1 - i)"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Layer actions for selected field -->
    <div
      v-if="editor.selectedIndex !== null"
      class="flex items-center justify-around border-t border-gray-100 bg-gray-50 px-2 py-1.5 dark:border-gray-800 dark:bg-gray-900"
    >
      <button
        title="Subir capa"
        class="btn-ghost h-7 w-7 p-0 text-sm"
        :disabled="editor.selectedIndex === (editor.layout?.fields.length ?? 0) - 1"
        @click="editor.moveLayer(editor.selectedIndex!, editor.selectedIndex! + 1)"
      >↑</button>
      <button
        title="Bajar capa"
        class="btn-ghost h-7 w-7 p-0 text-sm"
        :disabled="editor.selectedIndex === 0"
        @click="editor.moveLayer(editor.selectedIndex!, editor.selectedIndex! - 1)"
      >↓</button>
      <button
        title="Duplicar (Ctrl+D)"
        class="btn-ghost h-7 w-7 p-0 text-base"
        @click="editor.duplicateField(editor.selectedIndex!)"
      >⎘</button>
      <button
        title="Eliminar (Del)"
        class="btn-ghost h-7 w-7 p-0 text-base text-red-400 hover:text-red-600"
        @click="editor.removeField(editor.selectedIndex!)"
      >🗑</button>
    </div>
  </div>
</template>
