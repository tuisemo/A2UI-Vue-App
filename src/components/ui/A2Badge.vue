<script setup lang="ts">
defineProps<{
  text: string
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
}>()

const variantClasses = {
  default: 'bg-slate-50 text-slate-700 ring-1 ring-inset ring-slate-500/20',
  success: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-500/20',
  warning: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-500/20',
  error: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-500/20',
  info: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-500/20'
}
</script>

<template>
  <span :class="[
    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
    variantClasses[variant || 'default']
  ]">
    {{ text }}
  </span>
</template>
