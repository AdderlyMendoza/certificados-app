<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from '@/services/api'
import { generationService } from '@/services/generation.service'
import { templateService } from '@/services/template.service'
import type { Generation, Template, DatasetPreview } from '@/types'

const generations = ref<Generation[]>([])
const templates = ref<Template[]>([])
const loading = ref(true)
let pollTimer: ReturnType<typeof setInterval> | null = null

// ── Wizard state ───────────────────────────────────────────────────────────
const showWizard = ref(false)
const wizardStep = ref<1 | 2 | 3>(1)
const genName = ref('')
const selectedTemplateId = ref<number | null>(null)
const datasetFile = ref<File | null>(null)
const datasetPreview = ref<DatasetPreview | null>(null)
const previewLoading = ref(false)
const creating = ref(false)
const wizardError = ref('')

const selectedTemplate = computed(() =>
  templates.value.find(t => t.id === selectedTemplateId.value) ?? null
)

function openWizard() {
  wizardStep.value = 1
  genName.value = ''
  selectedTemplateId.value = null
  datasetFile.value = null
  datasetPreview.value = null
  wizardError.value = ''
  showWizard.value = true
}

async function onDatasetChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  datasetFile.value = file
  datasetPreview.value = null
  previewLoading.value = true
  try {
    datasetPreview.value = await generationService.previewDataset(file)
  } catch {
    wizardError.value = 'No se pudo leer el archivo'
  } finally {
    previewLoading.value = false
  }
}

async function createAndStart() {
  if (!genName.value.trim() || !selectedTemplateId.value || !datasetFile.value) {
    wizardError.value = 'Completa todos los campos'
    return
  }
  wizardError.value = ''
  creating.value = true
  try {
    const gen = await generationService.create({
      name: genName.value.trim(),
      templateId: selectedTemplateId.value,
      file: datasetFile.value,
    })
    generations.value.unshift(gen)
    await generationService.start(gen.id)
    generations.value[0] = await generationService.get(gen.id)
    showWizard.value = false
    startPolling()
  } catch (e: any) {
    wizardError.value = e?.response?.data?.message ?? 'Error al crear la generación'
  } finally {
    creating.value = false
  }
}

// ── Polling progress ───────────────────────────────────────────────────────
function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    const active = generations.value.filter(g => ['pending', 'processing'].includes(g.status))
    if (active.length === 0) { stopPolling(); return }
    for (const gen of active) {
      const updated = await generationService.get(gen.id)
      const idx = generations.value.findIndex(g => g.id === gen.id)
      if (idx !== -1) generations.value[idx] = updated
    }
  }, 2500)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function cancelGen(gen: Generation) {
  await generationService.cancel(gen.id)
  const idx = generations.value.findIndex(g => g.id === gen.id)
  if (idx !== -1) generations.value[idx] = await generationService.get(gen.id)
}

async function downloadZip(gen: Generation) {
  await generationService.downloadZip(gen.id, `${gen.name}.zip`)
}

async function downloadTemplate() {
  const { data } = await api.get('/generations/template-download', { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'plantilla_generacion.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  try {
    const [genPage, tplPage] = await Promise.all([
      generationService.list(),
      templateService.list(1, 100),
    ])
    generations.value = genPage.items
    templates.value = tplPage.items
    const hasActive = genPage.items.some(g => ['pending', 'processing'].includes(g.status))
    if (hasActive) startPolling()
  } finally {
    loading.value = false
  }
})
onUnmounted(stopPolling)

// ── Helpers ────────────────────────────────────────────────────────────────
const statusColor: Record<string, string> = {
  pending:    'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  processing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed:  'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  failed:     'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  cancelled:  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
}
</script>

