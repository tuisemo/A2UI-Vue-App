"""
A2UI Generator Service - Production-grade LLM interaction and component generation
"""
import json
import logging
import os
from typing import AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Streamlined prompt for better LLM compliance
SYSTEM_PROMPT = """# A2UI Protocol v2

## RULES (MUST FOLLOW)
1. Output ONE JSON object per line (JSONL format)
2. NO markdown code fences, NO arrays wrapping
3. Define children components BEFORE parents
4. ALWAYS start with skeleton → beginRendering → content → beginRendering
5. Final root component id MUST be "root"

## MESSAGE TYPES
Component:  {"id":"x","component":{"Type":{...props...}}}
Render:     {"beginRendering":{"surfaceId":"main","root":"component-id"}}
Data:       {"dataModelUpdate":{"surfaceId":"main","contents":[{"key":"k","valueString":"v"}]}}

## COMPONENTS
Layout: Column, Row, Card, List
Content: Text, Icon, Image, Markdown, Divider, Quote, Figure
Data: Chart, Table, Progress, Rating, Stat, MetricCard, Badge, TagList
Input: Button, TextField, CheckBox, Slider, Tabs
Process: Steps, Timeline, Accordion
Other: Price, Avatar, Alert

## FORMAT EXAMPLES
Text: {"id":"t","component":{"Text":{"text":{"literalString":"Hello"},"usageHint":"h1"}}}
Column: {"id":"c","component":{"Column":{"children":{"explicitList":["a","b"]},"alignment":"center"}}}
Row: {"id":"r","component":{"Row":{"children":{"explicitList":["a","b"]},"distribution":"spaceBetween"}}}
Card: {"id":"card","component":{"Card":{"child":"content-id"}}}
Icon: {"id":"i","component":{"Icon":{"name":{"literalString":"star"}}}}
Image: {"id":"img","component":{"Image":{"url":{"literalString":"https://images.unsplash.com/photo-xxx?w=800"}}}}
Badge: {"id":"b","component":{"Badge":{"text":{"literalString":"New"},"variant":"success"}}}
Alert: {"id":"a","component":{"Alert":{"title":{"literalString":"Title"},"message":{"literalString":"Msg"},"variant":"info"}}}

## DATA BINDING
Static value: {"text":{"literalString":"Hello"}}
Dynamic path: {"text":{"path":"/user/name"}}

## STANDARD FLOW (Always follow this pattern)
{"id":"sk-icon","component":{"Icon":{"name":{"literalString":"hourglass_empty"}}}}
{"id":"sk-text","component":{"Text":{"text":{"literalString":"加载中..."},"usageHint":"caption"}}}
{"id":"sk","component":{"Column":{"children":{"explicitList":["sk-icon","sk-text"]},"alignment":"center"}}}
{"beginRendering":{"surfaceId":"main","root":"sk"}}
... define your content components here (children before parents) ...
{"id":"root","component":{"Column":{"children":{"explicitList":["your-content-ids"]}}}}
{"beginRendering":{"surfaceId":"main","root":"root"}}

## ICONS (Material Symbols)
hourglass_empty, check_circle, error, info, warning, star, favorite, shopping_cart, person, settings, home, search, menu, close, add, remove, edit, delete, refresh, trending_up, trending_down, payments, local_shipping, location_on, phone, schedule, wb_sunny, cloud, restaurant

Now create UI. Start with skeleton, then content. Output JSONL only.
"""

# Supported component types for validation
SUPPORTED_COMPONENTS = {
    'Text', 'Icon', 'Image', 'Button', 'Card', 'Column', 'Row', 'List',
    'Badge', 'Alert', 'Avatar', 'Chart', 'Table', 'Progress', 'Rating',
    'Stat', 'Steps', 'Timeline', 'Accordion', 'Price', 'TagList',
    'MetricCard', 'Figure', 'Quote', 'Markdown', 'Divider', 'TextField',
    'CheckBox', 'Slider', 'Tabs', 'Video', 'Audio', 'Conditional'
}


