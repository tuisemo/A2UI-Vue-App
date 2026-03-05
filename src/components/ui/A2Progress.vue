<script setup lang="ts">
defineProps<{
  value: number
  max?: number
  showLabel?: boolean
  color?: 'primary' | 'success' | 'warning' | 'error'
}>()

const colorClasses = {
  primary: 'bg-slate-900 shadow-[0_0_12px_rgba(15,23,42,0.4)]',
  success: 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.5)]',
  warning: 'bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.6)]',
  error: 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.5)]'
}
</script>

<template>
  <div class="w-full">
    <div class="flex justify-between items-baseline mb-2" v-if="showLabel">
      <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Progress</span>
      <span class="text-sm font-bold text-slate-900">{{ Math.round(value / (max || 100) * 100) }}%</span>
    </div>
    <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden ring-1 ring-inset ring-slate-900/5">
      <div 
        :class="['h-full transition-all duration-700 ease-out rounded-full', colorClasses[color || 'primary']]"
        :style="{ width: `${(value / (max || 100)) * 100}%` }"
      ></div>
    </div>
  </div>
</template>
