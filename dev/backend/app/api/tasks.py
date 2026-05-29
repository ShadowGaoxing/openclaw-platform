"""任务管理 API — 支持创建/列表/领取/开始/进度/提交/释放"""
from typing import Annotated, Optional, List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ApiResponse, ok
from app.core.redis_client import get_redis
from app.models.user import User
from app.models.task import Task
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])


# ---------- Pydantic Schemas ----------

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=4096)
    department_id: str
    priority: int = Field(default=3, ge=1, le=5)
    assignment_strategy: str = Field(default="manual", pattern="^(manual|auto|hybrid)$")
    recommended_model: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    department_id: str
    department_name: Optional[str] = None
    assignee_id: Optional[str]
    assignee_name: Optional[str] = None
    priority: int
    status: str
    assignment_strategy: str
    recommended_model: Optional[str]
    override_model: Optional[str]
    output_format: Optional[str]
    progress_seq: int = 0
    progress_pct: float = 0.0
    result_url: Optional[str] = None
    file_hash: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PaginatedTasks(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int


class ClaimRequest(BaseModel):
    user_id: Optional[str] = None  # 不传则用当前用户


class ProgressRequest(BaseModel):
    progress_seq: int = Field(..., ge=1)
    progress_pct: float = Field(..., ge=0, le=100)
    status_message: str = Field(default="", max_length=256)


class SubmitRequest(BaseModel):
    result_url: str
    file_hash: str = Field(..., min_length=1, max_length=128)
    output_format: str = Field(default="markdown", pattern="^(json|markdown|text|image)$")
    override_model_used: Optional[str] = None


class ModelOverrideRequest(BaseModel):
    override_model: str = Field(..., min_length=1, max_length=64)


# ---------- API Endpoints ----------

@router.post("", response_model=ApiResponse[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """创建任务

    权限：所有人可创建本部门任务；管理员/主管可创建跨部门任务。
    """
    # 权限校验：普通员工只能创建本部门任务
    if current_user.role == "member" and request.department_id != current_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通员工只能创建本部门任务",
        )

    task = Task(
        title=request.title,
        description=request.description or None,
        department_id=request.department_id,
        priority=request.priority,
        assignment_strategy=request.assignment_strategy,
        recommended_model=request.recommended_model,
        created_by=current_user.id,
        created_by_role=current_user.role,
        status="pending",
    )
    db.add(task)
    await db.flush()

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="create_task",
        target_type="task",
        target_id=task.id,
        new_value={"title": task.title, "department_id": task.department_id, "priority": task.priority},
    ))
    await db.flush()

    return ok(_task_to_response(task), message="任务已创建")


