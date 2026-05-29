"""NATS 客户端 — Pub/Sub 进度/状态推送，所有 Agent 共用单连接"""
import asyncio
import json
import logging
from typing import Optional

import nats
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_nc: Optional[NatsClient] = None
_js: Optional[JetStreamContext] = None
_connection_lock = asyncio.Lock()


async def init_nats() -> Optional[NatsClient]:
    """初始化 NATS 连接 + JetStream

    PRD V2.2 §3：必须开 JetStream + at-least-once + 手动 ACK。
    MVP 阶段 NATS 服务可能未启动 → 容错降级（不阻塞 FastAPI 启动）。
    """
    global _nc, _js
    if _nc is not None and _nc.is_connected:
        return _nc

    async with _connection_lock:
        if _nc is not None and _nc.is_connected:
            return _nc
        settings = get_settings()
        try:
            _nc = await nats.connect(
                settings.nats_url,
                name="openclaw-backend",
                connect_timeout=3,
                max_reconnect_attempts=-1,  # 无限重连
            )
            _js = _nc.jetstream()
            # 创建关键 stream（幂等）
            try:
                await _js.add_stream(
                    name="TASK_PROGRESS",
                    subjects=["task.progress.>", "task.status.>"],
                    max_msgs=100000,
                    max_bytes=1 * 1024 * 1024 * 1024,  # 1GB
                    max_msg_size=10 * 1024 * 1024,  # 10MB
                )
            except Exception as e:
                logger.info(f"TASK_PROGRESS stream 已存在或创建失败: {e}")
            logger.info(f"NATS 已连接: {settings.nats_url}")
            return _nc
        except Exception as e:
            logger.warning(f"NATS 连接失败（降级，不阻塞启动）: {e}")
            _nc = None
            _js = None
            return None


async def close_nats():
    global _nc, _js
    if _nc:
        try:
            await _nc.drain()
        except Exception:
            pass
        _nc = None
        _js = None


async def publish_task_status(task_id: str, department_id: str, payload: dict):
    """发布任务状态变更事件（subject: task.status.{dept}.{task_id}）"""
    if _nc is None or not _nc.is_connected:
        return
    subject = f"task.status.{department_id}.{task_id}"
    try:
        await _nc.publish(subject, json.dumps(payload, default=str).encode())
    except Exception as e:
        logger.warning(f"发布状态失败 {subject}: {e}")


async def publish_task_progress(task_id: str, payload: dict):
    """发布任务进度（subject: task.progress.{task_id}）"""
    if _nc is None or not _nc.is_connected:
        return
    subject = f"task.progress.{task_id}"
    try:
        await _nc.publish(subject, json.dumps(payload, default=str).encode())
    except Exception as e:
        logger.warning(f"发布进度失败 {subject}: {e}")


async def publish_config_change(scope: str, payload: dict):
    """推送配置热更新（subject: config.{scope}）"""
    if _nc is None or not _nc.is_connected:
        return
    subject = f"config.{scope}"
    try:
        await _nc.publish(subject, json.dumps(payload, default=str).encode())
    except Exception as e:
        logger.warning(f"配置推送失败 {subject}: {e}")
