<script setup lang="ts">
defineProps<{
  tags: { label: string; color?: string }[]
}>()

const colorMap: Record<string, string> = {
  red: 'bg-red-100 text-red-700',
  green: 'bg-emerald-100 text-emerald-700',
  blue: 'bg-blue-100 text-blue-700',
  yellow: 'bg-amber-100 text-amber-700',
  purple: 'bg-purple-100 text-purple-700',
  pink: 'bg-pink-100 text-pink-700',
  default: 'bg-slate-100 text-slate-700'
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <span 
      v-for="tag in tags" 
      :key="tag.label"
      :class="['px-2.5 py-1 rounded-full text-xs font-medium', colorMap[tag.color || 'default']]"
    >
      {{ tag.label }}
    </span>
  </div>
</template>
