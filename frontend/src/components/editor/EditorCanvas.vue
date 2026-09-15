<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEditorStore } from '@/stores/editor'
import FieldElement from './FieldElement.vue'

const editor = useEditorStore()

// ── Canvas outer container (scroll area) ───────────────────────────────────
const outer = ref<HTMLElement | null>(null)

// ── Canvas size = PDF page size ────────────────────────────────────────────
const canvasStyle = computed(() => ({
  width: `${editor.layout?.page_width ?? 595}px`,
  height: `${editor.layout?.page_height ?? 842}px`,
  transform: `scale(${editor.zoom})`,
  transformOrigin: 'top left',
}))

const outerStyle = computed(() => ({
  width:  `${(editor.layout?.page_width  ?? 595) * editor.zoom + 80}px`,
  height: `${(editor.layout?.page_height ?? 842) * editor.zoom + 80}px`,
  minWidth: '100%',
  minHeight: '100%',
}))

// ── Keyboard shortcuts ─────────────────────────────────────────────────────
function onKeyDown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

  if ((e.key === 'Delete' || e.key === 'Backspace') && editor.selectedIndex !== null) {
    e.preventDefault()
    editor.removeField(editor.selectedIndex)
    return
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) { e.preventDefault(); editor.undo(); return }
  if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); editor.redo(); return }
  if ((e.ctrlKey || e.metaKey) && e.key === 'd' && editor.selectedIndex !== null) {
    e.preventDefault(); editor.duplicateField(editor.selectedIndex); return
  }

  // Arrow nudge
  if (editor.selectedField && ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) {
    e.preventDefault()
    const step = e.shiftKey ? 10 : 1
    const { x, y } = editor.selectedField
    editor.updateSelectedField({
      x: e.key === 'ArrowLeft' ? x - step : e.key === 'ArrowRight' ? x + step : x,
      y: e.key === 'ArrowUp'   ? y - step : e.key === 'ArrowDown'  ? y + step : y,
    })
    editor.commitFieldUpdate()
  }
}

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// ── Click on canvas background → deselect ─────────────────────────────────
function onCanvasClick(e: MouseEvent) {
  if (e.target === e.currentTarget || (e.target as HTMLElement).dataset.canvas) {
    editor.selectField(null)
  }
}

// ── Field event handlers ───────────────────────────────────────────────────
function onFieldMove(index: number, dx: number, dy: number) {
  const f = editor.layout!.fields[index]
  editor.updateSelectedField({ x: f.x + dx, y: f.y + dy })
}

function onFieldResize(index: number, x: number, y: number, w: number, h: number) {
  if (editor.selectedIndex !== index) editor.selectField(index)
  editor.updateSelectedField({ x, y, width: w, height: h })
}
</script>

<template>
  <!-- Scrollable outer region with checkerboard background -->
  <div
    ref="outer"
    class="flex-1 overflow-auto bg-[repeating-conic-gradient(#e5e7eb_0%_25%,#f9fafb_0%_50%)] bg-[length:20px_20px] p-10 dark:bg-[repeating-conic-gradient(#1f2937_0%_25%,#111827_0%_50%)]"
  >
    <div :style="outerStyle">
      <!-- The actual canvas (PDF page dimensions) -->
      <div class="relative shadow-2xl" :style="canvasStyle" @click="onCanvasClick">

        <!-- PDF background image -->
        <img
          v-if="editor.previewUrl"
          :src="editor.previewUrl"
          class="pointer-events-none absolute inset-0 h-full w-full object-fill"
          draggable="false"
          alt="PDF preview"
        />
        <div
          v-else
          class="pointer-events-none absolute inset-0 flex items-center justify-center bg-white text-gray-300"
          data-canvas
        >
          <span class="text-6xl">📄</span>
        </div>

        <!-- Grid overlay -->
        <svg
          v-if="editor.showGrid"
          class="pointer-events-none absolute inset-0 h-full w-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <pattern
              :id="`grid-${editor.gridSize}`"
              :width="editor.gridSize"
              :height="editor.gridSize"
              patternUnits="userSpaceOnUse"
            >
              <path
                :d="`M ${editor.gridSize} 0 L 0 0 0 ${editor.gridSize}`"
                fill="none"
                stroke="rgba(99,102,241,0.2)"
                stroke-width="0.5"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" :fill="`url(#grid-${editor.gridSize})`" />
        </svg>

        <!-- Page size indicator (corners) -->
        <div class="pointer-events-none absolute inset-0 border border-gray-300 dark:border-gray-600" data-canvas />

        <!-- Field elements -->
        <FieldElement
          v-for="(field, i) in editor.layout?.fields ?? []"
          :key="`${i}-${field.name}`"
          :field="field"
          :index="i"
          :selected="editor.selectedIndex === i"
          @select="editor.selectField(i)"
          @move="(dx, dy) => onFieldMove(i, dx, dy)"
          @resize="(x, y, w, h) => onFieldResize(i, x, y, w, h)"
          @move-end="editor.commitFieldUpdate()"
        />

        <!-- Ruler: top -->
        <svg
          class="pointer-events-none absolute left-0 top-0 h-5 w-full"
          style="margin-top:-20px"
        >
          <template v-for="tick in Math.floor((editor.layout?.page_width ?? 595) / 50)" :key="tick">
            <line :x1="tick*50" y1="10" :x2="tick*50" y2="20" stroke="#9ca3af" stroke-width="0.5"/>
            <text :x="tick*50+2" y="10" font-size="7" fill="#9ca3af">{{ tick * 50 }}</text>
          </template>
        </svg>
      </div>
    </div>
  </div>
</template>
