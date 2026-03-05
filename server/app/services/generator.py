"""
A2UI Generator Service - Production-grade LLM interaction and component generation
A2UI 核心生成服务 - 负责与大模型 (LLM) 进行异步通讯、解析组件 JSON、并实施流水线架构返回前端数据
"""

import json
import logging
import os
from typing import AsyncGenerator, Dict, Any

from dotenv import load_dotenv
from app.services.history_manager import conversation_manager
from app.utils.retry import retry_async, LLM_RETRYABLE_EXCEPTIONS, RetryError
from openai import AsyncOpenAI

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Streamlined prompt for better LLM compliance
SYSTEM_PROMPT = """
# Role: A2UI Protocol Architect
You are an expert AI interface generator specializing in the A2UI protocol. Your mission is to transform user intent into high-performance, aesthetically pleasing, server-driven UI streams.

# 1. CRITICAL PROTOCOL RULES (MUST FOLLOW)
- **Format**: Output STRICT JSON Lines (JSONL). One valid JSON object per line.
- **Syntax**: NO Markdown code fences (```json). NO wrapping arrays (`[...]`). NO explanatory text outside JSON.
- **Topological Sort**: Always define **Child** components BEFORE their **Parent** containers.
- **Data Typing**: All text strings must be wrapped: `{"literalString": "Value"}` or `{"path": "/data/ref"}`.
- **Nested Component Refs (CRITICAL)**: If you want to embed a component (like a Button) inside a `Table` row, you MUST first generate its definition (e.g. `{"id": "btn_1"...}`), and then in the Table's data row you MUST reference it using the `componentRef` wrapper: `{"id": "123", "act": {"componentRef": "btn_1"}}`.
- **IDs**: Use short, descriptive unique string IDs (e.g., `btn_sub`, `card_main`). The final root ID must be `"root"`.

# 2. STANDARD INTERACTION FLOW
For every response requiring UI, you MUST follow this exact 4-step sequence:
1.  **Define Skeleton**: Create a loading/skeleton UI structure.
2.  **Render Skeleton**: Emit `beginRendering` targeting the skeleton root.
3.  **Define Content**: Generate the actual UI components (leaves first -> nodes -> root).
4.  **Render Content**: Emit `beginRendering` targeting the final `"root"`.

# 3. COMPONENT LIBRARY (Schema & Usage)

## Layout & Containers
- **Grid**: `{"id":"g","component":{"Grid":{"children":{"explicitList":["id1","id2"]},"cols":3,"gap":6}}}`
- **Column**: `{"id":"c","component":{"Column":{"children":{"explicitList":["id1","id2"]},"alignment":"start"|"center","styles":{"gap":8}}}}`
- **Row**: `{"id":"r","component":{"Row":{"children":{"explicitList":["id1","id2"]},"distribution":"spaceBetween"|"start","styles":{"gap":4}}}}`
- **Card**: `{"id":"card","component":{"Card":{"child":"content_id","elevation":1}}}`
- **Divider**: `{"id":"div","component":{"Divider":{"variant":"fullWidth"}}}`

## Content & Display
- **Text**: `{"id":"t","component":{"Text":{"text":{"literalString":"..."},"usageHint":"h1"|"body"|"caption"|"code"}}}`
- **Icon**: `{"id":"i","component":{"Icon":{"name":{"literalString":"icon_name"}}}}`
- **Image**: `{"id":"img","component":{"Image":{"url":{"literalString":"https://placehold.co/600x400"}}}}` (Use placehold.co for image URLs, NEVER use example.com)
- **Avatar**: `{"id":"avt","component":{"Avatar":{"name":{"literalString":"John Doe"},"src":{"literalString":"..."},"size":"md"}}}`
- **Badge**: `{"id":"bdg","component":{"Badge":{"text":{"literalString":"New"},"variant":"success"|"warning"|"error"}}}`
- **Alert**: `{"id":"alt","component":{"Alert":{"title":{"literalString":"..."},"message":{"literalString":"..."},"variant":"info"|"warning"}}}`
- **TagList**: `{"id":"tags","component":{"TagList":{"tags":[{"label":{"literalString":"Vue"},"color":"green"}]}}}`
- **Quote**: `{"id":"qt","component":{"Quote":{"content":{"literalString":"..."},"author":{"literalString":"..."}}}}`
- **Figure**: `{"id":"fig","component":{"Figure":{"src":{"literalString":"..."},"caption":{"literalString":"..."}}}}`
- **Markdown**: `{"id":"md","component":{"Markdown":{"content":{"literalString":"**bold** and *italic*"}}}}`

## Data Visualization & Feedback
- **Stat**: `{"id":"st","component":{"Stat":{"label":{"literalString":"Views"},"value":{"literalString":"1.2k"},"trend":"up"}}}`
- **MetricCard**: `{"id":"mc","component":{"MetricCard":{"title":{"literalString":"Revenue"},"value":{"literalString":"$4k"},"icon":{"literalString":"payments"},"color":"success"}}}`
- **Table**: `{"id":"tbl","component":{"Table":{"columns":[{"key":"c1","label":"Col1"}],"data":[{"c1":"Val1"}]}}}`
- **Timeline**: `{"id":"tl","component":{"Timeline":{"items":[{"title":"...","time":"..."}]}}}`
- **Progress**: `{"id":"prg","component":{"Progress":{"value":75,"max":100,"color":"primary"}}}`
- **Rating**: `{"id":"rt","component":{"Rating":{"rating":4,"max":5}}}`
- **Steps**: `{"id":"stp","component":{"Steps":{"steps":[{"label":{"literalString":"Step 1"},"status":"completed"}]}}}`
- **Accordion**: `{"id":"acc","component":{"Accordion":{"items":[{"label":{"literalString":"Q1"},"content":{"literalString":"A1"}}]}}}`

## Input & Actions
- **Button**: `{"id":"btn","component":{"Button":{"label":{"literalString":"Action"},"actionId":"do_action","variant":"filled"|"outlined"}}}`
- **TextField**: `{"id":"inp","component":{"TextField":{"label":{"literalString":"Name"},"variable":"user_name"}}}`

# 4. ICON LIBRARY (Material Symbols Only)
Use ONLY these icons: `hourglass_empty` (loading), `check_circle`, `error`, `info`, `warning`, `star`, `favorite`, `shopping_cart`, `person`, `settings`, `home`, `search`, `menu`, `close`, `add`, `remove`, `edit`, `delete`, `refresh`, `trending_up`, `trending_down`, `payments`, `local_shipping`, `location_on`, `phone`, `schedule`, `wb_sunny`, `cloud`.

# 5. DESIGN & LAYOUT BEST PRACTICES (CRITICAL)
- **Hierarchy**: Use `h1` for titles, `caption` for metadata. Bold key numbers.
- **Grids over Columns**: **NEVER stack a complex dashboard in a single vertical Column!** You MUST use `Grid` (e.g. `cols: 3`) to perfectly align multiple `Card`, `MetricCard`, or `Chart` elements side by side.
- **Rows for inline groups**: If generating multiple `Badge`, `Avatar`, or `Button` items, always wrap them in a `Row` with `gap: 2` or `3` to place them horizontally. Do not let them stack vertically inside a standard Column.
- **Spacing**: Ensure generous padding. Cards should feel spaced out.
- **Feedback**: Use `Alert` components to show success/failure states clearly.
- **Skeleton**: The skeleton should visually approximate the final layout (e.g., if showing a list, show 3 skeleton rows).

# 6. OUTPUT PATTERN EXAMPLE

User: "Show my order status"

[Output Stream]:
{"id":"sk_i","component":{"Icon":{"name":{"literalString":"hourglass_empty"}}}}
{"id":"sk_t","component":{"Text":{"text":{"literalString":"Fetching order..."},"usageHint":"caption"}}}
{"id":"sk_root","component":{"Column":{"children":{"explicitList":["sk_i","sk_t"]},"alignment":"center"}}}
{"beginRendering":{"surfaceId":"main","root":"sk_root"}}
{"id":"ord_t","component":{"Text":{"text":{"literalString":"Order #12345"},"usageHint":"h1"}}}
{"id":"ord_s","component":{"Badge":{"text":{"literalString":"Shipped"},"variant":"success"}}}
{"id":"trk_b","component":{"Button":{"label":{"literalString":"Track"},"actionId":"trk_123","variant":"outlined"}}}
{"id":"ord_tbl","component":{"Table":{"columns":[{"key":"id","label":"ID"},{"key":"act","label":"Action"}],"data":[{"id":"123","act":{"componentRef":"trk_b"}}]}}}
{"id":"root","component":{"Column":{"children":{"explicitList":["ord_t","ord_s","ord_tbl"]},"styles":{"padding":16,"gap":12}}}}
{"beginRendering":{"surfaceId":"main","root":"root"}}
"""

