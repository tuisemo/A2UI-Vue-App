
"""
A2A Protocol Routes - Agent-to-Agent Communication Endpoints
"""
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.schemas import ChatRequest
from app.services.generator import generator_service
from app.services.history_manager import conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["a2a"])


class A2AMessage(BaseModel):
    """A2A protocol message structure"""
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict | None = None


class A2AResponse(BaseModel):
    """A2A protocol response structure"""
    jsonrpc: str = "2.0"
    id: str | int | None = None
    result: dict | None = None
    error: dict | None = None


class AgentCard(BaseModel):
    """A2A Agent Card - describes agent capabilities"""
    name: str
    description: str
    url: str
    version: str
    capabilities: dict = {
        "streaming": True,
        "components": True,
        "history": True,
    }
    default_modes: list[str] = ["chat", "ui-generation"]


@router.get("/.well-known/agent-card")
async def get_agent_card() -> AgentCard:
    return AgentCard(
        name="A2UI Generator Agent",
        description="Server-driven UI generation agent using A2UI protocol",
        url="http://localhost:8000",
        version="2.0.0",
        capabilities={
            "streaming": True,
            "components": True,
            "history": True,
            "tool_calling": True,
        },
        default_modes=["chat", "ui-generation"],
    )


@router.post("/api/a2a/message")
async def handle_a2a_message(message: A2AMessage) -> A2AResponse:
    try:
        if message.method == "agent.getCapabilities":
            return A2AResponse(
                id=message.id,
                result={"streaming": True, "components": True, "history": True}
            )
        elif message.method == "chat.send":
            if not message.params or "message" not in message.params:
                raise HTTPException(status_code=400, detail="Message required")
            return A2AResponse(
                id=message.id,
                error={"code": -32000, "message": "Use chat.stream method"}
            )
        elif message.method == "chat.stream":
            return A2AResponse(
                id=message.id,
                error={"code": -32000, "message": "Use /api/a2a/stream"}
            )
        else:
            return A2AResponse(
                id=message.id,
                error={"code": -32601, "message": f"Method not found: {message.method}"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A2A message error: {e}")
        return A2AResponse(
            id=message.id,
            error={"code": -32000, "message": str(e)}
        )


@router.post("/api/a2a/stream")
async def handle_a2a_stream(message: A2AMessage) -> StreamingResponse:
    if not message.params or "message" not in message.params:
        raise HTTPException(status_code=400, detail="Message required")
    
    chat_request = ChatRequest(message=message.params["message"])
    return StreamingResponse(
        generator_service.generate_stream(chat_request.message, chat_request.userAction),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/api/a2a/task")


@router.get("/api/a2a/conversations")
async def list_conversations():
    """List all active conversations"""
    convs = conversation_manager.list_conversations()
    stats = conversation_manager.get_stats()
    return {"conversations": convs, "stats": stats}


@router.get("/api/a2a/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get specific conversation history"""
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("/api/a2a/conversation")
async def create_conversation():
    """Create a new conversation session"""
    conv_id = conversation_manager.create_conversation()
    return {"conversation_id": conv_id, "status": "created"}


@router.delete("/api/a2a/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    success = conversation_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


async def create_a2a_task(message: A2AMessage) -> A2AResponse:
    if not message.params:
        raise HTTPException(status_code=400, detail="Task params required")
    
    task_id = f"task_{message.id}" if message.id else "task_1"
    return A2AResponse(
        id=message.id,
        result={"taskId": task_id, "status": "created"}
    )
