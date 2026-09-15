<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PdfEditor from '@/components/editor/PdfEditor.vue'

const route = useRoute()
const templateId = computed(() => Number(route.params.id))
</script>

<template>
  <!-- Full viewport editor - no AppLayout sidebar/navbar -->
  <div class="fixed inset-0 z-40 flex flex-col bg-gray-100 dark:bg-gray-950">
    <PdfEditor :template-id="templateId" />
  </div>
</template>