# Supported component types for validation
SUPPORTED_COMPONENTS = {
    "Text",
    "Icon",
    "Image",
    "Button",
    "Card",
    "Column",
    "Row",
    "Grid",
    "List",
    "Badge",
    "Alert",
    "Avatar",
    "Chart",
    "Table",
    "Progress",
    "Rating",
    "Stat",
    "Steps",
    "Timeline",
    "Accordion",
    "Price",
    "TagList",
    "MetricCard",
    "Figure",
    "Quote",
    "Markdown",
    "Divider",
    "TextField",
    "CheckBox",
    "Slider",
    "Tabs",
    "Video",
    "Audio",
    "Conditional",
}


# --- Pipeline Node Definitions ---

class PipelineNode:
    """Base class for generator pipeline nodes
    生成器流水线节点的抽象基类，所有处理节点都必须继承此方法并实现异步 process。
    """
    async def process(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield "" # to satisfy type checker


class IntentRecognitionNode(PipelineNode):
    """Determines the intent of the user query
    意图识别节点：
    作为一个前置拦截器，向大语言模型询问一次当前用户的输入是否需要展现 UI 还是只需要回答文本。
    把识别到的 intent（'ui' 或 'chat'）存入上下文 context，指导下一个流水线节点的运作。
    """
    
    async def process(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        client = context["client"]
        model = context["model"]
        user_query = context["user_query"]
        user_action = context.get("user_action")
        
        # Skip intent check if it's a direct user UI action
        # 如果是用户在界面上点击了某个按钮触发的 Action 操作，不需要识别，一定是走 UI 逻辑
        if user_action:
            context["intent"] = "ui"
            return
            
        try:
            intent_prompt = f"""Analyze the following user query and decide if it strictly requires generating a UI (cards, charts, layouts, buttons, forms, weather widgets) or if it's a general question that can be answered with text chat (greetings, code explanation, general knowledge, etc.).

Query: {user_query}

Output valid JSON ONLY in this format: {{"intent": "ui"}} or {{"intent": "chat"}}"""
            
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "You are a routing AI."}, {"role": "user", "content": intent_prompt}],
                response_format={"type": "json_object"} if "gpt" in model else None,
                temperature=0.1
            )
            content = response.choices[0].message.content or ""
            if "chat" in content.lower():
                context["intent"] = "chat"
            else:
                context["intent"] = "ui"
        except Exception as e:
            logger.error(f"Intent recognition failed: {str(e)}")
            context["intent"] = "ui"
            
        logger.info(f"Recognized intent: {context['intent']}")
        # This node yields nothing, just mutates context
        return
        yield "" 

