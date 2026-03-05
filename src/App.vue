<script setup lang="ts">
/**
 * 应用根组件 (Root Component)
 * 负责整体页面的宏观布局 (如渐变背景色、顶部导航栏) 和主体内容区 ChatInterface 挂载。
 */
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
    <!-- Header 顶部导航栏 -->
    <header class="border-b border-slate-200 bg-white/80 backdrop-blur-lg sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-6 py-2.5 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center">
            <span class="material-symbols-outlined text-white">auto_awesome</span>
          </div>
          <div>
            <h1 class="text-lg font-bold text-slate-900">A2UI Studio</h1>
            <p class="text-xs text-slate-500">Generative UI Engine</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">v2.0</span>
          <span class="px-2.5 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded-full">Vue 3 + Tailwind</span>
        </div>
      </div>
    </header>

    <!-- Main 主体内容区域 - 容纳核心的对话页面 -->
    <main class="max-w-7xl mx-auto w-full h-[calc(100vh-60px)]">
      <ChatInterface />
    </main>
  </div>
</template>

<script lang="ts">
import ChatInterface from './components/ChatInterface.vue'

export default {
  components: { ChatInterface }
}
</script>
