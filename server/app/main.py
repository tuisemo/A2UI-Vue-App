"""
A2UI Generative UI Server - FastAPI Application
A2UI 生成式 UI 服务端 - FastAPI 应用入口文件
"""
import sys
from pathlib import Path

# Add server directory to path for both direct run and module run
# 将 server 目录添加到系统路径，确保可以直接运行或作为模块导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 引入路由模块：聊天API (Chat) 和 A2A (Agent to Agent) 协议API
from app.routes.chat import router as chat_router
from app.routes.a2a import router as a2a_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理器 (Lifespan Manager)
    用于在应用启动和关闭时执行特定逻辑，例如日志打印、数据库连接等。
    """
    print("🚀 A2UI Server v2.0 starting...")
    print("🔗 A2A Protocol endpoints enabled")
    yield
    print("👋 A2UI Server shutting down...")

# 初始化 FastAPI 实例
app = FastAPI(
    title="A2UI Server",            # 接口文档标题
    description="Generative UI Engine API", # 接口文档描述
    version="2.0.0",                # 版本号
    lifespan=lifespan               # 绑定生命周期
)

# 配置 CORS (跨域资源共享) 拦截器
# 允许前端应用 (如运行在 localhost:5173 上的 Vue) 访问该服务端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 允许所有域名跨域访问 (生产环境建议收紧)
    allow_credentials=True,         # 允许携带 Cookie
    allow_methods=["*"],            # 允许所有的 HTTP 方法 (GET, POST, OPTIONS 等)
    allow_headers=["*"],            # 允许所有的 HTTP 请求头
)

# 注册 API 路由器
app.include_router(chat_router)
app.include_router(a2a_router)


if __name__ == "__main__":
    import uvicorn
    # 当直接运行 main.py 时，使用 uvicorn 启动 ASGI 服务器
    # host="0.0.0.0" 表示允许任意 IP 访问
    # reload=True 开启热更新，开发时修改代码会自动重启
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
