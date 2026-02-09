import { ref } from 'vue'
import { A2UIEngine, type A2UIState } from '../core/A2UIEngine'

export interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    // Engine state snapshot for this message
    uiState?: A2UIState
    timestamp: Date
}

// Global engine instance (singleton for this demo, but could be per-chat)
const engine = new A2UIEngine()

export function useA2UI() {
    const messages = ref<ChatMessage[]>([])
    
    // Proxy engine state
    const uiState = engine.state

    const sendMessage = async (userInput: string) => {
        if (!userInput.trim() || uiState.isLoading) return

        // 1. Add User Message
        messages.value.push({
            id: crypto.randomUUID(),
            role: 'user',
            content: userInput,
            timestamp: new Date()
        })

        // 2. Add Assistant Message (Placeholder)
        // Note: For now, we only support ONE active UI at a time in the main view.
        // In a real chat, we'd snapshot the UI state per message or use multiple engines.
        const assistantMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: '',
            uiState: uiState, // Link to reactive engine state
            timestamp: new Date()
        }
        messages.value.push(assistantMsg)

        // 3. Start Streaming
        await engine.streamChat(userInput)
    }

    const clearChat = () => {
        messages.value = []
        engine.reset()
    }

    return {
        messages,
        uiState,
        engine, // Export engine for renderer
        sendMessage,
        clearChat
    }
}
