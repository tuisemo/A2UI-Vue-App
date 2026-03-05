<script setup lang="ts">
import { ref, nextTick, computed, watch } from 'vue'
import { useA2UIStore } from '@/stores/a2ui'
import ComponentRenderer from './renderer/ComponentRenderer.vue'
import A2Markdown from './ui/A2Markdown.vue'

const store = useA2UIStore()
const inputText = ref('')
const chatContainer = ref<HTMLElement>()
const isAutoScroll = ref(true)

// Check if any message is loading
// 检查当前是否有对话正在请求中，用于禁用输入框或显示 Loading 动画
const isLoading = computed(() => store.messages.some(m => m.uiState?.isLoading))

// Auto scroll to bottom when messages change
// 自动滚动到页面底部以保持最新消息在视野内的方法
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
// 监听滚动事件：如果用户主动向上翻阅历史消息，则暂时停止新消息来时的自动滚动到底部功能
const handleScroll = () => {
  if (!chatContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatContainer.value
  // Re-enable auto-scroll when near bottom (within 100px)
  isAutoScroll.value = scrollHeight - scrollTop - clientHeight < 100
}

// 处理用户交互：提交输入并将内容交给 Pinia Store 的 sendMessage 动作
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
    <!-- Messages 聊天气泡和生成式视图的渲染列表区 -->
    <div 
      ref="chatContainer" 
      @scroll="handleScroll"
      class="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-4 scrollbar-thin"
    >
      <!-- Empty State -->
      <div v-if="!store.messages.length" class="flex flex-col items-center justify-center h-full text-center py-12 max-w-2xl mx-auto">
        <div class="w-16 h-16 bg-white rounded-2xl shadow-lg flex items-center justify-center mb-6">
          <span class="material-symbols-outlined text-3xl text-slate-700">auto_awesome</span>
        </div>
        <h2 class="text-2xl font-bold text-slate-900 mb-2">What would you like to build?</h2>
        <p class="text-slate-500 mb-10">Describe a UI and I'll generate it for you.</p>

        <!-- Scenarios -->
        <div class="w-full text-left">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4 text-center">Or Try These Examples</h3>
          <div class="flex flex-wrap justify-center gap-3">
            <button 
              v-for="s in scenarios" 
              :key="s.label"
              @click="inputText = s.prompt; handleSubmit()"
              class="px-4 py-2 text-sm bg-white border border-slate-200 rounded-full text-slate-600 hover:bg-slate-50 hover:text-slate-900 hover:-translate-y-1 hover:shadow-md transition-all shadow-sm"
            >
              {{ s.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <template v-for="msg in store.messages" :key="msg.id">
        <!-- User Message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="max-w-[85%] px-4 py-3 rounded-2xl bg-slate-900 text-white rounded-br-md shadow-md">
            {{ msg.content }}
          </div>
        </div>

        <!-- Assistant Message with UI or Text -->
        <div v-else class="flex justify-start">
          <div class="w-full max-w-full">
            <!-- Loading State -->
            <div v-if="msg.uiState?.isLoading && !msg.uiState?.rootId && !msg.content" 
                 class="inline-flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-white border border-slate-100 rounded-bl-md shadow-sm">
              <div class="flex items-center gap-1.5 opacity-70 pb-0.5">
                <span class="w-2 h-2 bg-slate-500 rounded-full animate-dot-pulse" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 bg-slate-500 rounded-full animate-dot-pulse" style="animation-delay: 200ms"></span>
                <span class="w-2 h-2 bg-slate-500 rounded-full animate-dot-pulse" style="animation-delay: 400ms"></span>
              </div>
            </div>

            <!-- Standard Text Response -->
            <div v-if="msg.content" class="bg-white rounded-2xl border border-slate-200 rounded-bl-md shadow-sm p-4 mb-3 max-w-[85%]">
               <A2Markdown :content="msg.content" class="prose-sm" />
            </div>

            <!-- Rendered UI -->
            <div v-if="msg.uiState?.rootId" class="animate-fade-in mt-2 w-full">
              <div class="bg-slate-50/30 rounded-2xl ring-1 ring-slate-200/60 shadow-sm p-4 md:p-5 overflow-hidden w-full">
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

    <!-- Input Area -->
    <div class="px-4 pb-4 pt-2 md:px-8 md:pb-6 md:pt-3 bg-slate-50/80 backdrop-blur-xl border-t border-slate-200/50 sticky bottom-0 z-10 w-full transition-all">
      <div class="max-w-5xl mx-auto flex flex-col gap-3">
        <!-- Input Wrapper -->
        <div class="flex items-end gap-3 bg-white rounded-3xl border border-slate-200 shadow-sm p-2 transition-all duration-300 focus-within:shadow-md focus-within:border-slate-300 focus-within:ring-4 focus-within:ring-slate-100/50">
          <textarea
            v-model="inputText"
            @keydown.enter.exact.prevent="handleSubmit"
            @keydown.enter.shift.exact="null"
            placeholder="Describe the UI you want..."
            rows="1"
            class="flex-1 px-5 py-3.5 bg-transparent border-none resize-none focus:outline-none text-slate-700 placeholder:text-slate-400 min-h-[52px] max-h-[160px] text-base leading-relaxed"
            style="field-sizing: content;"
          ></textarea>
          
          <!-- Actions Container -->
          <div class="flex items-center gap-2 pb-1 pr-1">
            <!-- Stop Button -->
            <button 
              v-if="isLoading"
              @click="store.stopGeneration"
              title="Stop generating"
              class="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center hover:bg-red-50 hover:text-red-500 transition-colors flex-shrink-0"
            >
              <span class="material-symbols-outlined fill-current">stop_circle</span>
            </button>
            
            <!-- Send Button -->
            <button 
              v-else
              @click="handleSubmit"
              :disabled="!inputText.trim()"
              class="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center disabled:bg-slate-100 disabled:text-slate-300 hover:bg-slate-800 transition-colors flex-shrink-0 shadow-sm disabled:shadow-none"
            >
              <span class="material-symbols-outlined text-xl">arrow_upward</span>
            </button>
          </div>
        </div>
        
        <!-- Reset Button -->
        <div v-if="store.messages.length" class="flex justify-center">
          <button @click="store.clearChat" class="text-xs font-medium text-slate-400 hover:text-slate-600 flex items-center gap-1.5 transition-colors px-3 py-1.5 rounded-full hover:bg-slate-200/50 active:bg-slate-200/80">
            <span class="material-symbols-outlined text-[14px]">refresh</span>
            Start a new conversation
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

@keyframes dotPulse {
  0% { transform: scale(0.8); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.8); opacity: 0.3; }
}

.animate-dot-pulse {
  animation: dotPulse 1.4s infinite ease-in-out;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
