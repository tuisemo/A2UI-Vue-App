<script setup lang="ts">
defineProps<{
  columns: { key: string; label: string; width?: string }[]
  data: Record<string, any>[]
  striped?: boolean
}>()
</script>

<template>
  <div class="w-full overflow-x-auto rounded-xl border border-slate-200">
    <table class="w-full text-left">
      <thead class="bg-slate-50 border-b border-slate-200">
        <tr>
          <th 
            v-for="col in columns" 
            :key="col.key"
            class="px-4 py-3 text-sm font-semibold text-slate-700"
            :style="{ width: col.width }"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="(row, index) in data" 
          :key="index"
          :class="[
            'border-b border-slate-100 last:border-0',
            striped && index % 2 === 1 ? 'bg-slate-50/50' : ''
          ]"
        >
          <td 
            v-for="col in columns" 
            :key="col.key"
            class="px-4 py-3 text-sm text-slate-600"
          >
            {{ row[col.key] }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
