// A2UI Component Types
export interface A2UIComponent {
  id: string
  type: string
  props: Record<string, any>
  children: string[]
}

export interface A2UIState {
  components: Map<string, A2UIComponent>
  rootId: string | null
  isLoading: boolean
  error: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// Supported Component Types (30+ components)
export type ComponentType = 
  // Layout
  | 'Column' | 'Row' | 'Card' | 'List'
  // Text & Content
  | 'Text' | 'Icon' | 'Image' | 'Divider' | 'Markdown' | 'Quote' | 'Figure'
  // Interactive
  | 'Button' | 'TextField' | 'CheckBox' | 'Slider' | 'Tabs'
  // Media
  | 'Video' | 'Audio'
  // Data Display
  | 'Chart' | 'Table' | 'Progress' | 'Rating' | 'Stat' | 'MetricCard'
  // Feedback & Status
  | 'Badge' | 'Avatar' | 'Alert' | 'TagList'
  // Process & Timeline
  | 'Steps' | 'Timeline' | 'Accordion'
  // E-commerce
  | 'Price'