class StandardChatNode(PipelineNode):
    """Handles standard conversational text queries
    标准聊天回答节点：
    如果上面的 IntentRecognitionNode 确认为 'chat' 意图，该节点将启动大模型对话流。
    只负责吐出文本块 (`text_chunk`)，不会吐出复杂的组件数据。
    """
    async def process(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        # 首先检查上下文，只有意图是 chat 才会处理，否则直接跳过
        if context.get("intent") != "chat":
            return
            
        client = context["client"]
        model = context["model"]
        user_query = context["user_query"]
        conversation_messages = context["history"]
        conversation_id = context.get("conversation_id")
        conv_manager = context["conversation_manager"]
        
        messages = conversation_messages + [{"role": "user", "content": user_query}]
        
        async def make_chat_call():
            return await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
        
        retry_decorator = retry_async(max_attempts=3, base_delay=1.0, max_delay=10.0, retryable_exceptions=LLM_RETRYABLE_EXCEPTIONS)
        retryable_chat_call = retry_decorator(make_chat_call)
        
        stream = await retryable_chat_call()
        
        full_text: str = ""
        async for chunk in stream:
            chunk_content: str = chunk.choices[0].delta.content or ""
            if chunk_content:
                full_text += chunk_content
                yield f"data: {json.dumps({'text_chunk': chunk_content})}\n\n"
                
        if conversation_id:
            conv_manager.add_message(conversation_id, "user", user_query)
            conv_manager.add_message(conversation_id, "assistant", full_text)
            
        yield "data: [DONE]\n\n"


class GenerativeUINode(PipelineNode):
    """Generates the A2UI JSON streaming components
    流式生成 UI 视图的核心节点：
    结合系统复杂的组件提示词 (SYSTEM_PROMPT)，调用模型返回标准 JSONL 每行流式包。
    进行逐行解析与组件校验后下发到前端。
    """
    
    def __init__(self, service):
        # 引用回服务对象，方便调用公共方法 _validate_component 等
        self.service = service # Reference back to use validate/fix methods

    async def process(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        if context.get("intent") != "ui":
            return
            
        client = context["client"]
        model = context["model"]
        user_query = context["user_query"]
        user_action = context.get("user_action")
        conversation_messages = context["history"]
        conversation_id = context.get("conversation_id")
        conv_manager = context["conversation_manager"]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ] + conversation_messages
        
        if user_action:
            action_context = f"""
# User Action Triggered
Action Name: {user_action.get('name', 'unknown')}
Source Component: {user_action.get('sourceComponentId', 'unknown')}
Timestamp: {user_action.get('timestamp', '')}
Context Data: {json.dumps(user_action.get('context', {}), indent=2)}

Generate an appropriate UI response to this user action.
"""
            messages.append({"role": "user", "content": action_context})
        else:
            # 常规的用户文字提问
            messages.append({
                "role": "user",
                "content": f'# Current Request\n\nUser Input: "{user_query}"\n\nGenerate the A2UI JSONL stream now.',
            })

        async def make_llm_call():
            # 发起真正的流式大模型请求
            return await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
        
        # 包装带有指数退避重试 (Exponential Backoff) 的装饰器以应对大模型的偶然连接超时或 502 等常见网络问题
        retry_decorator = retry_async(max_attempts=3, base_delay=1.0, max_delay=10.0, retryable_exceptions=LLM_RETRYABLE_EXCEPTIONS)
        retryable_llm_call = retry_decorator(make_llm_call)
        
        try:
            stream = await retryable_llm_call()
        except RetryError as e:
            logger.error(f"All retry attempts failed: {e.last_error}")
            try:
                logger.warning("Attempting final fallback with minimal context")
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages[-1:],
                    stream=True,
                )
            except Exception as final_error:
                logger.error(f"Final fallback also failed: {final_error}")
                raise e

        buffer: str = ""
        sent_ids: set[str] = set()
        component_count: int = 0
        render_count: int = 0
        has_final_render: bool = False

        # 下面的循环是处理 LLM Chunk 的核心，本质是：按换行符 `\n` 切断流式文字块，合并出完整的一行 JSON，然后进行单独的组件推送
        async for chunk in stream:
            chunk_content: str = chunk.choices[0].delta.content or ""
            if not chunk_content:
                continue

            buffer += chunk_content

            # 如果缓冲区凑够了一整行
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                # 剥离模型可能生成的 ```json 等代码块前缀防止 JSON Loads 崩溃
                if line.startswith("```"):
                    continue
                line = line.replace("```json", "").replace("```", "").strip()
                if not line:
                    continue

                try:
                    # 尝试将截取到的一行严格转为 Python 字典并丢给后端做字段/支持度校验
                    parsed: Dict[str, Any] = json.loads(line)
                    validated = self.service._validate_message(parsed)

                    if not validated:
                        continue

                    # -------------- 前端通信指令分类判断 --------------
                    # A2UI 前端目前定义了 4 大基础指令类型 (通过 JSON 顶层 key 判断)
                    
                    if "beginRendering" in validated:
                        # 'beginRendering' 指令：通知前端把内存/队列中的已缓冲组件正式挂载 (渲染) 到 DOM 树中
                        yield f"data: {json.dumps(validated)}\n\n"
                        render_count += 1
                        root_id = validated["beginRendering"].get("root", "")
                        if root_id == "root":
                            has_final_render = True
                        continue

                    if "dataModelUpdate" in validated:
                        # 'dataModelUpdate' 数据更新指令：支持双向数据绑定的组件 (例如表单) 传回模型的数据状态重置
                        yield f"data: {json.dumps(validated)}\n\n"
                        continue

                    if "deleteSurface" in validated:
                        # 'deleteSurface' 指令：销毁目标树，通常用于报错或重新生成前清空页面结构
                        yield f"data: {json.dumps(validated)}\n\n"
                        continue

                    if "text_chunk" in validated:
                        # 'text_chunk' 指令 (自定义拓展)：与组件无关的纯文本回答推送
                        yield f"data: {json.dumps(validated)}\n\n"
                        continue

                    comp_id = validated.get("id")
                    if comp_id and comp_id not in sent_ids:
                        # 这时就是一个普通的渲染微件 (Widget / UI Component)，为了符合 A2UI 规范我们需要包一层 'surfaceUpdate'
                        msg = {
                            "surfaceUpdate": {
                                "surfaceId": "main",
                                "components": [validated],
                            }
                        }
                        yield f"data: {json.dumps(msg)}\n\n"
                        sent_ids.add(comp_id)
                        component_count += 1

                except json.JSONDecodeError:
                    continue

        if buffer.strip():
            line = buffer.strip().replace("```json", "").replace("```", "").strip()
            if line:
                try:
                    parsed: Dict[str, Any] = json.loads(line)
                    validated = self.service._validate_message(parsed)
                    if validated:
                        if "beginRendering" in validated:
                            yield f"data: {json.dumps(validated)}\n\n"
                            if validated["beginRendering"].get("root") == "root":
                                has_final_render = True
                        elif "id" in validated and validated["id"] not in sent_ids:
                            msg = {
                                "surfaceUpdate": {
                                    "surfaceId": "main",
                                    "components": [validated],
                                }
                            }
                            yield f"data: {json.dumps(msg)}\n\n"
                            component_count += 1
                except:
                    pass

        if not has_final_render and "root" in sent_ids:
            final_render = {"beginRendering": {"surfaceId": "main", "root": "root"}}
            yield f"data: {json.dumps(final_render)}\n\n"

        logger.info(f"Generation complete: {component_count} components, {render_count} renders")
        
        if conversation_id:
            conv_manager.add_message(conversation_id, "user", user_query)
            conv_manager.add_message(conversation_id, "assistant", f"Generated {component_count} UI components")
        
        yield "data: [DONE]\n\n"


