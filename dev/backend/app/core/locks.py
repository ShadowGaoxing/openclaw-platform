"""分布式锁模块 — 调度器级 run_once + 任务级 acquire/release

约束来源: 架构约束文档 §1（周建国）
改动规格: 修改规格文档 B.2（陈思远 V2.0）

注意: redis_client 已启用 decode_responses=True，get 返回 str 而非 bytes。
"""

import os
import logging
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

# 全局唯一的 worker_id（主机名或容器 ID）
WORKER_ID = os.uname().nodename


async def run_once(job_name: str, fn, *args, ttl: int = 65, **kwargs):
    """调度器级分布式锁。

    确保全局只有一个 APScheduler worker 执行此定时任务。

    Args:
        job_name: 任务名称（全局唯一，如 'check_claim_timeouts'）
        fn: 异步函数
        ttl: 锁自动过期秒数。默认 65s（60s 调度间隔 + 5s 缓冲），
             30s 周期的任务（如 check_agent_heartbeats）应传 ttl=35。
    """
    redis = await get_redis()
    lock_key = f"scheduler:lock:{job_name}"

    # SET NX EX — 锁不存在才写入
    acquired = await redis.set(lock_key, WORKER_ID, ex=ttl, nx=True)
    if not acquired:
        logger.debug(f"Skipping {job_name} — already running on worker {WORKER_ID}")
        return

    try:
        await fn(*args, **kwargs)
    finally:
        # ownership 校验：只有自己是锁的持有者才释放
        owner = await redis.get(lock_key)
        if owner == WORKER_ID:
            await redis.delete(lock_key)
        elif owner is not None:
            # 锁被其他 worker 持有（可能在 TTL 内被另一个实例覆盖）
            logger.warning(
                "Skipping lock release for %s: owned by %s (self=%s)",
                lock_key, owner, WORKER_ID,
            )


async def acquire_task_lock(task_id: str, ttl: int = 30) -> bool:
    """任务级互斥锁。领取单任务时使用。

    Returns:
        True = 成功获取锁（可以处理此任务）
        False = 锁已被其他 worker 持有（跳过此任务）
    """
    redis = await get_redis()
    lock_key = f"task:lock:{task_id}"
    acquired = await redis.set(lock_key, WORKER_ID, ex=ttl, nx=True)
    return bool(acquired)


async def release_task_lock(task_id: str):
    """释放任务锁（仅限 owner）。"""
    redis = await get_redis()
    lock_key = f"task:lock:{task_id}"
    owner = await redis.get(lock_key)
    if owner == WORKER_ID:
        await redis.delete(lock_key)
    elif owner is not None:
        logger.warning(
            "Skipping task lock release for %s: owned by %s (self=%s)",
            lock_key, owner, WORKER_ID,
        )
