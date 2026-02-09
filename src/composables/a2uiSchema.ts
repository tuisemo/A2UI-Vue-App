/**
 * A2UI Component Schema Validation using Zod
 * Inspired by Vercel AI SDK streamObject pattern
 */
import { z } from 'zod'

// Literal value types used in A2UI
const LiteralString = z.object({
    literalString: z.string()
}).strict()

// Reserved for future use
// const LiteralNumber = z.object({ literalNumber: z.number() }).strict()
// const LiteralBoolean = z.object({ literalBoolean: z.boolean() }).strict()

// Children reference
const ChildrenRef = z.object({
    explicitList: z.array(z.string())
}).strict()

// Component type schemas
const TextComponent = z.object({
    Text: z.object({
        text: LiteralString,
        usageHint: z.enum(['h1', 'h2', 'h3', 'h4', 'h5', 'body', 'caption']).optional()
    }).passthrough()
})

const IconComponent = z.object({
    Icon: z.object({
        name: LiteralString
    }).passthrough()
})

const ImageComponent = z.object({
    Image: z.object({
        url: LiteralString,
        fit: z.enum(['contain', 'cover', 'fill']).optional()
    }).passthrough()
})

const DividerComponent = z.object({
    Divider: z.object({}).passthrough()
})

const ColumnComponent = z.object({
    Column: z.object({
        children: ChildrenRef.optional(),
        alignment: z.enum(['start', 'center', 'end', 'stretch']).optional(),
        distribution: z.enum(['start', 'center', 'end', 'spaceBetween', 'spaceAround']).optional()
    }).passthrough()
})

const RowComponent = z.object({
    Row: z.object({
        children: ChildrenRef.optional(),
        alignment: z.enum(['start', 'center', 'end', 'stretch']).optional(),
        distribution: z.enum(['start', 'center', 'end', 'spaceBetween', 'spaceAround']).optional()
    }).passthrough()
})

const CardComponent = z.object({
    Card: z.object({
        child: z.string().optional()
    }).passthrough()
})

const ListComponent = z.object({
    List: z.object({
        children: ChildrenRef.optional(),
        direction: z.enum(['vertical', 'horizontal']).optional()
    }).passthrough()
})

const ButtonComponent = z.object({
    Button: z.object({
        child: z.string().optional(),
        action: z.object({ name: z.string() }).optional(),
        primary: z.boolean().optional()
    }).passthrough()
})

// Union of all component types
const ComponentType = z.union([
    TextComponent,
    IconComponent,
    ImageComponent,
    DividerComponent,
    ColumnComponent,
    RowComponent,
    CardComponent,
    ListComponent,
    ButtonComponent,
    // Fallback for unknown component types
    z.record(z.string(), z.any())
])

// Single component instance
export const ComponentInstance = z.object({
    id: z.string(),
    component: ComponentType
}).passthrough()

// Surface update message
export const SurfaceUpdate = z.object({
    surfaceId: z.string(),
    components: z.array(ComponentInstance)
})

// Begin rendering message
export const BeginRendering = z.object({
    surfaceId: z.string(),
    root: z.string()
})

// Server to client message
export const ServerToClientMessage = z.object({
    surfaceUpdate: SurfaceUpdate.optional(),
    beginRendering: BeginRendering.optional(),
    dataModelUpdate: z.any().optional(),
    deleteSurface: z.any().optional()
}).refine(
    (msg) => msg.surfaceUpdate || msg.beginRendering || msg.dataModelUpdate || msg.deleteSurface,
    { message: "Message must contain at least one valid field" }
)

// A2UI response wrapper
export const A2UIResponse = z.object({
    a2ui: z.array(ServerToClientMessage)
})

// Type exports
export type ComponentInstanceType = z.infer<typeof ComponentInstance>
export type SurfaceUpdateType = z.infer<typeof SurfaceUpdate>
export type ServerToClientMessageType = z.infer<typeof ServerToClientMessage>

/**
 * Fix common LLM mistakes in component data
 */
export function fixComponentData(comp: any): any {
    if (!comp?.component) return comp
    
    const component = comp.component
    const type = Object.keys(component)[0]
    const props = component[type]
    
    if (!props) return comp

    // Fix Icon: various wrong formats -> {name: {literalString: "..."}}
    if (type === 'Icon') {
        let iconName = 'help'
        if (props.icon?.materialIcon?.name) {
            iconName = props.icon.materialIcon.name
        } else if (props.materialIcon?.name) {
            iconName = props.materialIcon.name
        } else if (typeof props.name === 'string') {
            iconName = props.name
        } else if (props.name?.literalString) {
            return comp // Already correct
        }
        comp.component.Icon = { name: { literalString: iconName } }
    }

    // Fix Text: {text: "..."} -> {text: {literalString: "..."}}
    if (type === 'Text') {
        if (typeof props.text === 'string') {
            props.text = { literalString: props.text }
        }
        if (!props.usageHint) {
            props.usageHint = 'body'
        }
    }

    // Fix Image: {url: "..."} -> {url: {literalString: "..."}}
    if (type === 'Image') {
        if (typeof props.url === 'string') {
            props.url = { literalString: props.url }
        }
        if (!props.fit) {
            props.fit = 'cover'
        }
    }

    return comp
}

/**
 * Validate and fix component array
 */
export function validateComponents(components: any[]): ComponentInstanceType[] {
    const validated: ComponentInstanceType[] = []
    
    for (const comp of components) {
        try {
            // First fix common issues
            const fixed = fixComponentData(comp)
            
            // Then validate
            const result = ComponentInstance.safeParse(fixed)
            if (result.success) {
                validated.push(result.data)
            } else {
                console.warn('Component validation failed:', result.error.message, comp)
                // Still include it but with minimal fix
                if (fixed?.id && fixed?.component) {
                    validated.push(fixed as ComponentInstanceType)
                }
            }
        } catch (e) {
            console.warn('Component processing error:', e)
        }
    }
    
    return validated
}

/**
 * Parse and validate A2UI message
 */
export function parseA2UIMessage(data: any): ServerToClientMessageType | null {
    try {
        // Handle wrapped format
        if (data.a2ui && Array.isArray(data.a2ui)) {
            // Return first valid message
            for (const msg of data.a2ui) {
                const parsed = parseA2UIMessage(msg)
                if (parsed) return parsed
            }
            return null
        }

        // Direct message format
        if (data.surfaceUpdate) {
            // Fix components before validation
            if (data.surfaceUpdate.components) {
                data.surfaceUpdate.components = data.surfaceUpdate.components.map(fixComponentData)
            }
        }

        const result = ServerToClientMessage.safeParse(data)
        if (result.success) {
            return result.data
        }
        
        console.warn('Message validation failed:', result.error.message)
        return null
    } catch (e) {
        console.warn('Message parsing error:', e)
        return null
    }
}