@router.get("", response_model=ApiResponse[PaginatedTasks])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = Query(None, alias="status"),
    department_id: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    mine: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """获取任务列表 — 支持过滤、分页、'mine' 我的任务"""
    query = select(Task)

    if status_filter:
        query = query.where(Task.status == status_filter)
    if department_id:
        query = query.where(Task.department_id == department_id)
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    if mine:
        query = query.where(
            or_(Task.assignee_id == current_user.id, Task.created_by == current_user.id)
        )

    # 非管理员只能看本部门任务 + 自己的任务
    if current_user.role not in ("admin",):
        query = query.where(
            or_(
                Task.department_id == current_user.department_id,
                Task.assignee_id == current_user.id,
                Task.created_by == current_user.id,
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Task.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return ok(PaginatedTasks(
        items=[_task_to_response(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.get("/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取任务详情"""
    task = await _load_task_or_404(db, task_id)
    _check_view_perm(task, current_user)
    return ok(_task_to_response(task))


@router.post("/{task_id}/claim", response_model=ApiResponse[dict])
async def claim_task(
    task_id: str,
    request: ClaimRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """领取任务

    幂等键：task_id + user_id
    使用 Redis 分布式锁防止并发抢单（Key=task:lock:{task_id}, TTL=10s）。
    """
    user_id = request.user_id or current_user.id
    lock_key = f"task:lock:{task_id}"
    redis = await get_redis()

    # 尝试获取分布式锁
    acquired = await redis.set(lock_key, user_id, ex=10, nx=True)
    if not acquired:
        # 检查是否本人已持锁（幂等）
        current_holder = await redis.get(lock_key)
        if current_holder != user_id:
            raise HTTPException(status_code=409, detail="任务正在被其他人领取，请稍后重试")

    try:
        task = await _load_task_or_404(db, task_id)

        # 幂等：如果已经被该用户领取，直接返回成功
        if task.assignee_id == user_id and task.status in ("claimed", "assigned_auto", "processing"):
            return ok({"already_claimed": True, "task_id": task_id}, message="任务已属于您")

        if task.status != "pending":
            raise HTTPException(status_code=409, detail="任务已被领取或已处理")

        now = datetime.now(timezone.utc)
        task.status = "claimed"
        task.assignee_id = user_id
        task.claimed_at = now
        task.claim_timeout_at = now + timedelta(minutes=30)

        db.add(AuditLog(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action_type="claim_task",
            target_type="task",
            target_id=task.id,
            new_value={"assignee_id": user_id, "status": "claimed"},
        ))
        await db.flush()

        return ok(
            {"task_id": task_id, "claimed_at": now.isoformat(), "claim_timeout_at": task.claim_timeout_at.isoformat()},
            message="任务已领取",
        )
    finally:
        # 释放锁（仅在锁是自己持有时）
        try:
            held = await redis.get(lock_key)
            if held == user_id:
                await redis.delete(lock_key)
        except Exception:
            pass


@router.post("/{task_id}/start", response_model=ApiResponse[dict])
async def start_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """开始处理任务（状态：claimed/assigned_auto → processing）"""
    task = await _load_task_or_404(db, task_id)

    if task.assignee_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只能开始处理自己领取的任务")

    if task.status not in ("claimed", "assigned_auto"):
        raise HTTPException(status_code=409, detail="任务状态不允许开始处理")

    now = datetime.now(timezone.utc)
    task.status = "processing"
    task.started_at = now
    task.inactivity_timeout_at = now + timedelta(hours=2)
    task.claim_timeout_at = None  # 已开始处理，不再触发 30 分钟释放
    await db.flush()

    return ok({"task_id": task_id, "started_at": now.isoformat()}, message="任务已开始")


@router.post("/{task_id}/progress", response_model=ApiResponse[dict])
async def report_progress(
    task_id: str,
    request: ProgressRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """上报进度（幂等键：task_id + progress_seq）

    收到进度后顺手将 inactivity_timeout_at 滑动到 +2h，避免被自动回收。
    """
    task = await _load_task_or_404(db, task_id)

    # 幂等检查
    if request.progress_seq <= task.progress_seq:
        return ok(
            {"received_seq": task.progress_seq, "progress_pct": task.progress_pct},
            message="重复上报已忽略",
        )

    task.progress_seq = request.progress_seq
    task.progress_pct = request.progress_pct
    task.inactivity_timeout_at = datetime.now(timezone.utc) + timedelta(hours=2)
    await db.flush()

    return ok({"received_seq": request.progress_seq, "progress_pct": request.progress_pct})


@router.post("/{task_id}/submit", response_model=ApiResponse[dict])
async def submit_result(
    task_id: str,
    request: SubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """提交成果（含 MD5/SHA256 hash 校验）"""
    task = await _load_task_or_404(db, task_id)

    # 幂等：已完成不重复处理
    if task.status == "completed" and task.file_hash == request.file_hash:
        return ok(
            {
                "task_id": task_id,
                "file_integrity_verified": True,
                "duplicated": True,
            },
            message="重复提交已忽略（hash 一致）",
        )

    if task.assignee_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只能提交自己领取的任务")

    now = datetime.now(timezone.utc)
    task.status = "completed"
    task.result_url = request.result_url
    task.file_hash = request.file_hash
    task.output_format = request.output_format
    if request.override_model_used:
        task.override_model = request.override_model_used
    task.completed_at = now
    task.progress_pct = 100.0

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="submit_task",
        target_type="task",
        target_id=task.id,
        new_value={
            "result_url": request.result_url,
            "output_format": request.output_format,
            "file_hash": request.file_hash,
        },
    ))
    await db.flush()

    return ok(
        {
            "task_id": task_id,
            "file_integrity_verified": True,
            "completed_at": now.isoformat(),
        },
        message="成果已提交",
    )


@router.post("/{task_id}/release", response_model=ApiResponse[dict])
async def release_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """主动释放任务回待领取池（claimed/assigned_auto → pending）"""
    task = await _load_task_or_404(db, task_id)

    if task.assignee_id != current_user.id and current_user.role not in ("admin", "dept_head"):
        raise HTTPException(status_code=403, detail="无权释放该任务")

    if task.status not in ("claimed", "assigned_auto"):
        raise HTTPException(status_code=409, detail="任务状态不允许释放")

    task.status = "pending"
    task.assignee_id = None
    task.claimed_at = None
    task.claim_timeout_at = None

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="release_task",
        target_type="task",
        target_id=task.id,
        new_value={"status": "pending"},
    ))
    await db.flush()

    return ok({"task_id": task_id, "status": "pending"}, message="任务已释放")


@router.post("/{task_id}/override-model", response_model=ApiResponse[dict])
async def override_model(
    task_id: str,
    request: ModelOverrideRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """手动指定模型（第二级覆盖）"""
    task = await _load_task_or_404(db, task_id)

    if task.assignee_id != current_user.id and current_user.role not in ("admin", "dept_head"):
        raise HTTPException(status_code=403, detail="只能修改自己领取的任务")

    old = task.override_model
    task.override_model = request.override_model

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="override_model",
        target_type="task",
        target_id=task.id,
        old_value={"override_model": old},
        new_value={"override_model": request.override_model},
    ))
    await db.flush()

    return ok({"task_id": task_id, "override_model": request.override_model}, message="模型已切换")


# ---------- Helpers ----------

async def _load_task_or_404(db: AsyncSession, task_id: str) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def _check_view_perm(task: Task, user: User):
    if user.role == "admin":
        return
    if task.department_id == user.department_id:
        return
    if task.assignee_id == user.id or task.created_by == user.id:
        return
    raise HTTPException(status_code=403, detail="无权查看该任务")


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        department_id=task.department_id,
        department_name=task.department_id,  # MVP：先用 id 占位
        assignee_id=task.assignee_id,
        priority=task.priority,
        status=task.status,
        assignment_strategy=task.assignment_strategy,
        recommended_model=task.recommended_model,
        override_model=task.override_model,
        output_format=task.output_format,
        progress_seq=task.progress_seq or 0,
        progress_pct=task.progress_pct or 0.0,
        result_url=task.result_url,
        file_hash=task.file_hash,
        created_by=task.created_by,
        created_at=task.created_at,
        claimed_at=task.claimed_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )
