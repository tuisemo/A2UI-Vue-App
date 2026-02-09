<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  items: { label: string; content: string }[]
  defaultOpen?: number
}>()

const openIndex = ref(props.defaultOpen ?? 0)
</script>

<template>
  <div class="divide-y divide-slate-200 border border-slate-200 rounded-xl overflow-hidden">
    <div v-for="(item, i) in items" :key="i">
      <button 
        @click="openIndex = openIndex === i ? -1 : i"
        class="w-full px-4 py-3 flex items-center justify-between bg-white hover:bg-slate-50 transition-colors"
      >
        <span class="font-medium text-slate-900">{{ item.label }}</span>
        <span :class="['material-symbols-outlined text-slate-400 transition-transform', openIndex === i ? 'rotate-180' : '']">
          expand_more
        </span>
      </button>
      <div v-show="openIndex === i" class="px-4 py-3 bg-slate-50 text-sm text-slate-600">
        {{ item.content }}
      </div>
    </div>
  </div>
</template>
