<script setup lang="ts">
defineProps<{
  src?: string
  name?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}>()

const sizeClasses = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-lg'
}

const getInitials = (name: string) => {
  return name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
}
</script>

<template>
  <div :class="[
    'rounded-full overflow-hidden flex items-center justify-center bg-slate-200 text-slate-600 font-semibold',
    sizeClasses[size || 'md']
  ]">
    <img v-if="src" :src="src" :alt="name" class="w-full h-full object-cover" />
    <span v-else-if="name">{{ getInitials(name) }}</span>
    <span v-else class="material-symbols-outlined">person</span>
  </div>
</template>
