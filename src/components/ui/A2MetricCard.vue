<script setup lang="ts">
defineProps<{
  title: string
  value: number | string
  subtitle?: string
  icon?: string
  color?: 'default' | 'success' | 'warning' | 'error' | 'info'
}>()

const colorClasses = {
  default: 'from-slate-500 to-slate-600',
  success: 'from-emerald-500 to-emerald-600',
  warning: 'from-amber-500 to-amber-600',
  error: 'from-red-500 to-red-600',
  info: 'from-blue-500 to-blue-600'
}
</script>

<template>
  <div :class="['rounded-xl p-5 text-white bg-gradient-to-br', colorClasses[color || 'default']]">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-white/80 text-sm mb-1">{{ title }}</p>
        <p class="text-3xl font-bold">{{ value }}</p>
        <p v-if="subtitle" class="text-white/60 text-sm mt-2">{{ subtitle }}</p>
      </div>
      <div v-if="icon" class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
        <span class="material-symbols-outlined text-2xl">{{ icon }}</span>
      </div>
    </div>
  </div>
</template>
