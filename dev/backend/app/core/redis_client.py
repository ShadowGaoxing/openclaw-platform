"""Redis 客户端 — 单例，用于分布式锁 + 心跳 + Token Bucket"""
from typing import Optional
import redis.asyncio as redis_async
from app.core.config import get_settings

_redis_client: Optional[redis_async.Redis] = None


async def init_redis() -> redis_async.Redis:
    global _redis_client
    settings = get_settings()
    _redis_client = redis_async.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    # 测试连接
    await _redis_client.ping()
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def get_redis() -> redis_async.Redis:
    global _redis_client
    if _redis_client is None:
        return await init_redis()
    return _redis_client
