<script setup lang="ts">
defineProps<{
  value: number
  max?: number
  showLabel?: boolean
  color?: 'primary' | 'success' | 'warning' | 'error'
}>()

const colorClasses = {
  primary: 'bg-slate-900',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500'
}
</script>

<template>
  <div class="w-full">
    <div class="flex justify-between mb-1" v-if="showLabel">
      <span class="text-sm text-slate-600">Progress</span>
      <span class="text-sm font-medium text-slate-900">{{ Math.round(value / (max || 100) * 100) }}%</span>
    </div>
    <div class="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
      <div 
        :class="['h-full transition-all duration-500', colorClasses[color || 'primary']]"
        :style="{ width: `${(value / (max || 100)) * 100}%` }"
      ></div>
    </div>
  </div>
</template>
