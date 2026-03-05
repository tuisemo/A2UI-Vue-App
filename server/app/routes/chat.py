from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services.generator import generator_service

# 初始化路由，所有的接口都会自动加上 /api 前缀，并且在 Swagger 文档中归类到 "chat" 下
router = APIRouter(prefix="/api", tags=["chat"])

@router.get("/health")
async def health_check():
    """
    健康检查接口
    用于测试服务是否正常运行、负载均衡检测等。
    """
    return {"status": "healthy", "service": "a2ui-server", "version": "2.0.0"}

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    核心对话流式接口 (Server-Sent Events)
    接收前端发送的文本或交互事件，将其传送给 LLM 生成器，并通过 SSE 流式返回长链接的文本或 UI 组件。
    """
    # 检查消息内容是否为空
    if not request.message.strip():
        # Handle userAction without message (action-only requests)
        # 如果既没有文本消息，也没有携带前台的按钮/表单交互事件(userAction)，则拦截抛错
        if not request.userAction:
            raise HTTPException(status_code=400, detail="Message or userAction required")
        # 如果是单纯的事件触发（比如点击了一个无字按钮），我们构造一个系统文本作为请求记录上下文
        request.message = f"[Action: {request.userAction.get('name', 'unknown')}]"
    
    # 返回流式响应 StreamingResponse
    # media_type="text/event-stream" 标志着这是一个 SSE (Server-Sent Events) 接口，允许服务器主动向客户端推送数据流
    return StreamingResponse(
        # 调用大模型服务，获得异步生成器 (AsyncGenerator)
        generator_service.generate_stream(
            request.message, 
            request.userAction,
            request.conversation_id
        ),
        media_type="text/event-stream",
        # 设置防缓冲的响应头，确保数据块一产生就立刻推送到前端，避免 Nginx 或浏览器等待完整的包
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
