<script setup lang="ts">
defineProps<{
  rating: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  showValue?: boolean
}>()

const sizeClasses = { sm: 'text-sm', md: 'text-lg', lg: 'text-2xl' }
</script>

<template>
  <div class="flex items-center gap-1">
    <div class="flex">
      <span 
        v-for="i in (max || 5)" 
        :key="i"
        :class="['material-symbols-outlined', sizeClasses[size || 'md'], i <= rating ? 'text-amber-400' : 'text-slate-200']"
        style="font-variation-settings: 'FILL' 1"
      >star</span>
    </div>
    <span v-if="showValue" class="text-sm text-slate-600 ml-1">{{ rating }}/{{ max || 5 }}</span>
  </div>
</template>
