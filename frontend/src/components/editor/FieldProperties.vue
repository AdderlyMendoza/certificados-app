<script setup lang="ts">
import { computed } from 'vue'
import { useEditorStore } from '@/stores/editor'
import type { LayoutField, FieldType } from '@/types'

const editor = useEditorStore()
const field = computed(() => editor.selectedField)

// Debounced update: commit history only on blur/change, not on every keystroke
function update(patch: Partial<LayoutField>) {
  editor.updateSelectedField(patch)
}
function commit() {
  editor.commitFieldUpdate()
}

const isTextLike = computed(() =>
  field.value ? ['text', 'variable', 'date', 'number'].includes(field.value.type) : false
)
const hasDimensions = computed(() =>
  field.value ? ['qr', 'image', 'signature', 'barcode'].includes(field.value.type) || field.value.width != null : false
)

function setAlign(newAlign: string) {
  if (!field.value) return
  const f = field.value
  const w = f.width ?? 200
  let newX = f.x
  if (newAlign === 'center' && f.align === 'left') newX = f.x + w / 2
  else if (newAlign === 'left' && f.align === 'center') newX = f.x - w / 2
  else if (newAlign === 'right' && f.align === 'left') newX = f.x + w
  else if (newAlign === 'left' && f.align === 'right') newX = f.x - w
  else if (newAlign === 'center' && f.align === 'right') newX = f.x - w / 2
  else if (newAlign === 'right' && f.align === 'center') newX = f.x + w / 2
  update({ align: newAlign, x: newX })
  commit()
}

const FONTS = ['Helvetica', 'Times', 'Courier']
const ALIGNS = [
  { value: 'left', icon: '⫞' },
  { value: 'center', icon: '⫠' },
  { value: 'right', icon: '⫟' },
]
</script>

