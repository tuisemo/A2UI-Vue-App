<script setup lang="ts">
defineProps<{
  steps: { label: string; description?: string; status: 'completed' | 'current' | 'pending' }[]
  direction?: 'horizontal' | 'vertical'
}>()
</script>

<template>
  <div :class="['flex', direction === 'vertical' ? 'flex-col gap-4' : 'flex-row items-start gap-2']">
    <div 
      v-for="(step, i) in steps" 
      :key="i"
      :class="['flex items-center', direction === 'vertical' ? 'gap-3' : 'flex-col gap-2 flex-1']"
    >
      <!-- Step indicator -->
      <div class="flex items-center">
        <div :class="[
          'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold',
          step.status === 'completed' ? 'bg-emerald-500 text-white' :
          step.status === 'current' ? 'bg-slate-900 text-white' :
          'bg-slate-200 text-slate-500'
        ]">
          <span v-if="step.status === 'completed'" class="material-symbols-outlined text-sm">check</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <!-- Connector line -->
        <div 
          v-if="i < steps.length - 1 && direction !== 'vertical'"
          :class="['h-0.5 flex-1 min-w-8', step.status === 'completed' ? 'bg-emerald-500' : 'bg-slate-200']"
        ></div>
      </div>
      <!-- Step content -->
      <div :class="direction === 'vertical' ? '' : 'text-center'">
        <p :class="['text-sm font-medium', step.status === 'pending' ? 'text-slate-400' : 'text-slate-900']">{{ step.label }}</p>
        <p v-if="step.description" class="text-xs text-slate-500 mt-0.5">{{ step.description }}</p>
      </div>
    </div>
  </div>
</template>
