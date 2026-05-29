"""成果共享 API — 一键分享/跨部门审批/共享库查询"""
from typing import Annotated, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ApiResponse, ok
from app.models.user import User
from app.models.task import Task
from app.models.shared_result import SharedResult
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/v1/shared", tags=["成果共享"])


class ShareRequest(BaseModel):
    task_id: str
    target_department_id: Optional[str] = None   # None = 同部门自动归档
    target_user_id: Optional[str] = None
    file_url: str
    file_hash: Optional[str] = None
    output_format: str = Field(default="markdown", pattern="^(json|markdown|text|image)$")


class SharedResultResponse(BaseModel):
    id: str
    task_id: str
    title: Optional[str] = None
    source_department_id: str
    source_department_name: Optional[str] = None
    target_department_id: Optional[str]
    target_user_id: Optional[str]
    approval_status: str
    file_url: str
    file_hash: Optional[str]
    output_format: Optional[str]
    created_at: datetime


class ApproveRequest(BaseModel):
    action: str = Field(..., pattern="^(approved|rejected)$")


async def _enrich_with_task(db: AsyncSession, shared: SharedResult) -> SharedResultResponse:
    result = await db.execute(select(Task).where(Task.id == shared.task_id))
    task = result.scalar_one_or_none()
    return SharedResultResponse(
        id=shared.id,
        task_id=shared.task_id,
        title=task.title if task else None,
        source_department_id=shared.source_department_id,
        source_department_name=shared.source_department_id,
        target_department_id=shared.target_department_id,
        target_user_id=shared.target_user_id,
        approval_status=shared.approval_status,
        file_url=shared.file_url,
        file_hash=shared.file_hash,
        output_format=shared.output_format,
        created_at=shared.created_at,
    )


@router.post("", response_model=ApiResponse[SharedResultResponse], status_code=201)
async def share_result(
    request: ShareRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """分享任务成果

    - 同部门 → auto approved
    - 跨部门 → pending，通知目标部门主管审批
    """
    result = await db.execute(select(Task).where(Task.id == request.task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    is_cross_dept = request.target_department_id and request.target_department_id != current_user.department_id
    approval_status = "pending" if is_cross_dept else "approved"

    shared = SharedResult(
        task_id=request.task_id,
        source_department_id=current_user.department_id,
        target_department_id=request.target_department_id,
        target_user_id=request.target_user_id,
        approval_status=approval_status,
        file_url=request.file_url,
        file_hash=request.file_hash,
        output_format=request.output_format,
    )
    db.add(shared)
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="share_result",
        target_type="task",
        target_id=request.task_id,
        new_value={
            "target_department_id": request.target_department_id,
            "approval_status": approval_status,
        },
    ))
    await db.flush()

    return ok(await _enrich_with_task(db, shared), message="已分享" if approval_status == "approved" else "分享申请已提交，等待审批")


@router.get("", response_model=ApiResponse[List[SharedResultResponse]])
async def list_shared(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[str] = None,
    source_dept: Optional[str] = None,
):
    """查看共享库

    员工只能看：本部门的 approved 成果 + 其他部门主动分享给本部门的 approved 成果。
    管理员可以看全部。
    """
    query = select(SharedResult)

    if current_user.role != "admin":
        query = query.where(
            or_(
                SharedResult.source_department_id == current_user.department_id,
                SharedResult.target_department_id == current_user.department_id,
            )
        ).where(SharedResult.approval_status == "approved")
    else:
        if status_filter:
            query = query.where(SharedResult.approval_status == status_filter)
        if source_dept:
            query = query.where(SharedResult.source_department_id == source_dept)

    query = query.order_by(SharedResult.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    enriched = [await _enrich_with_task(db, i) for i in items]
    return ok(enriched)


@router.get("/pending-approvals", response_model=ApiResponse[List[SharedResultResponse]])
async def pending_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
):
    """待我审批的跨部门分享（部门主管专用）"""
    query = select(SharedResult).where(
        SharedResult.target_department_id == current_user.department_id,
        SharedResult.approval_status == "pending",
    ).order_by(SharedResult.created_at.asc())

    result = await db.execute(query)
    items = result.scalars().all()
    enriched = [await _enrich_with_task(db, i) for i in items]
    return ok(enriched)


@router.post("/{shared_id}/approve", response_model=ApiResponse[SharedResultResponse])
async def approve_share(
    shared_id: str,
    request: ApproveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("dept_head"))],
):
    """审批跨部门分享"""
    result = await db.execute(select(SharedResult).where(SharedResult.id == shared_id))
    shared = result.scalar_one_or_none()
    if shared is None:
        raise HTTPException(status_code=404, detail="分享记录不存在")

    if current_user.role == "dept_head" and shared.target_department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="只能审批发给本部门的分享")

    if shared.approval_status != "pending":
        raise HTTPException(status_code=409, detail="该记录已审批")

    shared.approval_status = request.action
    shared.approved_by = current_user.id

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="approve_share",
        target_type="task",
        target_id=shared.task_id,
        old_value={"approval_status": "pending"},
        new_value={"approval_status": request.action},
    ))
    await db.flush()

    return ok(await _enrich_with_task(db, shared), message=f"分享已{'通过' if request.action == 'approved' else '拒绝'}")


def _shared_to_response(s: SharedResult) -> SharedResultResponse:
    return SharedResultResponse(
        id=s.id,
        task_id=s.task_id,
        source_department_id=s.source_department_id,
        source_department_name=s.source_department_id,
        target_department_id=s.target_department_id,
        target_user_id=s.target_user_id,
        approval_status=s.approval_status,
        file_url=s.file_url,
        file_hash=s.file_hash,
        output_format=s.output_format,
        created_at=s.created_at,
    )
