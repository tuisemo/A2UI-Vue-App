<script setup lang="ts">
import ComponentRenderer from '../renderer/ComponentRenderer.vue'

const props = defineProps<{
  children?: any
  msgId?: string
  cols?: number
  gap?: number
}>()

const emits = defineEmits<{
  (e: 'action', payload: any): void
}>()

const getGridColsClass = (cols?: number) => {
  switch (cols) {
    case 1: return 'grid-cols-1'
    case 2: return 'grid-cols-1 sm:grid-cols-2'
    case 3: return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
    case 4: return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
    case 5: return 'grid-cols-1 sm:grid-cols-3 lg:grid-cols-5'
    case 6: return 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6'
    default: return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' // Default to 3 columns for dashboards
  }
}

const getGapClass = (gap?: number) => {
  switch (gap) {
    case 0: return 'gap-0'
    case 2: return 'gap-2'
    case 3: return 'gap-3'
    case 4: return 'gap-4'
    case 6: return 'gap-6'
    case 8: return 'gap-8'
    default: return 'gap-4'
  }
}
</script>

<template>
  <div :class="[
    'grid w-full',
    getGridColsClass(cols),
    getGapClass(gap)
  ]">
    <template v-if="children?.explicitList">
      <ComponentRenderer
        v-for="childId in children.explicitList"
        :key="childId"
        :id="childId"
        :msg-id="msgId"
        @action="$emit('action', $event)"
      />
    </template>
  </div>
</template>
