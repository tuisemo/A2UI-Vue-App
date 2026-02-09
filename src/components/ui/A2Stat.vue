<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}>()

const trendColors = {
  up: 'text-emerald-500',
  down: 'text-red-500',
  neutral: 'text-slate-400'
}
const trendIcons = {
  up: 'trending_up',
  down: 'trending_down',
  neutral: 'trending_flat'
}
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-sm text-slate-500 mb-1">{{ label }}</p>
        <p class="text-2xl font-bold text-slate-900">{{ value }}</p>
        <div v-if="trend" class="flex items-center gap-1 mt-2">
          <span :class="['material-symbols-outlined text-sm', trendColors[trend]]">{{ trendIcons[trend] }}</span>
          <span :class="['text-xs font-medium', trendColors[trend]]">{{ trendValue }}</span>
        </div>
      </div>
      <div v-if="icon" class="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
        <span class="material-symbols-outlined text-slate-600">{{ icon }}</span>
      </div>
    </div>
  </div>
</template>