<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-2xl font-bold">Generaciones</h2>
      <div class="flex gap-2">
        <button class="btn-ghost" @click="downloadTemplate">📥 Descargar plantilla Excel</button>
        <button class="btn-primary" @click="openWizard">+ Nueva generación</button>
      </div>
    </div>

    <!-- Skeletons -->
    <div v-if="loading" class="space-y-2">
      <div v-for="i in 3" :key="i" class="card h-20 animate-pulse" />
    </div>

    <!-- Empty -->
    <div v-else-if="generations.length === 0" class="card flex flex-col items-center gap-3 py-12 text-center">
      <span class="text-5xl">⚙️</span>
      <p class="text-gray-500">Aún no hay generaciones.</p>
      <button class="btn-primary" @click="openWizard">Crear primera generación</button>
    </div>

    <!-- List -->
    <div v-else class="space-y-3">
      <div
        v-for="gen in generations"
        :key="gen.id"
        class="card"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-semibold truncate">{{ gen.name }}</span>
              <span class="rounded-full px-2 py-0.5 text-[11px] font-medium shrink-0" :class="statusColor[gen.status]">
                {{ gen.status }}
              </span>
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ gen.processed_rows }} / {{ gen.total_rows }} documentos
              <span v-if="gen.failed_rows" class="ml-2 text-red-500">· {{ gen.failed_rows }} errores</span>
            </div>

            <!-- Progress bar (active) -->
            <div
              v-if="gen.status === 'processing' || gen.status === 'pending'"
              class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gray-200"
            >
              <div
                class="h-full rounded-full bg-blue-500 transition-all duration-500"
                :style="{ width: gen.total_rows > 0 ? `${(gen.processed_rows / gen.total_rows) * 100}%` : '5%' }"
              />
            </div>
          </div>

          <!-- Actions -->
          <div class="flex shrink-0 items-center gap-1">
            <button
              v-if="gen.status === 'completed' && gen.zip_path"
              class="btn-primary h-8 px-3 text-xs"
              title="Descargar ZIP"
              @click="downloadZip(gen)"
            >⬇ ZIP</button>
            <button
              v-if="['pending','processing'].includes(gen.status)"
              class="btn-ghost h-8 px-3 text-xs text-red-500"
              @click="cancelGen(gen)"
            >✕ Cancelar</button>
          </div>
        </div>

        <p v-if="gen.error_message" class="mt-2 rounded bg-red-50 px-3 py-1.5 text-xs text-red-600 dark:bg-red-900/20">
          {{ gen.error_message }}
        </p>
      </div>
    </div>

    <!-- ── Wizard modal ─────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showWizard"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showWizard = false"
      >
        <div class="card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <!-- Steps indicator -->
          <div class="mb-5 flex items-center gap-2 text-xs font-semibold">
            <span v-for="n in 3" :key="n" :class="['flex h-6 w-6 items-center justify-center rounded-full',
              wizardStep === n ? 'bg-brand-600 text-white' : wizardStep > n ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500']">
              {{ wizardStep > n ? '✓' : n }}
            </span>
            <span class="ml-1 text-gray-500">
              {{ wizardStep === 1 ? 'Configuración' : wizardStep === 2 ? 'Dataset' : 'Confirmar' }}
            </span>
          </div>

          <!-- Step 1: name + template -->
          <template v-if="wizardStep === 1">
            <h3 class="mb-4 text-base font-bold">Nueva generación</h3>
            <div class="space-y-3">
              <div>
                <label class="mb-1 block text-sm font-medium">Nombre de la generación *</label>
                <input v-model="genName" class="input" placeholder="Certificados mayo 2026" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium">Plantilla *</label>
                <select v-model.number="selectedTemplateId" class="input">
                  <option :value="null" disabled>Elige una plantilla…</option>
                  <option v-for="t in templates" :key="t.id" :value="t.id">
                    [{{ t.type.toUpperCase() }}] {{ t.name }}
                  </option>
                </select>
              </div>

              <!-- Show variables of selected template -->
              <div v-if="selectedTemplate?.variables.length">
                <p class="mb-1 text-xs text-gray-500">Variables en la plantilla (deben coincidir con columnas del Excel):</p>
                <div class="flex flex-wrap gap-1">
                  <code
                    v-for="v in selectedTemplate.variables"
                    :key="v"
                    class="rounded bg-green-50 px-2 py-0.5 text-xs text-green-700 dark:bg-green-900/20"
                  >{{v}}</code>
                </div>
              </div>
            </div>
            <div class="mt-5 flex justify-end gap-2">
              <button class="btn-ghost" @click="showWizard = false">Cancelar</button>
              <button
                class="btn-primary"
                :disabled="!genName.trim() || !selectedTemplateId"
                @click="wizardStep = 2"
              >Siguiente →</button>
            </div>
          </template>

          <!-- Step 2: upload dataset -->
          <template v-else-if="wizardStep === 2">
            <h3 class="mb-4 text-base font-bold">Subir dataset (Excel/CSV/ODS)</h3>
            <p class="mb-3 text-xs text-gray-500">
              ¿No tienes el archivo?
              <button class="text-brand-600 underline" @click="downloadTemplate">Descargar plantilla de ejemplo</button>
            </p>
            <input type="file" accept=".xlsx,.xls,.csv,.ods" class="input" @change="onDatasetChange" />

            <div v-if="previewLoading" class="mt-4 animate-pulse text-sm text-gray-500">Analizando archivo…</div>

            <div v-if="datasetPreview" class="mt-4">
              <!-- Errors -->
              <div v-if="datasetPreview.errors.length" class="mb-2 space-y-1">
                <p v-for="err in datasetPreview.errors" :key="err" class="text-xs text-red-500">⚠️ {{ err }}</p>
              </div>

              <!-- Columns detected -->
              <p class="mb-1 text-xs font-medium text-gray-600">
                {{ datasetPreview.total_rows }} filas · {{ datasetPreview.columns.length }} columnas detectadas:
              </p>
              <div class="mb-3 flex flex-wrap gap-1">
                <span
                  v-for="col in datasetPreview.columns"
                  :key="col"
                  class="rounded bg-blue-50 px-2 py-0.5 text-xs font-mono text-blue-700 dark:bg-blue-900/20"
                >{{ col }}</span>
              </div>

              <!-- Preview table -->
              <div class="overflow-x-auto rounded border border-gray-200 dark:border-gray-700">
                <table class="w-full text-xs">
                  <thead class="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th v-for="col in datasetPreview.columns" :key="col" class="px-2 py-1.5 text-left font-semibold">
                        {{ col }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(row, ri) in datasetPreview.rows"
                      :key="ri"
                      class="border-t border-gray-100 dark:border-gray-800"
                    >
                      <td v-for="col in datasetPreview.columns" :key="col" class="px-2 py-1 truncate max-w-[120px]">
                        {{ row[col] ?? '' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="mt-5 flex justify-end gap-2">
              <button class="btn-ghost" @click="wizardStep = 1">← Volver</button>
              <button
                class="btn-primary"
                :disabled="!datasetPreview || !!datasetPreview.errors.length"
                @click="wizardStep = 3"
              >Siguiente →</button>
            </div>
          </template>

          <!-- Step 3: confirm -->
          <template v-else>
            <h3 class="mb-4 text-base font-bold">Confirmar y generar</h3>
            <div class="space-y-2 rounded-lg bg-gray-50 p-4 text-sm dark:bg-gray-800">
              <div class="flex justify-between"><span class="text-gray-500">Nombre</span><span class="font-medium">{{ genName }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">Plantilla</span><span class="font-medium">{{ selectedTemplate?.name }}</span></div>
              <div class="flex justify-between"><span class="text-gray-500">Documentos a generar</span><span class="font-bold text-brand-600">{{ datasetPreview?.total_rows }}</span></div>
            </div>
            <p class="mt-3 text-xs text-gray-500">
              Se generará un PDF por cada fila. Puedes monitorear el progreso en esta pantalla y descargar el ZIP cuando termine.
            </p>

            <p v-if="wizardError" class="mt-2 text-sm text-red-500">{{ wizardError }}</p>

            <div class="mt-5 flex justify-end gap-2">
              <button class="btn-ghost" @click="wizardStep = 2">← Volver</button>
              <button class="btn-primary" :disabled="creating" @click="createAndStart">
                {{ creating ? 'Generando…' : '⚡ Iniciar generación' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>
