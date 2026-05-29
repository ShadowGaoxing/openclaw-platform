"""后台定时任务调度器

PRD V2.2 §6.1 + §6.2：
- 每 60s：检查 claim_timeout_at 过期任务 → pending（30 分钟未开始自动释放）
- 每 60s：检查 inactivity_timeout_at 过期任务 → 自动回收，通知管理员
- 每 60s：auto/hybrid 策略且超过 10 分钟无人领取 → 自动兜底分配给最空闲 Agent
- 每 30s：检查 Agent 心跳，超过阈值更新状态（suspected / stale）

调度器去重（V2.2 修复冲刺）：
- 四个定时任务全部包 run_once（Redis 分布式锁）
- auto_fallback_assign 内任务锁加 ownership 校验
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory
from app.core.redis_client import get_redis
from app.core.locks import run_once
from app.models.task import Task
from app.models.agent import Agent
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _get_session() -> AsyncSession:
    return AsyncSessionFactory()


# ---------- 任务超时检查 ----------

async def check_claim_timeouts():
    """30 分钟内未开始 → 自动释放回待领取池"""
    async with AsyncSessionFactory() as db:
        try:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Task).where(
                    Task.status == "claimed",
                    Task.claim_timeout_at <= now,
                    Task.claim_timeout_at != None,
                )
            )
            tasks = result.scalars().all()

            for task in tasks:
                old_assignee = task.assignee_id
                task.status = "pending"
                task.assignee_id = None
                task.claim_timeout_at = None
                task.claimed_at = None

                db.add(AuditLog(
                    actor_id="system",
                    actor_role="system",
                    action_type="claim_timeout",
                    target_type="task",
                    target_id=task.id,
                    new_value={"status": "pending", "reason": "30min_timeout", "released_from": old_assignee},
                ))
                logger.info(f"Task {task.id} released due to claim timeout (was assigned to {old_assignee})")

            if tasks:
                await db.commit()
        except Exception as e:
            logger.error(f"claim timeout check failed: {e}")
            await db.rollback()


async def check_inactivity_timeouts():
    """processing 状态 2 小时无进度上报 → 自动回收"""
    async with AsyncSessionFactory() as db:
        try:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Task).where(
                    Task.status == "processing",
                    Task.inactivity_timeout_at <= now,
                    Task.inactivity_timeout_at != None,
                )
            )
            tasks = result.scalars().all()

            for task in tasks:
                task.status = "pending"
                old_assignee = task.assignee_id
                task.assignee_id = None
                task.started_at = None
                task.inactivity_timeout_at = None

                db.add(AuditLog(
                    actor_id="system",
                    actor_role="system",
                    action_type="inactivity_timeout",
                    target_type="task",
                    target_id=task.id,
                    new_value={"status": "pending", "reason": "2h_inactivity", "released_from": old_assignee},
                ))
                logger.warning(f"Task {task.id} auto-reclaimed due to 2h inactivity (was {old_assignee})")

            if tasks:
                await db.commit()
        except Exception as e:
            logger.error(f"inactivity timeout check failed: {e}")
            await db.rollback()


async def auto_fallback_assign():
    """auto/hybrid 策略任务超过 10 分钟无人领取 → 分配给负载最低的 Agent

    PRD §6.1 决策 3：按 current_concurrency / max_concurrency 比例排序，最低的优先。
    """
    async with AsyncSessionFactory() as db:
        try:
            now = datetime.now(timezone.utc)
            ten_min_ago = now - timedelta(minutes=10)

            # 找满足条件的任务
            result = await db.execute(
                select(Task).where(
                    Task.status == "pending",
                    Task.assignment_strategy.in_(["auto", "hybrid"]),
                    Task.created_at <= ten_min_ago,
                )
            )
            tasks = result.scalars().all()
            if not tasks:
                return

            # 找在线 Agent 中负载最低的
            agent_result = await db.execute(
                select(Agent).where(Agent.status == "online")
            )
            agents = agent_result.scalars().all()
            if not agents:
                return

            # 按负载比率排序
            def load_ratio(a: Agent) -> float:
                if a.max_concurrency == 0:
                    return 1.0
                return a.current_concurrency / a.max_concurrency

            agents_sorted = sorted(agents, key=load_ratio)

            for task in tasks:
                # 找与任务同部门的最低负载 Agent
                dept_agents = [a for a in agents_sorted if a.department_id == task.department_id]
                target = dept_agents[0] if dept_agents else agents_sorted[0]  # fallback 跨部门

                lock_key = f"task:lock:{task.id}"
                redis = await get_redis()
                acquired = await redis.set(lock_key, "system:auto", ex=10, nx=True)
                if not acquired:
                    # 审计日志：任务锁争用
                    db.add(AuditLog(
                        actor_id="system",
                        actor_role="system",
                        action_type="task_lock_contention",
                        target_type="task",
                        target_id=task.id,
                        new_value={"action": "skipped", "reason": "lock_held_by_other_worker"},
                    ))
                    continue  # 有人正在领取，跳过

                try:
                    task.status = "assigned_auto"
                    task.assignee_id = target.user_id
                    task.claimed_at = now
                    task.claim_timeout_at = now + timedelta(minutes=30)

                    db.add(AuditLog(
                        actor_id="system",
                        actor_role="system",
                        action_type="auto_assign",
                        target_type="task",
                        target_id=task.id,
                        new_value={
                            "status": "assigned_auto",
                            "agent": target.agent_name,
                            "load_ratio": load_ratio(target),
                        },
                    ))
                    logger.info(f"Task {task.id} auto-assigned to agent {target.agent_name} (load {load_ratio(target):.2f})")
                finally:
                    # ownership 校验：只有 system:auto 持有者才能释放
                    current_owner = await redis.get(lock_key)
                    if current_owner == "system:auto":
                        await redis.delete(lock_key)
                    elif current_owner is not None:
                        logger.warning(
                            "Skipping task lock release for %s: owned by %s (expected system:auto)",
                            lock_key, current_owner,
                        )

            await db.commit()
        except Exception as e:
            logger.error(f"auto fallback assign failed: {e}")
            await db.rollback()


# ---------- Agent 状态检查 ----------

async def check_agent_heartbeats():
    """检查 Agent 心跳状态，超时则更新状态

    PRD §6.2 §7.1：
    - 90s 未收到 → suspected_failure（告警）
    - 120s 未收到 → stale（自动释放已分配任务）
    """
    async with AsyncSessionFactory() as db:
        try:
            now = datetime.now(timezone.utc)
            suspected_threshold = now - timedelta(seconds=90)
            stale_threshold = now - timedelta(seconds=120)

            result = await db.execute(
                select(Agent).where(Agent.status.in_(["online", "suspected_failure", "reconnecting"]))
            )
            agents = result.scalars().all()

            for agent in agents:
                if agent.last_seen_at is None:
                    continue

                if agent.last_seen_at <= stale_threshold:
                    if agent.status != "stale":
                        agent.status = "stale"
                        # 释放该 agent 分配的任务
                        await _release_agent_tasks(db, agent.user_id, reason="agent_stale")
                        logger.warning(f"Agent {agent.agent_name} marked as stale (last seen: {agent.last_seen_at})")
                elif agent.last_seen_at <= suspected_threshold:
                    if agent.status != "suspected_failure":
                        agent.status = "suspected_failure"
                        agent.suspected_at = now
                        logger.warning(f"Agent {agent.agent_name} suspected failure (last seen: {agent.last_seen_at})")

            await db.commit()
        except Exception as e:
            logger.error(f"agent heartbeat check failed: {e}")
            await db.rollback()


async def _release_agent_tasks(db: AsyncSession, user_id: str, reason: str):
    """释放某 Agent 持有的所有 claimed/processing 任务"""
    if not user_id:
        return
    result = await db.execute(
        select(Task).where(
            Task.assignee_id == user_id,
            Task.status.in_(["claimed", "assigned_auto", "processing"]),
        )
    )
    tasks = result.scalars().all()
    for task in tasks:
        task.status = "pending"
        task.assignee_id = None
        task.claimed_at = None
        task.claim_timeout_at = None
        db.add(AuditLog(
            actor_id="system",
            actor_role="system",
            action_type="agent_stale_release",
            target_type="task",
            target_id=task.id,
            new_value={"status": "pending", "reason": reason},
        ))


# ---------- 调度器初始化 ----------

def setup_scheduler():
    """注册所有定时任务（带分布式锁）"""

    async def safe_claim_timeouts():
        await run_once("check_claim_timeouts", check_claim_timeouts)

    async def safe_inactivity_timeouts():
        await run_once("check_inactivity_timeouts", check_inactivity_timeouts)

    async def safe_auto_assign():
        await run_once("auto_fallback_assign", auto_fallback_assign)

    async def safe_agent_heartbeats():
        await run_once("check_agent_heartbeats", check_agent_heartbeats, ttl=35)

    scheduler.add_job(
        safe_claim_timeouts,
        "interval",
        seconds=60,
        id="check_claim_timeouts",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        safe_inactivity_timeouts,
        "interval",
        seconds=60,
        id="check_inactivity_timeouts",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        safe_auto_assign,
        "interval",
        seconds=60,
        id="auto_fallback_assign",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        safe_agent_heartbeats,
        "interval",
        seconds=30,
        id="check_agent_heartbeats",
        max_instances=1,
        coalesce=True,
    )