class A2UIGeneratorService:
    """
    负责组装管理 API 参数以及组合流水线 (Pipeline) 的服务类
    """
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("API_BASE_URL"),
        )
        self.model = os.getenv("MODEL_NAME", "qwen-plus")
        self.conversation_manager = conversation_manager
        
        # Initialize pipeline nodes
        self.pipeline = [
            IntentRecognitionNode(),
            StandardChatNode(),
            GenerativeUINode(self)
        ]
        
        logger.info(f"Initialized A2UI Generator: model={self.model}")

    def _validate_component(self, comp: Dict[str, Any]) -> bool:
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

    def _fix_component(self, comp: Dict[str, Any]) -> Dict[str, Any] | None:
        """Fix common LLM format mistakes and validate
        修正大模型最常见的语法格式问题，并清洗数据结构。由于不同大模型对复杂 Prompt 理解有异，此层做兜底修复。
        """
        if not self._validate_component(comp):
            return None

        component = comp["component"]
        comp_type = next(iter(component.keys()))
        props = component[comp_type]

        if not isinstance(props, dict):
            return None

        # Check if component type is supported
        if comp_type not in SUPPORTED_COMPONENTS:
            logger.warning(
                f"Unsupported component type: {comp_type}, converting to Text"
            )
            comp["component"] = {
                "Text": {
                    "text": {"literalString": f"[{comp_type}]"},
                    "usageHint": "caption",
                }
            }
            return comp

        # Fix string values to literalString format
        def fix_string_prop(obj: Dict[str, Any], key: str):
            if key in obj and isinstance(obj[key], str):
                obj[key] = {"literalString": obj[key]}

        # Type-specific fixes
        if comp_type == "Icon":
            fix_string_prop(props, "name")
            if "materialIcon" in props:
                name = props.get("materialIcon", {}).get("name", "help")
                props["name"] = {"literalString": name}
                props.pop("materialIcon", None)

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
            fix_string_prop(props, "label")
            if "label" not in props and "child" not in props and "icon" not in props:
                return None

        return comp

    def _validate_message(self, parsed: Dict[str, Any]) -> Dict[str, Any] | None:
        """Validate and fix A2UI message
        严格校验一条完整的 JSON Line 结构。如果是 A2UI 组件片段则送去清洗 (_fix_component)；
        如果是合法的操作指令 (如 beginRendering 等) 则直接放行。
        """
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
        elif "text_chunk" in parsed:
            return parsed
        return None

    async def generate_stream(self, user_query: str, user_action: dict | None = None, conversation_id: str | None = None) -> AsyncGenerator[str, None]:
        """Stream A2UI components via pipeline processing
        暴露给外部 FastApi Router (/api/chat) 调用的核心生成接口。
        它在此处初始化包含当前状态的上下文变量 (context)，并依次推入已经注册的 pipeline 节点阵列运行。
        """
        conversation_messages = []
        if conversation_id:
            if not self.conversation_manager.get_conversation(conversation_id):
                self.conversation_manager.create_conversation(conversation_id)
            conversation_messages = self.conversation_manager.get_messages_for_llm(conversation_id)
            logger.info(f"Loaded {len(conversation_messages)} historical messages for {conversation_id}")

        context: Dict[str, Any] = {
            "client": self.client,
            "model": self.model,
            "user_query": user_query,
            "user_action": user_action,
            "conversation_id": conversation_id,
            "history": conversation_messages,
            "conversation_manager": self.conversation_manager,
            "intent": None
        }

        try:
            for node in self.pipeline:
                async for chunk in node.process(context):
                    yield chunk
                    
            # if we end up here and no node completed the response due to intent fallthrus
            if context.get("intent") is None:
               yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Generation error: {e}")
            error_ui = self._get_error_ui(str(e))
            yield f"data: {json.dumps(error_ui)}\n\n"
            yield "data: [DONE]\n\n"

    def _get_error_ui(self, error: str) -> dict:
        """
        当后端服务崩溃报错时调用。
        它会强制构造一个标准的 A2UI Alert 报警提示组件结构发送给前端，保证前端渲染出错原因供用户查看，而不是白屏死锁。
        """
        return {
            "a2ui": [
                {
                    "surfaceUpdate": {
                        "surfaceId": "main",
                        "components": [
                            {
                                "id": "alert",
                                "component": {
                                    "Alert": {
                                        "title": {"literalString": "Error"},
                                        "message": {"literalString": error[:200]},
                                        "variant": "error",
                                    }
                                },
                            },
                            {
                                "id": "root",
                                "component": {
                                    "Column": {"children": {"explicitList": ["alert"]}}
                                },
                            },
                        ],
                    }
                },
                {"beginRendering": {"surfaceId": "main", "root": "root"}},
            ]
        }


# Singleton instance
generator_service = A2UIGeneratorService()
