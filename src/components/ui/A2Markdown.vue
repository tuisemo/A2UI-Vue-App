<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
}>()

const html = computed(() => {
  return marked(props.content || '', { breaks: true })
})
</script>

<template>
  <div 
    class="prose prose-slate max-w-none prose-headings:font-semibold prose-a:text-blue-600"
    v-html="html"
  ></div>
</template>

<style scoped>
.prose :deep(h1) { @apply text-2xl font-bold mb-4; }
.prose :deep(h2) { @apply text-xl font-semibold mb-3; }
.prose :deep(h3) { @apply text-lg font-medium mb-2; }
.prose :deep(p) { @apply mb-4 leading-relaxed; }
.prose :deep(ul) { @apply list-disc pl-5 mb-4; }
.prose :deep(ol) { @apply list-decimal pl-5 mb-4; }
.prose :deep(li) { @apply mb-1; }
.prose :deep(code) { @apply bg-slate-100 px-1.5 py-0.5 rounded text-sm; }
.prose :deep(pre) { @apply bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto mb-4; }
.prose :deep(blockquote) { @apply border-l-4 border-slate-300 pl-4 italic text-slate-600; }
</style>
