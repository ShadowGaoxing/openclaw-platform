"""统一响应格式 — 所有 API 共用包装，附带 request_id 便于追踪"""
import uuid
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """标准 API 响应包装

    遵循 PRD V2.2 §8：所有接口返回值包含 request_id。
    """

    status: str = "ok"
    data: Optional[T] = None
    message: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_code: Optional[str] = None


def ok(data: T = None, message: str = "") -> ApiResponse[T]:
    return ApiResponse[T](status="ok", data=data, message=message or None)


def fail(error_code: str, message: str, status: str = "error") -> ApiResponse:
    return ApiResponse(status=status, error_code=error_code, message=message)
