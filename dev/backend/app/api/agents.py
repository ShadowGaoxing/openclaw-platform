"""Agent 管理 API — 注册/心跳/列表/状态"""
from datetime import datetime, timezone, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ApiResponse, ok
from app.core.redis_client import get_redis
from app.models.user import User
from app.models.agent import Agent

router = APIRouter(prefix="/api/v1/agents", tags=["Agent 管理"])

# 心跳超时阈值
SUSPECTED_THRESHOLD_S = 90   # 90s → suspected_failure
STALE_THRESHOLD_S = 120       # 120s → stale


class AgentRegisterRequest(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=128)
    version: str = Field(..., max_length=32)
    department_id: str
    max_concurrency: int = Field(default=2, ge=1, le=16)
    available_models: List[str] = Field(default=[])
    ip_address: Optional[str] = None


class HeartbeatRequest(BaseModel):
    agent_name: str
    current_concurrency: int = Field(default=0, ge=0)
    cpu_pct: Optional[float] = None
    mem_pct: Optional[float] = None
    gpu_pct: Optional[float] = None
    available_models: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: str
    agent_name: str
    user_id: Optional[str]
    department_id: str
    version: Optional[str]
    status: str
    current_concurrency: int
    max_concurrency: int
    cpu_pct: Optional[float]
    mem_pct: Optional[float]
    gpu_pct: Optional[float]
    available_models: Optional[List[str]]
    ip_address: Optional[str]
    last_seen_at: Optional[datetime]
    registered_at: datetime


@router.post("/register", response_model=ApiResponse[AgentResponse], status_code=201)
async def register_agent(
    request: AgentRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    http_request: Request = None,
):
    """Agent 启动时注册（幂等：已存在则更新）"""
    result = await db.execute(select(Agent).where(Agent.agent_name == request.agent_name))
    agent = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if agent is None:
        agent = Agent(
            agent_name=request.agent_name,
            user_id=current_user.id,
            department_id=request.department_id,
            version=request.version,
            max_concurrency=request.max_concurrency,
            available_models=request.available_models,
            ip_address=request.ip_address,
            status="online",
            last_seen_at=now,
        )
        db.add(agent)
    else:
        agent.user_id = current_user.id
        agent.version = request.version
        agent.max_concurrency = request.max_concurrency
        agent.available_models = request.available_models
        agent.ip_address = request.ip_address
        agent.status = "online"
        agent.last_seen_at = now

    await db.flush()

    # 同时写 Redis 心跳（TTL 60s）
    redis = await get_redis()
    await redis.setex(f"agent:heartbeat:{request.agent_name}", 60, "online")

    return ok(_agent_to_response(agent), message="Agent 已注册")


@router.post("/heartbeat", response_model=ApiResponse[dict])
async def agent_heartbeat(
    request: HeartbeatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Agent 心跳上报（每 30s 一次，写 Redis；状态变更才写 DB）

    PRD V2.2 §5.3：心跳写 Redis TTL 60s，状态变更才写 PG。
    Fallback：如果 Redis 写失败，降级为直接写 PG。
    """
    now = datetime.now(timezone.utc)
    redis_key = f"agent:heartbeat:{request.agent_name}"

    # 尝试写 Redis
    redis_ok = False
    try:
        redis = await get_redis()
        await redis.setex(redis_key, 60, "online")
        # 同时更新实时指标（hash）
        await redis.hset(
            f"agent:metrics:{request.agent_name}",
            mapping={
                "current_concurrency": request.current_concurrency,
                "cpu_pct": request.cpu_pct or 0,
                "mem_pct": request.mem_pct or 0,
                "gpu_pct": request.gpu_pct or 0,
                "last_seen": now.isoformat(),
            },
        )
        await redis.expire(f"agent:metrics:{request.agent_name}", 120)
        redis_ok = True
    except Exception:
        redis_ok = False

    # 状态变更 才写 PG（例如之前是 offline → online）
    result = await db.execute(select(Agent).where(Agent.agent_name == request.agent_name))
    agent = result.scalar_one_or_none()

    if agent:
        changed = agent.status not in ("online",) or not redis_ok
        if changed:
            agent.status = "online"
            agent.last_seen_at = now
            agent.current_concurrency = request.current_concurrency
            if request.available_models is not None:
                agent.available_models = request.available_models
            await db.flush()

    return ok(
        {
            "agent_name": request.agent_name,
            "redis_ok": redis_ok,
            "server_time": now.isoformat(),
        }
    )


@router.get("/heartbeat-fallback", response_model=ApiResponse[dict])
async def heartbeat_fallback(
    agent_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Redis 异常降级：心跳直接写 PG（PRD §5.3 兜底策略）"""
    result = await db.execute(select(Agent).where(Agent.agent_name == agent_name))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent 未注册")

    now = datetime.now(timezone.utc)
    agent.last_seen_at = now
    agent.status = "online"
    await db.flush()

    return ok({"agent_name": agent_name, "fallback": True, "server_time": now.isoformat()})


@router.get("", response_model=ApiResponse[List[AgentResponse]])
async def list_agents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    department_id: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """查看 Agent 列表（管理员看全部；其他人看本部门）"""
    query = select(Agent)

    if current_user.role != "admin":
        query = query.where(Agent.department_id == current_user.department_id)
    elif department_id:
        query = query.where(Agent.department_id == department_id)

    if status_filter:
        query = query.where(Agent.status == status_filter)

    query = query.order_by(Agent.last_seen_at.desc())
    result = await db.execute(query)
    agents = result.scalars().all()

    return ok([_agent_to_response(a) for a in agents])


def _agent_to_response(agent: Agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        agent_name=agent.agent_name,
        user_id=agent.user_id,
        department_id=agent.department_id,
        version=agent.version,
        status=agent.status,
        current_concurrency=agent.current_concurrency,
        max_concurrency=agent.max_concurrency,
        cpu_pct=agent.cpu_pct,
        mem_pct=agent.mem_pct,
        gpu_pct=agent.gpu_pct,
        available_models=agent.available_models,
        ip_address=agent.ip_address,
        last_seen_at=agent.last_seen_at,
        registered_at=agent.registered_at,
    )
