"""部门管理 API — 部门列表、配额设置、模型锁定"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ApiResponse, ok
from app.core.nats_client import publish_config_change
from app.models.user import User
from app.models.department import Department
from app.models.department_quota import DepartmentQuota
from app.models.department_model_lock import DepartmentModelLock
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/v1/departments", tags=["部门管理"])


class DepartmentCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=64)
    head_user_id: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    code: str
    name: str
    head_user_id: Optional[str]
    is_active: bool


class QuotaUpdateRequest(BaseModel):
    max_concurrent_tasks: Optional[int] = Field(None, ge=1)
    max_daily_api_budget: Optional[float] = Field(None, ge=0)
    max_daily_upload_mb: Optional[int] = Field(None, ge=1)
    max_user_rate: Optional[int] = Field(None, ge=1)


class QuotaResponse(BaseModel):
    department_id: str
    max_concurrent_tasks: int
    max_daily_api_budget: Optional[float]
    max_daily_upload_mb: int
    max_user_rate: int


class ModelLockRequest(BaseModel):
    task_type: str = Field(..., min_length=1)
    locked_model: str = Field(..., min_length=1)


class ModelLockResponse(BaseModel):
    id: str
    department_id: str
    task_type: str
    locked_model: str


@router.get("", response_model=ApiResponse[List[DepartmentResponse]])
async def list_departments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取所有部门（所有人可见）"""
    result = await db.execute(select(Department).where(Department.is_active == True).order_by(Department.name))
    depts = result.scalars().all()
    return ok([DepartmentResponse(id=d.id, code=d.code, name=d.name, head_user_id=d.head_user_id, is_active=d.is_active) for d in depts])


@router.post("", response_model=ApiResponse[DepartmentResponse], status_code=201)
async def create_department(
    request: DepartmentCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """创建部门（仅管理员）"""
    existing = await db.execute(select(Department).where(Department.code == request.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="部门代码已存在")

    dept = Department(code=request.code, name=request.name, head_user_id=request.head_user_id)
    db.add(dept)

    # 自动创建默认配额
    quota = DepartmentQuota(department_id=dept.id)
    db.add(quota)

    await db.flush()
    return ok(DepartmentResponse(id=dept.id, code=dept.code, name=dept.name, head_user_id=dept.head_user_id, is_active=dept.is_active))


@router.get("/{dept_id}/quota", response_model=ApiResponse[QuotaResponse])
async def get_quota(
    dept_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """查看部门配额"""
    if current_user.role == "member" and current_user.department_id != dept_id:
        raise HTTPException(status_code=403, detail="无权查看其他部门配额")

    result = await db.execute(select(DepartmentQuota).where(DepartmentQuota.department_id == dept_id))
    quota = result.scalar_one_or_none()
    if quota is None:
        raise HTTPException(status_code=404, detail="配额未设置")

    return ok(QuotaResponse(
        department_id=quota.department_id,
        max_concurrent_tasks=quota.max_concurrent_tasks,
        max_daily_api_budget=quota.max_daily_api_budget,
        max_daily_upload_mb=quota.max_daily_upload_mb,
        max_user_rate=quota.max_user_rate,
    ))


@router.put("/{dept_id}/quota", response_model=ApiResponse[QuotaResponse])
async def update_quota(
    dept_id: str,
    request: QuotaUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
):
    """更新部门配额（管理员或本部门主管）"""
    if current_user.role == "dept_head" and current_user.department_id != dept_id:
        raise HTTPException(status_code=403, detail="只能修改本部门配额")

    result = await db.execute(select(DepartmentQuota).where(DepartmentQuota.department_id == dept_id))
    quota = result.scalar_one_or_none()

    if quota is None:
        quota = DepartmentQuota(department_id=dept_id)
        db.add(quota)

    if request.max_concurrent_tasks is not None:
        quota.max_concurrent_tasks = request.max_concurrent_tasks
    if request.max_daily_api_budget is not None:
        quota.max_daily_api_budget = request.max_daily_api_budget
    if request.max_daily_upload_mb is not None:
        quota.max_daily_upload_mb = request.max_daily_upload_mb
    if request.max_user_rate is not None:
        quota.max_user_rate = request.max_user_rate

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="update_quota",
        target_type="department",
        target_id=dept_id,
        new_value=request.model_dump(exclude_none=True),
    ))
    await db.flush()

    return ok(QuotaResponse(
        department_id=quota.department_id,
        max_concurrent_tasks=quota.max_concurrent_tasks,
        max_daily_api_budget=quota.max_daily_api_budget,
        max_daily_upload_mb=quota.max_daily_upload_mb,
        max_user_rate=quota.max_user_rate,
    ))


@router.get("/{dept_id}/model-locks", response_model=ApiResponse[List[ModelLockResponse]])
async def get_model_locks(
    dept_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """查看部门模型锁定配置"""
    result = await db.execute(
        select(DepartmentModelLock).where(DepartmentModelLock.department_id == dept_id)
    )
    locks = result.scalars().all()
    return ok([ModelLockResponse(id=l.id, department_id=l.department_id, task_type=l.task_type, locked_model=l.locked_model) for l in locks])


@router.post("/{dept_id}/model-locks", response_model=ApiResponse[ModelLockResponse], status_code=201)
async def set_model_lock(
    dept_id: str,
    request: ModelLockRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
):
    """设置部门模型锁（决策 4 第三级），变更通过 NATS 热推送"""
    if current_user.role == "dept_head" and current_user.department_id != dept_id:
        raise HTTPException(status_code=403, detail="只能设置本部门锁定")

    # 先删旧锁（幂等）
    result = await db.execute(
        select(DepartmentModelLock).where(
            DepartmentModelLock.department_id == dept_id,
            DepartmentModelLock.task_type == request.task_type,
        )
    )
    old_lock = result.scalar_one_or_none()
    if old_lock:
        await db.delete(old_lock)

    lock = DepartmentModelLock(
        department_id=dept_id,
        task_type=request.task_type,
        locked_model=request.locked_model,
        locked_by=current_user.id,
    )
    db.add(lock)
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="lock_model",
        target_type="department",
        target_id=dept_id,
        new_value={"task_type": request.task_type, "locked_model": request.locked_model},
    ))
    await db.flush()

    # NATS 热推送
    await publish_config_change(f"model_lock.{dept_id}", {
        "event": "lock_set",
        "department_id": dept_id,
        "task_type": request.task_type,
        "locked_model": request.locked_model,
    })

    return ok(ModelLockResponse(id=lock.id, department_id=lock.department_id, task_type=lock.task_type, locked_model=lock.locked_model))


@router.delete("/{dept_id}/model-locks/{lock_id}", response_model=ApiResponse[dict])
async def remove_model_lock(
    dept_id: str,
    lock_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
):
    """解除模型锁定"""
    if current_user.role == "dept_head" and current_user.department_id != dept_id:
        raise HTTPException(status_code=403, detail="只能修改本部门配置")

    result = await db.execute(
        select(DepartmentModelLock).where(
            DepartmentModelLock.id == lock_id,
            DepartmentModelLock.department_id == dept_id,
        )
    )
    lock = result.scalar_one_or_none()
    if lock is None:
        raise HTTPException(status_code=404, detail="锁定配置不存在")

    await db.delete(lock)
    await publish_config_change(f"model_lock.{dept_id}", {
        "event": "lock_removed",
        "department_id": dept_id,
        "lock_id": lock_id,
    })
    await db.flush()

    return ok({"deleted": True})