class A2UIGeneratorService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("API_BASE_URL"),
        )
        self.model = os.getenv("MODEL_NAME", "qwen-plus")
        logger.info(f"Initialized A2UI Generator: model={self.model}")

    def _validate_component(self, comp: dict) -> bool:
        """Validate component structure"""
        if not isinstance(comp, dict):
            return False
        if "id" not in comp or "component" not in comp:
            return False
        if not isinstance(comp["component"], dict):
            return False
        if len(comp["component"]) == 0:
            return False
        return True

    def _fix_component(self, comp: dict) -> dict | None:
        """Fix common LLM format mistakes and validate"""
        if not self._validate_component(comp):
            return None

        component = comp["component"]
        comp_type = next(iter(component.keys()))
        props = component[comp_type]

        if not isinstance(props, dict):
            return None

        # Check if component type is supported
        if comp_type not in SUPPORTED_COMPONENTS:
            logger.warning(f"Unsupported component type: {comp_type}, converting to Text")
            comp["component"] = {
                "Text": {"text": {"literalString": f"[{comp_type}]"}, "usageHint": "caption"}
            }
            return comp

        # Fix string values to literalString format
        def fix_string_prop(obj: dict, key: str):
            if key in obj and isinstance(obj[key], str):
                obj[key] = {"literalString": obj[key]}

        # Type-specific fixes
        if comp_type == "Icon":
            fix_string_prop(props, "name")
            if "materialIcon" in props:
                name = props.get("materialIcon", {}).get("name", "help")
                props["name"] = {"literalString": name}
                del props["materialIcon"]

        elif comp_type == "Text":
            fix_string_prop(props, "text")

        elif comp_type == "Image":
            fix_string_prop(props, "url")

        elif comp_type == "Badge":
            fix_string_prop(props, "text")

        elif comp_type == "Alert":
            fix_string_prop(props, "title")
            fix_string_prop(props, "message")

        elif comp_type == "Markdown":
            fix_string_prop(props, "content")

        elif comp_type == "Quote":
            fix_string_prop(props, "content")
            fix_string_prop(props, "author")

        elif comp_type == "Stat":
            fix_string_prop(props, "label")

        elif comp_type == "MetricCard":
            fix_string_prop(props, "title")

        elif comp_type == "Figure":
            fix_string_prop(props, "src")
            fix_string_prop(props, "caption")

        elif comp_type == "TextField":
            fix_string_prop(props, "label")
            fix_string_prop(props, "placeholder")

        elif comp_type == "CheckBox":
            fix_string_prop(props, "label")

        elif comp_type == "Slider":
            fix_string_prop(props, "label")

        elif comp_type == "Avatar":
            fix_string_prop(props, "src")
            fix_string_prop(props, "name")

        elif comp_type == "Button":
            if "child" not in props:
                return None

        return comp

    def _validate_message(self, parsed: dict) -> dict | None:
        """Validate and fix A2UI message"""
        if "id" in parsed and "component" in parsed:
            return self._fix_component(parsed)
        elif "beginRendering" in parsed:
            br = parsed["beginRendering"]
            if isinstance(br, dict) and "surfaceId" in br and "root" in br:
                return parsed
        elif "dataModelUpdate" in parsed:
            dm = parsed["dataModelUpdate"]
            if isinstance(dm, dict) and "surfaceId" in dm and "contents" in dm:
                return parsed
        elif "deleteSurface" in parsed:
            ds = parsed["deleteSurface"]
            if isinstance(ds, dict) and "surfaceId" in ds:
                return parsed
        return None

    async def generate_stream(self, user_query: str) -> AsyncGenerator[str, None]:
        """Stream A2UI components with validation"""
        try:
            # Try standard call first
            try:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Create UI for: {user_query}"}
                    ],
                    stream=True,
                    temperature=0.7
                )
            except Exception as e:
                logger.warning(f"Standard call failed: {e}, retrying with minimal params")
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": f"{SYSTEM_PROMPT}\n\nCreate UI for: {user_query}"}
                    ],
                    stream=True
                )

            buffer = ""
            sent_ids = set()
            component_count = 0
            render_count = 0
            has_final_render = False

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if not content:
                    continue

                buffer += content

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    # Clean markdown artifacts
                    if line.startswith("```"):
                        continue
                    line = line.replace("```json", "").replace("```", "").strip()
                    if not line:
                        continue

                    try:
                        parsed = json.loads(line)
                        validated = self._validate_message(parsed)
                        
                        if not validated:
                            logger.debug(f"Invalid message skipped: {line[:100]}")
                            continue

                        # Handle beginRendering
                        if "beginRendering" in validated:
                            yield f"data: {json.dumps(validated)}\n\n"
                            render_count += 1
                            root_id = validated["beginRendering"].get("root", "")
                            if root_id == "root":
                                has_final_render = True
                            logger.info(f"Render #{render_count}: root={root_id}")
                            continue

                        # Handle dataModelUpdate
                        if "dataModelUpdate" in validated:
                            yield f"data: {json.dumps(validated)}\n\n"
                            logger.debug("Data model update sent")
                            continue

                        # Handle deleteSurface
                        if "deleteSurface" in validated:
                            yield f"data: {json.dumps(validated)}\n\n"
                            continue

                        # Handle component
                        comp_id = validated.get("id")
                        if comp_id and comp_id not in sent_ids:
                            msg = {"surfaceUpdate": {"surfaceId": "main", "components": [validated]}}
                            yield f"data: {json.dumps(msg)}\n\n"
                            sent_ids.add(comp_id)
                            component_count += 1

                    except json.JSONDecodeError:
                        continue

            # Process remaining buffer
            if buffer.strip():
                line = buffer.strip().replace("```json", "").replace("```", "").strip()
                if line:
                    try:
                        parsed = json.loads(line)
                        validated = self._validate_message(parsed)
                        if validated:
                            if "beginRendering" in validated:
                                yield f"data: {json.dumps(validated)}\n\n"
                                if validated["beginRendering"].get("root") == "root":
                                    has_final_render = True
                            elif "id" in validated and validated["id"] not in sent_ids:
                                msg = {"surfaceUpdate": {"surfaceId": "main", "components": [validated]}}
                                yield f"data: {json.dumps(msg)}\n\n"
                                component_count += 1
                    except:
                        pass

            # Fallback: ensure final render
            if not has_final_render and "root" in sent_ids:
                final_render = {"beginRendering": {"surfaceId": "main", "root": "root"}}
                yield f"data: {json.dumps(final_render)}\n\n"
                logger.info("Fallback: sent final beginRendering")

            logger.info(f"Generation complete: {component_count} components, {render_count} renders")
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Generation error: {e}")
            error_ui = self._get_error_ui(str(e))
            yield f"data: {json.dumps(error_ui)}\n\n"
            yield "data: [DONE]\n\n"

    def _get_error_ui(self, error: str) -> dict:
        return {
            "a2ui": [
                {"surfaceUpdate": {"surfaceId": "main", "components": [
                    {"id": "alert", "component": {"Alert": {
                        "title": {"literalString": "Error"},
                        "message": {"literalString": error[:200]},
                        "variant": "error"
                    }}},
                    {"id": "root", "component": {"Column": {"children": {"explicitList": ["alert"]}}}}
                ]}},
                {"beginRendering": {"surfaceId": "main", "root": "root"}}
            ]
        }


# Singleton instance
generator_service = A2UIGeneratorService()
