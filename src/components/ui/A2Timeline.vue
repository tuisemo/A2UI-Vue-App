<script setup lang="ts">
defineProps<{
  items: { time: string; title: string; description?: string; icon?: string }[]
}>()
</script>

<template>
  <div class="relative pl-6 space-y-6">
    <!-- Vertical line -->
    <div class="absolute left-2 top-2 bottom-2 w-0.5 bg-slate-200"></div>
    
    <div v-for="(item, i) in items" :key="i" class="relative">
      <!-- Dot -->
      <div :class="[
        'absolute -left-6 w-4 h-4 rounded-full border-2 border-white',
        i === 0 ? 'bg-slate-900' : 'bg-slate-300'
      ]"></div>
      
      <!-- Content -->
      <div class="bg-white rounded-lg border border-slate-200 p-3">
        <div class="flex items-center gap-2 mb-1">
          <span v-if="item.icon" class="material-symbols-outlined text-sm text-slate-500">{{ item.icon }}</span>
          <span class="text-xs text-slate-400">{{ item.time }}</span>
        </div>
        <p class="font-medium text-slate-900">{{ item.title }}</p>
        <p v-if="item.description" class="text-sm text-slate-500 mt-1">{{ item.description }}</p>
      </div>
    </div>
  </div>
</template>