<template>
  <div class="flex w-64 shrink-0 flex-col border-l border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
    <div class="border-b border-gray-100 px-4 py-2 dark:border-gray-800">
      <span class="text-xs font-bold uppercase tracking-wide text-gray-500">Propiedades</span>
    </div>

    <!-- No selection -->
    <div
      v-if="!field"
      class="flex h-full items-center justify-center p-6 text-center text-xs text-gray-400"
    >
      Selecciona un campo en el canvas para editar sus propiedades.
    </div>

    <!-- Field properties -->
    <div v-else class="flex-1 overflow-y-auto space-y-0">

      <!-- Section: Identity -->
      <section class="border-b border-gray-100 p-4 space-y-2 dark:border-gray-800">
        <label class="block text-[11px] font-semibold uppercase text-gray-400">Identificación</label>

        <div>
          <label class="mb-0.5 block text-xs">Nombre / ID</label>
          <input
            :value="field.name"
            class="input text-xs"
            placeholder="nombre_campo"
            @input="update({ name: ($event.target as HTMLInputElement).value })"
            @blur="commit"
          />
        </div>

        <div v-if="field.type === 'text'">
          <label class="mb-0.5 block text-xs">Valor fijo</label>
          <input
            :value="field.value ?? ''"
            class="input text-xs"
            placeholder="Texto que aparecerá…"
            @input="update({ value: ($event.target as HTMLInputElement).value })"
            @blur="commit"
          />
        </div>
      </section>

      <!-- Section: Position & Size -->
      <section class="border-b border-gray-100 p-4 space-y-2 dark:border-gray-800">
        <label class="block text-[11px] font-semibold uppercase text-gray-400">Posición y tamaño</label>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="mb-0.5 block text-xs">X (px)</label>
            <input
              type="number"
              :value="Math.round(field.x)"
              class="input text-xs"
              @change="update({ x: +($event.target as HTMLInputElement).value }); commit()"
            />
          </div>
          <div>
            <label class="mb-0.5 block text-xs">Y (px)</label>
            <input
              type="number"
              :value="Math.round(field.y)"
              class="input text-xs"
              @change="update({ y: +($event.target as HTMLInputElement).value }); commit()"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="mb-0.5 block text-xs">Ancho</label>
            <input
              type="number"
              :value="field.width ?? ''"
              placeholder="auto"
              class="input text-xs"
              @change="update({ width: ($event.target as HTMLInputElement).value ? +($event.target as HTMLInputElement).value : null as any }); commit()"
            />
          </div>
          <div>
            <label class="mb-0.5 block text-xs">Alto</label>
            <input
              type="number"
              :value="field.height ?? ''"
              placeholder="auto"
              class="input text-xs"
              @change="update({ height: ($event.target as HTMLInputElement).value ? +($event.target as HTMLInputElement).value : null as any }); commit()"
            />
          </div>
        </div>

        <div>
          <label class="mb-0.5 block text-xs">Rotación (°)</label>
          <input
            type="number"
            :value="field.rotation"
            class="input text-xs"
            @change="update({ rotation: +($event.target as HTMLInputElement).value }); commit()"
          />
        </div>
      </section>

      <!-- Section: Typography (text-like fields only) -->
      <section v-if="isTextLike" class="border-b border-gray-100 p-4 space-y-2 dark:border-gray-800">
        <label class="block text-[11px] font-semibold uppercase text-gray-400">Tipografía</label>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="mb-0.5 block text-xs">Fuente</label>
            <select
              :value="field.font"
              class="input text-xs"
              @change="update({ font: ($event.target as HTMLSelectElement).value }); commit()"
            >
              <option v-for="f in FONTS" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
          <div>
            <label class="mb-0.5 block text-xs">Tamaño</label>
            <input
              type="number"
              :value="field.font_size"
              min="4"
              max="200"
              class="input text-xs"
              @change="update({ font_size: +($event.target as HTMLInputElement).value }); commit()"
            />
          </div>
        </div>

        <!-- Color picker + hex -->
        <div>
          <label class="mb-0.5 block text-xs">Color</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              :value="field.color"
              class="h-8 w-10 cursor-pointer rounded border border-gray-300 p-0.5"
              @input="update({ color: ($event.target as HTMLInputElement).value })"
              @change="commit"
            />
            <input
              :value="field.color"
              class="input flex-1 text-xs font-mono"
              maxlength="7"
              @input="update({ color: ($event.target as HTMLInputElement).value })"
              @blur="commit"
            />
          </div>
        </div>

        <!-- Bold / Italic / Align -->
        <div class="flex items-center gap-2">
          <button
            :class="['btn h-8 w-8 p-0 text-sm font-bold', field.bold ? 'bg-brand-600 text-white' : 'btn-ghost']"
            title="Negrita"
            @click="update({ bold: !field.bold }); commit()"
          >B</button>
          <button
            :class="['btn h-8 w-8 p-0 text-sm italic', field.italic ? 'bg-brand-600 text-white' : 'btn-ghost']"
            title="Cursiva"
            @click="update({ italic: !field.italic }); commit()"
          >I</button>
          <div class="mx-1 h-5 w-px bg-gray-200" />
          <button
            v-for="a in ALIGNS"
            :key="a.value"
            :class="['btn h-8 w-8 p-0 text-base', field.align === a.value ? 'bg-brand-600 text-white' : 'btn-ghost']"
            :title="a.value"
            @click="setAlign(a.value)"
          >{{ a.icon }}</button>
        </div>
      </section>

      <!-- Section: Page (multi-page PDFs) -->
      <section class="p-4 space-y-2">
        <label class="block text-[11px] font-semibold uppercase text-gray-400">Página</label>
        <input
          type="number"
          :value="field.page"
          min="0"
          class="input w-24 text-xs"
          @change="update({ page: +($event.target as HTMLInputElement).value }); commit()"
        />
      </section>

      <!-- Quick actions -->
      <div class="flex gap-2 border-t border-gray-100 p-3 dark:border-gray-800">
        <button
          class="btn-ghost flex-1 text-xs"
          @click="editor.duplicateField(editor.selectedIndex!)"
        >⎘ Duplicar</button>
        <button
          class="flex-1 rounded-lg border border-red-200 px-2 py-1.5 text-xs text-red-500 hover:bg-red-50 dark:border-red-900 dark:hover:bg-red-900/20"
          @click="editor.removeField(editor.selectedIndex!)"
        >🗑 Eliminar</button>
      </div>
    </div>
  </div>
</template>
