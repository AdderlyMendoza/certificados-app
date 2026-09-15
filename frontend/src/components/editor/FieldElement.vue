<script setup lang="ts">
import { computed, ref } from 'vue'
import { useEditorStore } from '@/stores/editor'
import type { LayoutField } from '@/types'

const props = defineProps<{
  field: LayoutField
  index: number
  selected: boolean
}>()

const emit = defineEmits<{
  select: []
  move: [dx: number, dy: number]
  resize: [x: number, y: number, w: number, h: number]
  moveEnd: []
}>()

const editor = useEditorStore()

// ── Appearance helpers ─────────────────────────────────────────────────────
const typeColor: Record<string, string> = {
  text:      'border-blue-500',
  variable:  'border-green-500',
  qr:        'border-purple-500',
  image:     'border-orange-500',
  signature: 'border-orange-400',
  date:      'border-teal-500',
  number:    'border-teal-600',
  barcode:   'border-yellow-600',
}
const typeBg: Record<string, string> = {
  text:      'bg-blue-50/80',
  variable:  'bg-green-50/80',
  qr:        'bg-purple-50/80',
  image:     'bg-orange-50/80',
  signature: 'bg-orange-50/80',
  date:      'bg-teal-50/80',
  number:    'bg-teal-50/80',
  barcode:   'bg-yellow-50/80',
}
const typeIcon: Record<string, string> = {
  text: 'T', variable: '{}', qr: '⊡', image: '🖼', signature: '✍', date: '📅', number: '#', barcode: '▐▌',
}

const borderClass = computed(() => typeColor[props.field.type] ?? 'border-gray-400')
const bgClass = computed(() => typeBg[props.field.type] ?? 'bg-gray-50/80')

const displayLabel = computed(() => {
  const f = props.field
  if (f.type === 'text') return f.value || '— texto fijo —'
  if (f.type === 'variable' || f.type === 'date' || f.type === 'number') return `{{${f.name}}}`
  if (f.type === 'qr') return `QR: ${f.name}`
  if (f.type === 'image') return `IMG: ${f.name}`
  if (f.type === 'signature') return `FIRMA: ${f.name}`
  if (f.type === 'barcode') return `BC: ${f.name}`
  return f.name
})

const fieldStyle = computed(() => {
  const f = props.field
  let left = f.x
  if (['center', 'right'].includes(f.align) && f.width) {
    left = f.align === 'center' ? f.x - f.width / 2 : f.x - f.width
  }
  return {
    left: `${left}px`,
    top: `${f.y}px`,
    width: f.width ? `${f.width}px` : 'auto',
    height: f.height ? `${f.height}px` : 'auto',
    minWidth: '40px',
    minHeight: '20px',
    transform: f.rotation ? `rotate(${f.rotation}deg)` : undefined,
    zIndex: props.selected ? 10 : props.index + 1,
  }
})

const textStyle = computed(() => {
  const f = props.field
  if (!['text', 'variable', 'date', 'number'].includes(f.type)) return {}
  return {
    fontFamily: f.font,
    fontSize: `${f.font_size}px`,
    color: f.color,
    fontWeight: f.bold ? 'bold' : 'normal',
    fontStyle: f.italic ? 'italic' : 'normal',
    textAlign: f.align as any,
    lineHeight: 1.2,
  }
})

// ── Drag logic ─────────────────────────────────────────────────────────────
let dragging = false
let startX = 0, startY = 0, startFx = 0, startFy = 0

function onPointerDown(e: PointerEvent) {
  if ((e.target as HTMLElement).dataset.handle) return
  e.preventDefault()
  emit('select')
  dragging = true
  startX = e.clientX
  startY = e.clientY
  startFx = props.field.x
  startFy = props.field.y
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!dragging) return
  const dxScreen = e.clientX - startX
  const dyScreen = e.clientY - startY
  const dx = dxScreen / editor.zoom
  const dy = dyScreen / editor.zoom
  emit('move', editor.snap(startFx + dx) - props.field.x, editor.snap(startFy + dy) - props.field.y)
}

function onPointerUp() {
  if (!dragging) return
  dragging = false
  emit('moveEnd')
}

// ── Resize handles ─────────────────────────────────────────────────────────
type HandleDir = 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw'

