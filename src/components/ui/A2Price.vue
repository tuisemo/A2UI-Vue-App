<script setup lang="ts">
defineProps<{
  price: number | string
  currency?: string
  period?: string
  originalPrice?: number | string
}>()
</script>

<template>
  <div class="flex items-baseline gap-1">
    <span class="text-sm text-slate-500">{{ currency || '¥' }}</span>
    <span class="text-3xl font-bold text-slate-900">{{ price }}</span>
    <span v-if="period" class="text-sm text-slate-500">/{{ period }}</span>
    <span v-if="originalPrice" class="text-sm text-slate-400 line-through ml-2">{{ currency || '¥' }}{{ originalPrice }}</span>
  </div>
</template>
