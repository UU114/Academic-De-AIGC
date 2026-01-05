"""
AcademicGuard - Main FastAPI Application Entry Point
AcademicGuard - FastAPI 应用主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import get_settings
from src.db.database import init_db
from src.api.routes import documents, analyze, suggest, session, export, transition, structure, flow, paragraph, structure_guidance
from src.api.routes import auth, payment, task, feedback
from src.middleware.mode_checker import ModeCheckerMiddleware


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    应用生命周期管理
    """
    # Startup: Initialize database and load models
    # 启动: 初始化数据库和加载模型
    print(f"Starting {settings.app_name} v{settings.app_version}...")
    await init_db()
    print("Database initialized")

    yield

    # Shutdown: Cleanup resources
    # 关闭: 清理资源
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AIGC Detection & Human-AI Collaborative Humanization Engine",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS Middleware
# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mode Checker Middleware - adds system mode info to requests
# 模式检查中间件 - 将系统模式信息添加到请求
app.add_middleware(ModeCheckerMiddleware)

# Include API routers
# 包含API路由
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(suggest.router, prefix="/api/v1/suggest", tags=["Suggestions"])
app.include_router(session.router, prefix="/api/v1/session", tags=["Session"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(transition.router, prefix="/api/v1/transition", tags=["Transition"])
app.include_router(structure.router, prefix="/api/v1/structure", tags=["Structure"])
app.include_router(flow.router, prefix="/api/v1/flow", tags=["Flow"])
app.include_router(paragraph.router, prefix="/api/v1/paragraph", tags=["Paragraph Logic"])
app.include_router(structure_guidance.router, prefix="/api/v1/structure-guidance", tags=["Structure Guidance"])

# Dual-mode system routes (认证、支付、任务路由)
# Dual-mode system routes (Auth, Payment, Task)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["Payment"])
app.include_router(task.router, prefix="/api/v1/task", tags=["Task"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])


@app.get("/")
async def root():
    """
    Root endpoint - Health check
    根端点 - 健康检查
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "mode": settings.system_mode.value,
        "is_debug": settings.is_debug_mode()
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    健康检查端点
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