const HANDLES: { dir: HandleDir; style: string }[] = [
  { dir: 'n',  style: 'top-[-4px] left-1/2 -translate-x-1/2 cursor-n-resize' },
  { dir: 'ne', style: 'top-[-4px] right-[-4px] cursor-ne-resize' },
  { dir: 'e',  style: 'top-1/2 right-[-4px] -translate-y-1/2 cursor-e-resize' },
  { dir: 'se', style: 'bottom-[-4px] right-[-4px] cursor-se-resize' },
  { dir: 's',  style: 'bottom-[-4px] left-1/2 -translate-x-1/2 cursor-s-resize' },
  { dir: 'sw', style: 'bottom-[-4px] left-[-4px] cursor-sw-resize' },
  { dir: 'w',  style: 'top-1/2 left-[-4px] -translate-y-1/2 cursor-w-resize' },
  { dir: 'nw', style: 'top-[-4px] left-[-4px] cursor-nw-resize' },
]

let resizing: HandleDir | null = null
let resizeStart = { x: 0, y: 0, fx: 0, fy: 0, fw: 0, fh: 0 }

function onHandlePointerDown(e: PointerEvent, dir: HandleDir) {
  e.preventDefault()
  e.stopPropagation()
  resizing = dir
  resizeStart = {
    x: e.clientX,
    y: e.clientY,
    fx: props.field.x,
    fy: props.field.y,
    fw: props.field.width ?? 150,
    fh: props.field.height ?? 30,
  }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onHandlePointerMove(e: PointerEvent, dir: HandleDir) {
  if (resizing !== dir) return
  const dx = (e.clientX - resizeStart.x) / editor.zoom
  const dy = (e.clientY - resizeStart.y) / editor.zoom

  let { fx, fy, fw, fh } = resizeStart

  if (dir.includes('e')) fw = Math.max(20, editor.snap(fw + dx))
  if (dir.includes('s')) fh = Math.max(10, editor.snap(fh + dy))
  if (dir.includes('w')) { const nw = Math.max(20, editor.snap(fw - dx)); fx = editor.snap(fx + (fw - nw)); fw = nw }
  if (dir.includes('n')) { const nh = Math.max(10, editor.snap(fh - dy)); fy = editor.snap(fy + (fh - nh)); fh = nh }

  // Para campos centrados, mantener x como punto central
  if (props.field.align === 'center' && dir.includes('w')) {
    const oldCenter = resizeStart.fx + resizeStart.fw / 2
    fx = editor.snap(oldCenter - fw / 2)
  }

  emit('resize', fx, fy, fw, fh)
}

function onHandlePointerUp() {
  if (!resizing) return
  resizing = null
  emit('moveEnd')
}
</script>

<template>
  <div
    class="absolute select-none"
    :style="fieldStyle"
    :class="['border', borderClass, selected ? 'ring-2 ring-offset-1 ring-blue-400' : 'border-dashed']"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
  >
    <!-- Field content preview -->
    <div
      class="h-full w-full overflow-hidden rounded-sm px-1 py-0.5 text-xs"
      :class="bgClass"
      :style="textStyle"
    >
      <span v-if="['qr'].includes(field.type)" class="flex h-full items-center justify-center gap-1 text-purple-700">
        <span class="text-lg">⊡</span>
        <span class="text-[10px] font-mono">{{ displayLabel }}</span>
      </span>
      <span v-else-if="['image', 'signature'].includes(field.type)"
        class="flex h-full items-center justify-center gap-1 text-orange-600">
        <span>{{ typeIcon[field.type] }}</span>
        <span class="text-[10px]">{{ displayLabel }}</span>
      </span>
      <span v-else class="block truncate">{{ displayLabel }}</span>
    </div>

    <!-- Type badge (top-left, only when selected) -->
    <div
      v-if="selected"
      class="absolute -top-5 left-0 rounded-t px-1.5 py-0.5 text-[9px] font-bold text-white"
      :class="borderClass.replace('border-', 'bg-')"
    >
      {{ typeIcon[field.type] }} {{ field.type }}
    </div>

    <!-- Resize handles (only when selected and has explicit dimensions) -->
    <template v-if="selected">
      <div
        v-for="h in HANDLES"
        :key="h.dir"
        :data-handle="h.dir"
        class="absolute h-2.5 w-2.5 rounded-full border-2 border-white bg-blue-500 shadow"
        :class="h.style"
        @pointerdown.stop="onHandlePointerDown($event, h.dir)"
        @pointermove.stop="onHandlePointerMove($event, h.dir)"
        @pointerup.stop="onHandlePointerUp"
      />
    </template>
  </div>
</template>
