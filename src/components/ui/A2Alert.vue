<script setup lang="ts">
defineProps<{
  title?: string
  message: string
  variant?: 'info' | 'success' | 'warning' | 'error'
  dismissible?: boolean
}>()

const emit = defineEmits<{
  (e: 'dismiss'): void
}>()

const variantClasses = {
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  error: 'bg-red-50 border-red-200 text-red-800'
}

const iconMap = {
  info: 'info',
  success: 'check_circle',
  warning: 'warning',
  error: 'error'
}
</script>

<template>
  <div :class="[
    'flex items-start gap-3 p-4 rounded-xl border',
    variantClasses[variant || 'info']
  ]">
    <span class="material-symbols-outlined text-xl">{{ iconMap[variant || 'info'] }}</span>
    <div class="flex-1">
      <h4 v-if="title" class="font-semibold mb-1">{{ title }}</h4>
      <p class="text-sm opacity-90">{{ message }}</p>
    </div>
    <button 
      v-if="dismissible" 
      @click="emit('dismiss')"
      class="opacity-60 hover:opacity-100 transition-opacity"
    >
      <span class="material-symbols-outlined text-lg">close</span>
    </button>
  </div>
</template>
