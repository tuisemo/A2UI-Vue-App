<script setup lang="ts">
defineProps<{
  text: string
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
}>()

const variantClasses = {
  default: 'bg-slate-100 text-slate-700',
  success: 'bg-emerald-100 text-emerald-700',
  warning: 'bg-amber-100 text-amber-700',
  error: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700'
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
