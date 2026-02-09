<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
    <!-- Header -->
    <header class="border-b border-slate-200 bg-white/80 backdrop-blur-lg sticky top-0 z-50">
      <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
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

    <!-- Main -->
    <main class="max-w-5xl mx-auto px-6 py-8 h-[calc(100vh-80px)]">
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
