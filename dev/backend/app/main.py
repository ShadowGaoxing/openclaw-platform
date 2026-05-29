"""FastAPI 主入口 — 启动 NATS/Redis/Scheduler/DB"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.redis_client import init_redis, close_redis
from app.core.nats_client import init_nats, close_nats
from app.core.scheduler import scheduler, setup_scheduler
from app.api import auth, tasks, agents, models as models_api, departments, shared, admin, files

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期：启动初始化各组件，关闭时清理"""
    # 1. DB 初始化（自动建表）
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Redis 初始化（容错）
    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis init failed (degraded mode): {e}")

    # 3. NATS 初始化（容错）
    try:
        await init_nats()
    except Exception as e:
        logger.warning(f"NATS init failed (degraded mode): {e}")

    # 4. 后台调度器启动
    setup_scheduler()
    scheduler.start()
    logger.info(f"Background scheduler started with {len(scheduler.get_jobs())} jobs")

    yield

    # 关闭流程
    logger.info("Shutting down...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await close_nats()
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    description="跨部门 OpenCLAW 协作系统 API V2.2",
)

# CORS — 从 settings 读取，开发环境默认 ["*"]，生产环境通过 CORS_ORIGINS 环境变量配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(models_api.router)
app.include_router(departments.router)
app.include_router(shared.router)
app.include_router(admin.router)
app.include_router(files.router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "service": settings.app_name,
        "scheduler_running": scheduler.running,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR",
            "request_id": request.headers.get("X-Request-Id", ""),
        },
    )
