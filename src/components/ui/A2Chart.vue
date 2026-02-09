<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  options: any
  height?: string
}>()

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value || !props.options) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  // Ensure options has required structure
  const safeOptions = {
    ...props.options,
    xAxis: props.options?.xAxis || {},
    yAxis: props.options?.yAxis || {},
    series: props.options?.series || []
  }
  
  chartInstance.setOption(safeOptions, true)
}

onMounted(() => {
  if (props.options) {
    initChart()
  }
})

watch(() => props.options, (newOptions) => {
  if (newOptions) {
    initChart()
  }
}, { deep: true })

onUnmounted(() => {
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <div 
    ref="chartRef" 
    class="w-full rounded-xl overflow-hidden"
    :style="{ height: height || '300px' }"
  ></div>
</template>
