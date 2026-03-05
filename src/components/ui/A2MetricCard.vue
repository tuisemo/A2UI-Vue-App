<script setup lang="ts">
defineProps<{
  title: string
  value: number | string
  subtitle?: string
  icon?: string
  color?: 'default' | 'success' | 'warning' | 'error' | 'info'
}>()

const colorClasses = {
  default: { bg: 'bg-slate-50', text: 'text-slate-600', icon: 'bg-slate-100 text-slate-600 ring-slate-500/10' },
  success: { bg: 'bg-emerald-50', text: 'text-emerald-600', icon: 'bg-emerald-100 text-emerald-600 ring-emerald-500/20' },
  warning: { bg: 'bg-amber-50', text: 'text-amber-600', icon: 'bg-amber-100 text-amber-600 ring-amber-500/20' },
  error: { bg: 'bg-red-50', text: 'text-red-600', icon: 'bg-red-100 text-red-600 ring-red-500/20' },
  info: { bg: 'bg-blue-50', text: 'text-blue-600', icon: 'bg-blue-100 text-blue-600 ring-blue-500/20' }
}
</script>

<template>
  <div class="rounded-2xl p-6 bg-white ring-1 ring-slate-900/5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-slate-500 text-sm font-medium mb-1">{{ title }}</p>
        <p class="text-3xl font-bold text-slate-900 tracking-tight">{{ value }}</p>
        <div v-if="subtitle" :class="['mt-3 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold', colorClasses[color || 'default'].bg, colorClasses[color || 'default'].text]">
          {{ subtitle }}
        </div>
      </div>
      <div v-if="icon" :class="['w-12 h-12 rounded-xl flex items-center justify-center ring-1 ring-inset', colorClasses[color || 'default'].icon]">
        <span class="material-symbols-outlined text-2xl drop-shadow-sm">{{ icon }}</span>
      </div>
    </div>
  </div>
</template>
