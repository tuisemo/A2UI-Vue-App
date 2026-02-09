import { reactive } from 'vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { fixComponentData } from '@/composables/a2uiSchema'

// Core types for our native engine
export interface A2UIComponent {
  id: string
  type: string
  props: Record<string, any>
  children: string[] // Derived convenience property
}

export interface A2UIState {
  components: Map<string, A2UIComponent>
  rootId: string | null
  isLoading: boolean
  error: string | null
}

export class A2UIEngine {
  // Reactive state
  public state: A2UIState

  constructor() {
    this.state = reactive({
      components: new Map(),
      rootId: null,
      isLoading: false,
      error: null
    })
  }

  /**
   * Reset the engine state
   */
  reset() {
    this.state.components.clear()
    this.state.rootId = null
    this.state.error = null
    this.state.isLoading = false
  }

  /**
   * Get a component by ID
   */
  getComponent(id: string): A2UIComponent | undefined {
    return this.state.components.get(id)
  }

  /**
   * Helper to extract children IDs from component props
   */
  private extractChildren(props: any): string[] {
    const children: string[] = []
    
    // Explicit list (Column, Row, List)
    if (props.children?.explicitList) {
      children.push(...props.children.explicitList)
    }
    
    // Single child (Card, Button, Tabs content)
    if (typeof props.child === 'string') {
      children.push(props.child)
    }
    
    // Modal
    if (props.entryPointChild) children.push(props.entryPointChild)
    if (props.contentChild) children.push(props.contentChild)
    
    // Tabs
    if (Array.isArray(props.tabs)) {
      props.tabs.forEach((tab: any) => {
        if (tab.child) children.push(tab.child)
      })
    }

    return children
  }

  /**
   * Parse and register a component from raw JSON
   */
  registerComponent(rawComp: any) {
    if (!rawComp || !rawComp.id || !rawComp.component) return

    // Auto-fix format issues
    const fixed = fixComponentData(rawComp)
    if (!fixed) return

    const type = Object.keys(fixed.component)[0]
    const props = fixed.component[type]
    const children = this.extractChildren(props)

    // Update reactive map
    this.state.components.set(fixed.id, {
      id: fixed.id,
      type,
      props,
      children
    })
  }

  /**
   * Handle incoming A2UI message
   */
  handleMessage(data: any) {
    // 1. surfaceUpdate (Component definitions)
    if (data.surfaceUpdate) {
      const comps = data.surfaceUpdate.components || []
      comps.forEach((c: any) => this.registerComponent(c))
    }

    // 2. beginRendering (Set Root ID)
    if (data.beginRendering) {
      this.state.rootId = data.beginRendering.root
    }
  }

  /**
   * Stream a chat request
   */
  async streamChat(message: string, endpoint: string = '/api/chat') {
    this.reset()
    this.state.isLoading = true

    try {
      await fetchEventSource(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
        
        onmessage: (msg) => {
          if (msg.data === '[DONE]') return
          
          try {
            const data = JSON.parse(msg.data)
            this.handleMessage(data)
          } catch (e) {
            console.warn('Failed to parse SSE message:', e)
          }
        },
        
        onerror: (err) => {
          console.error('SSE Error:', err)
          this.state.error = err.message || 'Stream connection failed'
          throw err // Rethrow to stop retrying
        }
      })
    } catch (e: any) {
      this.state.error = e.message
    } finally {
      this.state.isLoading = false
    }
  }
}
