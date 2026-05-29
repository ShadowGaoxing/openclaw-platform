"""管理后台 API — 数据看板、审计日志、用户管理"""
from typing import Annotated, Optional, List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ApiResponse, ok
from app.core.redis_client import get_redis
from app.models.user import User
from app.models.task import Task
from app.models.audit_log import AuditLog
from app.models.agent import Agent

router = APIRouter(prefix="/api/v1/admin", tags=["管理后台"])


class DashboardStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int
    dead_tasks: int
    online_agents: int
    offline_agents: int
    suspected_agents: int
    today_completed: int


class AuditLogResponse(BaseModel):
    id: int
    actor_id: str
    actor_role: str
    action_type: str
    target_type: str
    target_id: str
    old_value: Optional[dict]
    new_value: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime


@router.get("/stats", response_model=ApiResponse[DashboardStats])
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
    department_id: Optional[str] = None,
):
    """获取数据看板统计"""
    task_q = select(Task)
    agent_q = select(Agent)

    # 非管理员只看本部门
    if current_user.role != "admin":
        dept = department_id or current_user.department_id
        task_q = task_q.where(Task.department_id == dept)
        agent_q = agent_q.where(Agent.department_id == dept)
    elif department_id:
        task_q = task_q.where(Task.department_id == department_id)
        agent_q = agent_q.where(Agent.department_id == department_id)

    task_result = await db.execute(task_q)
    tasks = task_result.scalars().all()

    agent_result = await db.execute(agent_q)
    agents = agent_result.scalars().all()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_completed = sum(1 for t in tasks if t.status == "completed" and t.completed_at and t.completed_at >= today_start)

    return ok(DashboardStats(
        total_tasks=len(tasks),
        pending_tasks=sum(1 for t in tasks if t.status == "pending"),
        processing_tasks=sum(1 for t in tasks if t.status == "processing"),
        completed_tasks=sum(1 for t in tasks if t.status == "completed"),
        failed_tasks=sum(1 for t in tasks if t.status == "failed"),
        dead_tasks=sum(1 for t in tasks if t.status == "dead"),
        online_agents=sum(1 for a in agents if a.status == "online"),
        offline_agents=sum(1 for a in agents if a.status in ("offline", "stale")),
        suspected_agents=sum(1 for a in agents if a.status == "suspected_failure"),
        today_completed=today_completed,
    ))


@router.get("/audit-logs", response_model=ApiResponse[List[AuditLogResponse]])
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    """查看审计日志（管理员/主管）"""
    query = select(AuditLog)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return ok([AuditLogResponse(
        id=l.id,
        actor_id=l.actor_id,
        actor_role=l.actor_role,
        action_type=l.action_type,
        target_type=l.target_type,
        target_id=l.target_id,
        old_value=l.old_value,
        new_value=l.new_value,
        ip_address=l.ip_address,
        created_at=l.created_at,
    ) for l in logs])
