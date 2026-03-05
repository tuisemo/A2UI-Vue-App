import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import type { A2UIComponent } from '@/types'
import { fixComponentData } from '@/composables/a2uiSchema'

// Supported component types (whitelist)
// 组件白名单验证，防止后端返回不支持的异常组件导致前端崩溃
const SUPPORTED_COMPONENTS = new Set([
  'Text', 'Icon', 'Image', 'Button', 'Card', 'Column', 'Row', 'Grid', 'List',
  'Badge', 'Alert', 'Avatar', 'Chart', 'Table', 'Progress', 'Rating',
  'Stat', 'Steps', 'Timeline', 'Accordion', 'Price', 'TagList',
  'MetricCard', 'Figure', 'Quote', 'Markdown', 'Divider', 'TextField',
  'CheckBox', 'Slider', 'Tabs', 'Video', 'Audio', 'Conditional'
])

// Data model entry (A2UI spec compliant)
interface DataModelEntry {
  key: string
  valueString?: string
  valueNumber?: number
  valueBoolean?: boolean
  valueMap?: DataModelEntry[]
}

// UI State with buffering support
// 组件与数据双缓冲状态池，用于解决流式渲染中的闪烁和不连续问题
interface UIState {
  // Rendered components (applied after beginRendering)
  // 已经正式挂载到视图树上的组件集合
  components: Map<string, A2UIComponent>
  // Buffer for pending components
  pendingComponents: Map<string, A2UIComponent>
  // Rendered data model
  dataModel: Record<string, any>
  // Buffer for pending data updates
  pendingDataModel: Record<string, any>
  // Current root
  rootId: string | null
  // Render version for animation control
  renderVersion: number
  // Loading state
  isLoading: boolean
}

// Extended message type
// 对话单项实体，每一个对话不仅带有纯文本，还带有自己独立的 UIState 用于承载微件 UI 环境
interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  uiState?: UIState
}

export const useA2UIStore = defineStore('a2ui', () => {
  const messages = ref<ChatMessage[]>([])
  const error = ref<string | null>(null)

  // Track globally which components triggered an action and are awaiting response
  const pendingActionIds = ref<Set<string>>(new Set())

  // Controller for aborting ongoing SSE streams
  let abortController: AbortController | null = null

  // Batch processing queue
  // 用于帧限流 (requestAnimationFrame) 的消息缓冲队列，防止高频 SSE 推送卡死主线程
  let pendingMessages: { msgId: string; data: any }[] = []
  let rafId: number | null = null
  let lastRenderTime = 0
  const MIN_RENDER_INTERVAL = 16 // ~60fps

  // Extract children IDs from component props
  function extractChildren(props: any): string[] {
    const children: string[] = []
    if (props.children?.explicitList) children.push(...props.children.explicitList)
    if (typeof props.child === 'string') children.push(props.child)
    if (props.thenChild) children.push(props.thenChild)
    if (props.elseChild) children.push(props.elseChild)
    if (props.entryPointChild) children.push(props.entryPointChild)
    if (props.contentChild) children.push(props.contentChild)
    if (Array.isArray(props.tabs)) {
      props.tabs.forEach((tab: any) => { if (tab.child) children.push(tab.child) })
    }
    return children
  }

  // Validate and fix component, return null if invalid
  // 校验并修复来自 LLM 的组件数据，剥离核心属性及拍扁 children
  function validateComponent(rawComp: any): { id: string; type: string; props: any; children: string[] } | null {
    if (!rawComp?.id || !rawComp?.component) return null

    const fixed = fixComponentData(rawComp)
    if (!fixed) return null

    const type = Object.keys(fixed.component)[0]
    const props = fixed.component[type]

    // Whitelist check - fallback to Text for unknown types
    if (!SUPPORTED_COMPONENTS.has(type)) {
      console.warn(`[A2UI] Unknown component "${type}", fallback to Text`)
      return {
        id: fixed.id,
        type: 'Text',
        props: { text: { literalString: `[${type}]` }, usageHint: 'caption' },
        children: []
      }
    }

    return {
      id: fixed.id,
      type,
      props,
      children: extractChildren(props)
    }
  }

  // Parse dataModelUpdate contents to plain object
  function parseDataModelContents(contents: DataModelEntry[]): Record<string, any> {
    const result: Record<string, any> = {}
    for (const entry of contents) {
      if (entry.valueString !== undefined) {
        result[entry.key] = entry.valueString
      } else if (entry.valueNumber !== undefined) {
        result[entry.key] = entry.valueNumber
      } else if (entry.valueBoolean !== undefined) {
        result[entry.key] = entry.valueBoolean
      } else if (entry.valueMap !== undefined) {
        result[entry.key] = parseDataModelContents(entry.valueMap)
      }
    }
    return result
  }

  // Deep merge objects
  function deepMerge(target: Record<string, any>, source: Record<string, any>): Record<string, any> {
    const result = { ...target }
    for (const key of Object.keys(source)) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(result[key] || {}, source[key])
      } else {
        result[key] = source[key]
      }
    }
    return result
  }

  // Set value at path in object
  function setAtPath(obj: Record<string, any>, path: string, value: any) {
    const parts = path.split('/').filter(p => p)
    let current = obj
    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current)) current[parts[i]] = {}
      current = current[parts[i]]
    }
    if (parts.length > 0) {
      Object.assign(current, value)
    } else {
      Object.assign(obj, value)
    }
  }

  // Get value at path from object
  function getAtPath(obj: Record<string, any>, path: string): any {
    const parts = path.split('/').filter(p => p)
    let current = obj
    for (const part of parts) {
      if (current == null || typeof current !== 'object') return undefined
      current = current[part]
    }
    return current
  }

  // Set value at path in object (for data binding) - internal helper
  function setDataAtPathInternal(obj: Record<string, any>, path: string, value: any): Record<string, any> {
    const parts = path.split('/').filter(p => p)
    if (parts.length === 0) return obj

    // Create a deep clone to ensure reactivity
    const result = JSON.parse(JSON.stringify(obj))
    let current = result
    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current) || typeof current[parts[i]] !== 'object') {
        current[parts[i]] = {}
      }
      current = current[parts[i]]
    }

    const lastPart = parts[parts.length - 1]
    current[lastPart] = value
    return result
  }

  // Process a single A2UI message (internal, called from batch processor)
  // 此方法由 `processBatch` (一帧) 定时调度调用，根据返回的单条不同指令进入对应的行为逻辑。
  function processMessage(msgId: string, data: any) {
    const msg = messages.value.find(m => m.id === msgId)
    if (!msg) return

    // Process text_chunk
    if (data.text_chunk) {
      msg.content += data.text_chunk
      if (msg.uiState) msg.uiState.renderVersion++ // For reactivity if needed
      return // text chunks are not part of UI state components
    }

    if (!msg.uiState) return

    // Process surfaceUpdate - buffer components
    // 👉 UI 组件更新分支：A2UI 的机制是将组件发送前端后首先放入内存 buffer (未激活状态待挂载)，
    // 等待所有的依赖结构接收完毕之后，才会收到 `beginRendering` 才会一齐渲染。
    if (data.surfaceUpdate) {
      const components = data.surfaceUpdate.components || []
      for (const comp of components) {
        const validated = validateComponent(comp)
        if (validated) {
          msg.uiState.pendingComponents.set(validated.id, validated)
        }
      }
    }

    // Process dataModelUpdate - buffer data
    // 👉 数据模型更新分支：把 LLM 预设定的表单内容写入内存。同样也是写入 pendingDataModel 缓冲区待触发。
    if (data.dataModelUpdate) {
      const { path, contents } = data.dataModelUpdate
      if (Array.isArray(contents)) {
        const parsed = parseDataModelContents(contents)
        if (path) {
          setAtPath(msg.uiState.pendingDataModel, path, parsed)
        } else {
          msg.uiState.pendingDataModel = deepMerge(msg.uiState.pendingDataModel, parsed)
        }
      }
    }

    // Process deleteSurface - clear everything
    // 👉 重置/清空页面。例如服务奔溃重试时会由后端发起，避免页面重叠和卡死
    if (data.deleteSurface) {
      msg.uiState.components.clear()
      msg.uiState.pendingComponents.clear()
      msg.uiState.dataModel = {}
      msg.uiState.pendingDataModel = {}
      msg.uiState.rootId = null
      msg.uiState.renderVersion++
    }

    // Process beginRendering - apply buffered changes
    // 👉 激活指令：将刚才积攒在 pendingComponents 和 pendingDataModel 双缓冲里面的组件全部移入正式视图层。
    // 这项技术解决了 “流式吐出组件带来的骨架剧烈跳跃晃动” （因为父节点可能早早下发但子节点还没生成好）。
    if (data.beginRendering) {
      const newRootId = data.beginRendering.root

      // Apply pending components to rendered components
      msg.uiState.pendingComponents.forEach((comp, id) => {
        msg.uiState!.components.set(id, comp)
      })
      msg.uiState.pendingComponents.clear()

      // Apply pending data model
      msg.uiState.dataModel = deepMerge(msg.uiState.dataModel, msg.uiState.pendingDataModel)
      msg.uiState.pendingDataModel = {}

      // Switch root
      const previousRoot = msg.uiState.rootId
      msg.uiState.rootId = newRootId
      msg.uiState.renderVersion++

      if (previousRoot !== newRootId) {
        console.log(`[A2UI] Render #${msg.uiState.renderVersion}: ${previousRoot || 'null'} → ${newRootId} (${msg.uiState.components.size} components)`)
      }
    }
  }

  // Batch process queued messages with RAF throttling
  // 利用 RequestAnimationFrame 实现的一批渲染队列处理，通过限频(16ms/60fps)保障动画流畅
  function processBatch() {
    const now = performance.now()
    if (now - lastRenderTime < MIN_RENDER_INTERVAL && pendingMessages.length < 50) {
      // Throttle: wait for next frame
      rafId = requestAnimationFrame(processBatch)
      return
    }

    // Process all pending messages
    const batch = pendingMessages
    pendingMessages = []
    rafId = null
    lastRenderTime = now

    for (const { msgId, data } of batch) {
      processMessage(msgId, data)
    }
  }

  // Queue message for batch processing
  function queueMessage(msgId: string, data: any) {
    pendingMessages.push({ msgId, data })

    // Schedule batch processing
    if (!rafId) {
      rafId = requestAnimationFrame(processBatch)
    }
  }

  // Handle incoming A2UI message
  // 判断外层是否被包装在 [ {"a2ui":...} ] 中
  function handleA2UIMessage(msgId: string, data: any) {
    // Handle wrapped messages (e.g. error UI)
    if (data.a2ui && Array.isArray(data.a2ui)) {
      data.a2ui.forEach((item: any) => queueMessage(msgId, item))
    } else {
      queueMessage(msgId, data)
    }
  }

  // Send message and stream response
  // 发送用户提问，并将新生成的对话窗注入页面，并发起针对 /api/chat 的 SSE 监听。
  async function sendMessage(userInput: string) {
    if (!userInput.trim()) return

    // Check if already loading
    const hasLoading = messages.value.some(m => m.uiState?.isLoading)
    if (hasLoading) return

    error.value = null

    // Add user message
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: userInput,
      timestamp: new Date()
    })

    // Add assistant message with fresh UI state
    const assistantMsgId = crypto.randomUUID()
    messages.value.push({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      uiState: {
        components: new Map(),
        pendingComponents: new Map(),
        dataModel: {},
        pendingDataModel: {},
        rootId: null,
        renderVersion: 0,
        isLoading: true
      }
    })

    // Prepare abort controller
    if (abortController) {
      abortController.abort('New request started')
    }
    abortController = new AbortController()

    try {
      // 必须使用 fetchEventSource (@microsoft) 而不是原生 EventSource 这个坑在于原生并不支持携带 POST Request 的 body。
      await fetchEventSource('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput }),
        signal: abortController.signal,
        onmessage: (msg) => {
          // 在收到 SSE 数据帧时的流式调度函数
          if (msg.data === '[DONE]') {
            // Flush any remaining pending messages
            // 流式回答结束指令：如果限流帧 (RAF) 还没有将池子排空，强制排空绘制出完整的画面。
            if (pendingMessages.length > 0) {
              processBatch()
            }
            return
          }
          try {
            // 推入限流帧池排队
            const raw = JSON.parse(msg.data)
            handleA2UIMessage(assistantMsgId, raw)
          } catch (e) {
            console.warn('[A2UI] Parse error:', e)
          }
        },
        onerror: (err) => {
          error.value = err.message || 'Connection failed'
          throw err
        }
      })
    } catch (e: any) {
      if (e.name === 'AbortError' || e === 'AbortError') {
        console.log('[A2UI] Stream aborted by user.')
      } else {
        error.value = e.message
      }
    } finally {
      abortController = null
      // Mark this message as done loading
      const msg = messages.value.find(m => m.id === assistantMsgId)
      if (msg?.uiState) {
        msg.uiState.isLoading = false
      }
    }
  }

  // Clear all
  function clearChat() {
    messages.value = []
    error.value = null
    pendingMessages = []
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
  }

  // Get component by ID
  function getComponent(msgId: string, compId: string): A2UIComponent | undefined {
    const msg = messages.value.find(m => m.id === msgId)
    return msg?.uiState?.components.get(compId)
  }

  // Get data at path
  function getDataAtPath(msgId: string, path: string): any {
    const msg = messages.value.find(m => m.id === msgId)
    if (!msg?.uiState?.dataModel) return undefined
    return getAtPath(msg.uiState.dataModel, path)
  }

  // Get render version for animation keys
  function getRenderVersion(msgId: string): number {
    const msg = messages.value.find(m => m.id === msgId)
    return msg?.uiState?.renderVersion || 0
  }

  // Set data at path (for two-way data binding)
  function setDataAtPath(msgId: string, path: string, value: any) {
    const msg = messages.value.find(m => m.id === msgId)
    if (!msg?.uiState) return

    // Update data model with new value
    msg.uiState.dataModel = setDataAtPathInternal(msg.uiState.dataModel, path, value)
    console.log(`[A2UI] Data binding: ${path} =`, value)
  }

  // Send user action to backend
  // 从生成的微件组件触发用户交互行为 (例如点击按钮、提交表单)，将其发送给 LLM 后端生成后续 UI
  async function sendUserAction(action: { name: string; sourceId?: string; context?: any }) {
    const lastAssistantMsg = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (!lastAssistantMsg) return

    // Track local component loading state
    if (action.sourceId) {
      pendingActionIds.value.add(action.sourceId)
    }

    // Build userAction message
    const userAction = {
      userAction: {
        name: action.name,
        surfaceId: 'main',
        sourceComponentId: action.sourceId || 'unknown',
        timestamp: new Date().toISOString(),
        context: {
          ...action.context,
          // Include current data model state
          dataModel: lastAssistantMsg.uiState?.dataModel
        }
      }
    }

    console.log('[A2UI] Sending user action:', userAction)

    // Create a new assistant message for the response
    const responseMsgId = crypto.randomUUID()
    messages.value.push({
      id: responseMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      uiState: {
        components: new Map(),
        pendingComponents: new Map(),
        dataModel: { ...lastAssistantMsg.uiState?.dataModel },
        pendingDataModel: {},
        rootId: null,
        renderVersion: 0,
        isLoading: true
      }
    })

    // Prepare abort controller
    if (abortController) {
      abortController.abort('New request started')
    }
    abortController = new AbortController()

    try {
      await fetchEventSource('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: action.name,
          userAction: userAction.userAction
        }),
        signal: abortController.signal,
        onmessage: (msg) => {
          if (msg.data === '[DONE]') {
            if (pendingMessages.length > 0) {
              processBatch()
            }
            return
          }
          try {
            const raw = JSON.parse(msg.data)
            handleA2UIMessage(responseMsgId, raw)
          } catch (e) {
            console.warn('[A2UI] Parse error:', e)
          }
        },
        onerror: (err) => {
          console.error('[A2UI] Action error:', err)
          throw err
        }
      })
    } catch (e: any) {
      if (e.name === 'AbortError' || e === 'AbortError') {
        console.log('[A2UI] User Action stream aborted by user.')
      } else {
        error.value = e.message
      }
    } finally {
      abortController = null
      if (action.sourceId) {
        pendingActionIds.value.delete(action.sourceId)
      }

      const msg = messages.value.find(m => m.id === responseMsgId)
      if (msg?.uiState) {
        msg.uiState.isLoading = false
      }
    }
  }

  // Stop current generation stream
  function stopGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  return {
    messages,
    error,
    pendingActionIds,
    sendMessage,
    sendUserAction,
    stopGeneration,
    clearChat,
    getComponent,
    getDataAtPath,
    setDataAtPath,
    getRenderVersion
  }
})
