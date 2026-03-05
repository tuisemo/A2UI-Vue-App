from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

# ==========================================
# 接口请求和对话层面的数据结构
# ==========================================

class ChatRequest(BaseModel):
    """
    接受来自于前端的 /api/chat 对话请求体
    """
    message: str                                  # 用户发送的文本内容
    userAction: Optional[Dict[str, Any]] = None   # 用户在 UI 中的交互事件 (例如点击特定按钮携带的上下文)
    conversation_id: Optional[str] = None         # 会话 ID（用于实现多轮对话历史管理）


class ConversationMessage(BaseModel):
    """Represents a single message in conversation history
    用于在内存或数据库中表示历史记录中的单条消息
    """
    role: str  # "user" or "assistant"            # 角色枚举，用户或大模型
    content: str                                  # 消息内容
    timestamp: str                                # 消息生成的时间戳
    components: Optional[List[Dict[str, Any]]] = None # (可选) 记录这条消息中大模型生成了哪些 UI 组件
    user_action: Optional[Dict[str, Any]] = None  # (可选) 如果是因为事件操作产生的消息，存放事件荷载


class ConversationHistory(BaseModel):
    """Container for conversation history
    表示一场完整会话的载体类
    """
    conversation_id: str                          # 唯一会话识别码
    messages: List[ConversationMessage]           # 此会话包含的所有历史交流数组
    created_at: str                               # 创建时间
    updated_at: str                               # 最新回答时间
    metadata: Dict[str, Any] = {}                 # 扩展字段，用于存储特殊会话配置等


# ==========================================
# A2UI 前端组件协议的数据结构
# ==========================================

class A2UIComponent(BaseModel):
    """
    一个标准 A2UI 组件的渲染单元
    """
    id: str           # 组件的唯一标识 (大模型实时生成)
    component: dict   # 组件真实的 JSON 参数属性字典 (包含类型、样式、具体数据等)


class SurfaceUpdate(BaseModel):
    """
    视图更新指令包装，用来承装新增的 A2UI 组件块
    """
    surfaceId: str                 # 目标渲染面板 (默认通常是 "main")
    components: List[A2UIComponent]# 本次网络包带回的新增组件列表


class BeginRendering(BaseModel):
    """
    开始渲染指令，指示客户端将已下发的组件链条在某个入口实际渲染出来
    """
    surfaceId: str # 面板名
    root: str      # 指向根组件 id (例如 "root"，或用于骨架屏的 "sk_root")


class A2UIMessage(BaseModel):
    """
    完整的 A2UI 数据指令封装，每次 Stream 流返回一行都是可选的下列指令之一
    """
    surfaceUpdate: Optional[SurfaceUpdate] = None     # 组件节点更新指令
    beginRendering: Optional[BeginRendering] = None   # 拼装渲染执行指令
    # 其他指令如: dataModelUpdate (数据更新), text_chunk (标准文字输出) 也可以在这扩展
