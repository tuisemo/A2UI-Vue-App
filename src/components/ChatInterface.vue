<script setup lang="ts">
import { ref, nextTick, computed, watch, onMounted } from 'vue'
import { useA2UIStore } from '@/stores/a2ui'
import ComponentRenderer from './renderer/ComponentRenderer.vue'

const store = useA2UIStore()
const inputText = ref('')
const chatContainer = ref<HTMLElement>()
const isAutoScroll = ref(true)

// Check if any message is loading
const isLoading = computed(() => store.messages.some(m => m.uiState?.isLoading))

// Auto scroll to bottom when messages change
const scrollToBottom = (smooth = true) => {
  if (!chatContainer.value || !isAutoScroll.value) return
  nextTick(() => {
    chatContainer.value?.scrollTo({ 
      top: chatContainer.value.scrollHeight, 
      behavior: smooth ? 'smooth' : 'auto' 
    })
  })
}

// Watch for new messages and content updates
watch(
  () => store.messages.map(m => ({ 
    id: m.id, 
    rootId: m.uiState?.rootId,
    version: m.uiState?.renderVersion 
  })),
  () => scrollToBottom(),
  { deep: true }
)

// Detect manual scroll to disable auto-scroll temporarily
const handleScroll = () => {
  if (!chatContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatContainer.value
  // Re-enable auto-scroll when near bottom (within 100px)
  isAutoScroll.value = scrollHeight - scrollTop - clientHeight < 100
}

const handleSubmit = async () => {
  if (!inputText.value.trim() || isLoading.value) return
  const msg = inputText.value
  inputText.value = ''
  isAutoScroll.value = true
  await store.sendMessage(msg)
  scrollToBottom()
}

const scenarios = [
  { label: '🌤️ 天气查询', prompt: '查询北京今天的天气，包含温度、湿度、风速等信息' },
  { label: '📊 数据图表', prompt: '展示一个销售数据的柱状图，包含过去6个月的数据' },
  { label: '🍜 餐厅推荐', prompt: '推荐3家附近评分高的川菜餐厅，包含图片和评分' },
  { label: '📝 Markdown', prompt: '用Markdown格式介绍Vue 3的主要特性' },
  { label: '📱 产品卡片', prompt: '展示一款热门智能手机的产品卡片，包含图片、价格、规格' },
  { label: '📋 数据表格', prompt: '展示一个用户订单列表的表格，包含订单号、商品、金额、状态' }
]
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Scenarios -->
    <div class="px-2 py-3 border-b border-slate-100 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Try These</h3>
      <div class="flex flex-wrap gap-2">
        <button 
          v-for="s in scenarios" 
          :key="s.label"
          @click="inputText = s.prompt"
          class="px-3 py-1.5 text-sm bg-white border border-slate-200 rounded-full text-slate-600 hover:bg-slate-50 hover:text-slate-900 hover:-translate-y-0.5 transition-all shadow-sm"
        >
          {{ s.label }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div 
      ref="chatContainer" 
      @scroll="handleScroll"
      class="flex-1 overflow-y-auto px-4 py-6 space-y-6 scrollbar-thin"
    >
      <!-- Empty State -->
      <div v-if="!store.messages.length" class="flex flex-col items-center justify-center h-full text-center py-12">
        <div class="w-16 h-16 bg-white rounded-2xl shadow-lg flex items-center justify-center mb-6">
          <span class="material-symbols-outlined text-3xl text-slate-700">auto_awesome</span>
        </div>
        <h2 class="text-2xl font-bold text-slate-900 mb-2">What would you like to build?</h2>
        <p class="text-slate-500">Describe a UI and I'll generate it for you.</p>
      </div>

      <!-- Chat Messages -->
      <template v-for="msg in store.messages" :key="msg.id">
        <!-- User Message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="max-w-[85%] px-4 py-3 rounded-2xl bg-slate-900 text-white rounded-br-md shadow-md">
            {{ msg.content }}
          </div>
        </div>

        <!-- Assistant Message with UI -->
        <div v-else class="flex justify-start">
          <div class="w-full max-w-full">
            <!-- Loading State -->
            <div v-if="msg.uiState?.isLoading && !msg.uiState?.rootId" 
                 class="inline-flex items-center gap-2 px-4 py-3 rounded-2xl bg-white border border-slate-200 rounded-bl-md shadow-sm">
              <div class="flex gap-1">
                <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
              </div>
              <span class="text-sm text-slate-500">Generating UI...</span>
            </div>

            <!-- Rendered UI -->
            <div v-if="msg.uiState?.rootId" class="animate-fade-in">
              <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 md:p-6 overflow-hidden">
                <ComponentRenderer :id="msg.uiState.rootId" :msg-id="msg.id" />
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Error -->
      <div v-if="store.error" class="flex justify-center px-4">
        <div class="px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2 max-w-md">
          <span class="material-symbols-outlined text-lg">error</span>
          <span class="flex-1">{{ store.error }}</span>
        </div>
      </div>
      
      <!-- Bottom spacer for better scroll experience -->
      <div class="h-4"></div>
    </div>

    <!-- Scroll to bottom button -->
    <Transition name="fade">
      <button 
        v-if="!isAutoScroll && store.messages.length"
        @click="isAutoScroll = true; scrollToBottom()"
        class="absolute bottom-28 right-8 w-10 h-10 bg-white border border-slate-200 rounded-full shadow-lg flex items-center justify-center hover:bg-slate-50 transition-colors z-20"
      >
        <span class="material-symbols-outlined text-slate-600">keyboard_arrow_down</span>
      </button>
    </Transition>

    <!-- Input -->
    <div class="p-4 bg-white/80 backdrop-blur-sm border-t border-slate-100">
      <div class="bg-white rounded-2xl border border-slate-200 shadow-lg p-2">
        <div class="flex items-end gap-2 bg-slate-50 rounded-xl p-1">
          <textarea
            v-model="inputText"
            @keydown.enter.exact.prevent="handleSubmit"
            @keydown.enter.shift.exact="null"
            :disabled="isLoading"
            placeholder="Describe the UI you want..."
            rows="1"
            class="flex-1 px-4 py-3 bg-transparent border-none resize-none focus:outline-none text-slate-900 placeholder:text-slate-400 min-h-[48px] max-h-[120px]"
            style="field-sizing: content;"
          ></textarea>
          <button 
            @click="handleSubmit"
            :disabled="!inputText.trim() || isLoading"
            class="w-11 h-11 rounded-full bg-slate-900 text-white flex items-center justify-center disabled:bg-slate-200 disabled:text-slate-400 hover:bg-slate-800 transition-colors flex-shrink-0"
          >
            <span v-if="isLoading" class="material-symbols-outlined animate-spin">progress_activity</span>
            <span v-else class="material-symbols-outlined">arrow_upward</span>
          </button>
        </div>
        <div v-if="store.messages.length" class="flex justify-end pt-2 pr-2">
          <button @click="store.clearChat" class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors">
            <span class="material-symbols-outlined text-sm">refresh</span>
            Reset
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.scrollbar-thin::-webkit-scrollbar { width: 6px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.scrollbar-thin::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
