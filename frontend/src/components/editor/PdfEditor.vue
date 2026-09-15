<script setup lang="ts">
import { onUnmounted } from 'vue'
import { useEditorStore } from '@/stores/editor'
import EditorToolbar from './EditorToolbar.vue'
import EditorCanvas from './EditorCanvas.vue'
import LayersPanel from './LayersPanel.vue'
import FieldProperties from './FieldProperties.vue'

const props = defineProps<{ templateId: number }>()
const editor = useEditorStore()

editor.loadTemplate(props.templateId)

onUnmounted(() => editor.reset())
</script>

<template>
  <div class="flex h-full flex-col overflow-hidden">

    <!-- Loading overlay -->
    <div
      v-if="editor.loading"
      class="absolute inset-0 z-50 flex flex-col items-center justify-center bg-white/80 dark:bg-gray-950/80"
    >
      <div class="text-4xl animate-pulse">📄</div>
      <p class="mt-3 text-sm font-medium text-gray-600">Cargando plantilla…</p>
    </div>

    <!-- Toolbar -->
    <EditorToolbar />

    <!-- Body: layers | canvas | properties -->
    <div class="flex flex-1 overflow-hidden">
      <LayersPanel />
      <div class="editor-canvas-pane flex flex-1 overflow-hidden">
        <EditorCanvas />
      </div>
      <FieldProperties />
    </div>
  </div>
</template>
