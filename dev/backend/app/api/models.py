"""模型注册表 API — CRUD + 路由查询"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ApiResponse, ok
from app.core.nats_client import publish_config_change
from app.models.user import User
from app.models.model_registry import ModelRegistry
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/v1/models", tags=["模型管理"])


class ModelCreateRequest(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=128)
    model_type: str = Field(..., pattern="^(local|api)$")
    deploy_location: Optional[str] = None
    supported_task_types: List[str] = Field(default=[])
    cost_per_call: float = Field(default=0.0, ge=0)
    avg_latency_ms: Optional[int] = None
    status: str = Field(default="online", pattern="^(online|offline|degraded)$")
    max_pool_size: Optional[int] = None
    min_ram_gb: Optional[float] = None
    version: Optional[str] = None


class ModelUpdateRequest(BaseModel):
    model_type: Optional[str] = Field(None, pattern="^(local|api)$")
    deploy_location: Optional[str] = None
    supported_task_types: Optional[List[str]] = None
    cost_per_call: Optional[float] = Field(None, ge=0)
    avg_latency_ms: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(online|offline|degraded)$")
    max_pool_size: Optional[int] = None
    min_ram_gb: Optional[float] = None
    version: Optional[str] = None


class ModelResponse(BaseModel):
    id: str
    model_name: str
    model_type: str
    deploy_location: Optional[str]
    supported_task_types: List[str]
    cost_per_call: float
    avg_latency_ms: Optional[int]
    status: str
    max_pool_size: Optional[int]
    min_ram_gb: Optional[float]
    version: Optional[str]


@router.get("", response_model=ApiResponse[List[ModelResponse]])
async def list_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_type: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """获取模型列表，支持按任务类型和状态过滤"""
    query = select(ModelRegistry).order_by(ModelRegistry.cost_per_call)

    if status_filter:
        query = query.where(ModelRegistry.status == status_filter)

    result = await db.execute(query)
    models = result.scalars().all()

    # 按任务类型过滤（JSONB 包含）
    if task_type:
        models = [m for m in models if task_type in (m.supported_task_types or [])]

    return ok([_model_to_response(m) for m in models])


@router.post("", response_model=ApiResponse[ModelResponse], status_code=201)
async def create_model(
    request: ModelCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """注册新模型（仅管理员）"""
    existing = await db.execute(
        select(ModelRegistry).where(ModelRegistry.model_name == request.model_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="模型名称已存在")

    model = ModelRegistry(
        model_name=request.model_name,
        model_type=request.model_type,
        deploy_location=request.deploy_location,
        supported_task_types=request.supported_task_types,
        cost_per_call=request.cost_per_call,
        avg_latency_ms=request.avg_latency_ms,
        status=request.status,
        max_pool_size=request.max_pool_size,
        min_ram_gb=request.min_ram_gb,
        version=request.version,
    )
    db.add(model)
    await db.flush()

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="create_model",
        target_type="model",
        target_id=model.id,
        new_value={"model_name": model.model_name, "model_type": model.model_type},
    ))
    await db.flush()

    return ok(_model_to_response(model), message="模型已注册")


@router.put("/{model_id}", response_model=ApiResponse[ModelResponse])
async def update_model(
    model_id: str,
    request: ModelUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """更新模型配置（仅管理员）——变更通过 NATS 热推送"""
    result = await db.execute(select(ModelRegistry).where(ModelRegistry.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")

    old_cost = model.cost_per_call
    if request.model_type is not None:
        model.model_type = request.model_type
    if request.deploy_location is not None:
        model.deploy_location = request.deploy_location
    if request.supported_task_types is not None:
        model.supported_task_types = request.supported_task_types
    if request.cost_per_call is not None:
        model.cost_per_call = request.cost_per_call
    if request.avg_latency_ms is not None:
        model.avg_latency_ms = request.avg_latency_ms
    if request.status is not None:
        model.status = request.status
    if request.max_pool_size is not None:
        model.max_pool_size = request.max_pool_size
    if request.min_ram_gb is not None:
        model.min_ram_gb = request.min_ram_gb
    if request.version is not None:
        model.version = request.version

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action_type="update_model",
        target_type="model",
        target_id=model.id,
        old_value={"cost_per_call": old_cost},
        new_value={"cost_per_call": model.cost_per_call, "status": model.status},
    ))
    await db.flush()

    # 热推送到所有 Agent
    await publish_config_change("model_registry", {
        "event": "model_updated",
        "model_name": model.model_name,
        "cost_per_call": model.cost_per_call,
        "status": model.status,
    })

    return ok(_model_to_response(model), message="模型已更新")


def _model_to_response(model: ModelRegistry) -> ModelResponse:
    return ModelResponse(
        id=model.id,
        model_name=model.model_name,
        model_type=model.model_type,
        deploy_location=model.deploy_location,
        supported_task_types=model.supported_task_types or [],
        cost_per_call=model.cost_per_call or 0.0,
        avg_latency_ms=model.avg_latency_ms,
        status=model.status,
        max_pool_size=model.max_pool_size,
        min_ram_gb=model.min_ram_gb,
        version=model.version,
    )
