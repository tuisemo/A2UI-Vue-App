"""
Conversation History Manager - In-memory storage for conversation context
对话历史管理器 - 基于内存存储的会话上下文管理机制 (用于维护多轮对话的联系)
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.models.schemas import ConversationMessage, ConversationHistory

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation history for multiple users/sessions
    为多用户或多窗口管理会话记录。
    注意：当前是基于内存实现的字典，服务重启会丢失记录。如需持久化可替换为 Redis 或数据库。
    """
    
    def __init__(self, max_history_per_conversation: int = 20):
        # 内部存储：Key 为 conversation_id，Value 为相关的对话模型
        self._conversations: Dict[str, ConversationHistory] = {}
        # 最大存储消息条数，防止上下文过长导致 LLM 超过 Token 限制
        self.max_history = max_history_per_conversation
        logger.info(f"Initialized ConversationManager (max_history={max_history_per_conversation})")
    
    def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Create a new conversation session
        新建一场对话上下文。如果没传 ID 则随机生成一个 UUID。
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        now = datetime.utcnow().isoformat() + "Z"
        self._conversations[conversation_id] = ConversationHistory(
            conversation_id=conversation_id,
            messages=[],
            created_at=now,
            updated_at=now,
            metadata={}
        )
        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve conversation history by ID
        通过 ID 获取会话的所有历史数据
        """
        return self._conversations.get(conversation_id)
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        components: Optional[List[Dict]] = None,
        user_action: Optional[Dict] = None
    ) -> bool:
        """Add a message to conversation history
        将一条消息 (可能是用户的提问、用户的按钮操作，或者是机器人的回答) 添加到历史中。
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat() + "Z",
            components=components,
            user_action=user_action
        )
        
        conv.messages.append(message)
        
        # Trim old messages if exceeds max
        # 如果历史消息超过设定的 max_history，则截断历史 (抛弃最旧的记录)
        if len(conv.messages) > self.max_history:
            conv.messages = conv.messages[-self.max_history:]
        
        conv.updated_at = datetime.utcnow().isoformat() + "Z"
        logger.debug(f"Added {role} message to {conversation_id}, total messages: {len(conv.messages)}")
        return True
    
    def get_messages_for_llm(self, conversation_id: str) -> List[Dict[str, str]]:
        """Format conversation history for LLM API consumption
        将历史类对象格式化为大模型 OpenAI 接口认识的标准 [{'role': 'xx', 'content': 'xx'}, ...] 格式
        """
        conv = self._conversations.get(conversation_id)
        if not conv:
            return []
        
        messages = []
        for msg in conv.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    def list_conversations(self) -> List[str]:
        """List all active conversation IDs"""
        return list(self._conversations.keys())
    
    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        return {
            "total_conversations": len(self._conversations),
            "total_messages": sum(len(c.messages) for c in self._conversations.values()),
            "max_history_per_conversation": self.max_history
        }


# Singleton instance
conversation_manager = ConversationManager(max_history_per_conversation=20)
