import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import type { A2UIComponent } from '@/types'
import { fixComponentData } from '@/composables/a2uiSchema'

// Supported component types (whitelist)
const SUPPORTED_COMPONENTS = new Set([
  'Text', 'Icon', 'Image', 'Button', 'Card', 'Column', 'Row', 'List',
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
interface UIState {
  // Rendered components (applied after beginRendering)
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
  
  // Batch processing queue
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

  // Process a single A2UI message (internal, called from batch processor)
  function processMessage(msgId: string, data: any) {
    const msg = messages.value.find(m => m.id === msgId)
    if (!msg?.uiState) return

    // Process surfaceUpdate - buffer components
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
    if (data.deleteSurface) {
      msg.uiState.components.clear()
      msg.uiState.pendingComponents.clear()
      msg.uiState.dataModel = {}
      msg.uiState.pendingDataModel = {}
      msg.uiState.rootId = null
      msg.uiState.renderVersion++
    }

    // Process beginRendering - apply buffered changes
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
  function handleA2UIMessage(msgId: string, data: any) {
    // Handle wrapped messages (e.g. error UI)
    if (data.a2ui && Array.isArray(data.a2ui)) {
      data.a2ui.forEach((item: any) => queueMessage(msgId, item))
    } else {
      queueMessage(msgId, data)
    }
  }

  // Send message and stream response
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

    try {
      await fetchEventSource('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput }),
        onmessage: (msg) => {
          if (msg.data === '[DONE]') {
            // Flush any remaining pending messages
            if (pendingMessages.length > 0) {
              processBatch()
            }
            return
          }
          try {
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
      error.value = e.message
    } finally {
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

  return {
    messages,
    error,
    sendMessage,
    clearChat,
    getComponent,
    getDataAtPath,
    getRenderVersion
  }
})
