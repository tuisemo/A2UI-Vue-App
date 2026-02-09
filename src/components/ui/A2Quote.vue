<script setup lang="ts">
defineProps<{
  content: string
  author?: string
  avatar?: string
}>()
</script>

<template>
  <blockquote class="relative bg-slate-50 rounded-xl p-6 border-l-4 border-slate-900">
    <span class="absolute top-4 left-4 text-4xl text-slate-200 font-serif">"</span>
    <p class="text-slate-700 italic pl-6 pr-4">{{ content }}</p>
    <div v-if="author" class="flex items-center gap-3 mt-4 pl-6">
      <div v-if="avatar" class="w-8 h-8 rounded-full overflow-hidden bg-slate-200">
        <img :src="avatar" :alt="author" class="w-full h-full object-cover" />
      </div>
      <span class="text-sm font-medium text-slate-600">— {{ author }}</span>
    </div>
  </blockquote>
</template>
