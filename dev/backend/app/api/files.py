"""文件上传 API — MinIO 直传 + SHA256 校验

PRD V2.2 §6.4：单文件 50MB，类型白名单，上传前客户端计算 SHA256。
"""
import hashlib
import io
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.response import ApiResponse, ok
from app.core.minio_client import get_minio, ensure_bucket, get_object_name, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE_BYTES
from app.models.user import User

router = APIRouter(prefix="/api/v1/files", tags=["文件上传"])

ALLOWED_EXTENSIONS = {".md", ".json", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".mp4"}


class UploadResponse(BaseModel):
    file_url: str
    file_hash: str
    filename: str
    size_bytes: int
    content_type: str


@router.post("/upload", response_model=ApiResponse[UploadResponse])
async def upload_file(
    task_id: Annotated[str, Form()],
    expected_hash: Annotated[str, Form()],
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """上传任务成果文件到 MinIO

    客户端必须提前计算 SHA256(file_bytes)，服务端校验一致才入库。
    """
    # 文件大小限制
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"文件超过 50MB 限制 (实际: {len(content) // (1024*1024)}MB)")

    # 文件类型白名单（扩展名 + Content-Type）
    import os
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"不支持的文件类型: {ext}，允许: {', '.join(ALLOWED_EXTENSIONS)}")

    # SHA256 校验
    actual_hash = "sha256:" + hashlib.sha256(content).hexdigest()
    normalized_expected = expected_hash if expected_hash.startswith("sha256:") else "sha256:" + expected_hash
    if actual_hash != normalized_expected:
        raise HTTPException(
            status_code=400,
            detail=f"文件完整性校验失败 (expected: {normalized_expected[:20]}..., got: {actual_hash[:20]}...)",
        )

    # 上传到 MinIO
    bucket = ensure_bucket(current_user.department_id)
    object_name = get_object_name(current_user.department_id, task_id, file.filename or "result")

    client = get_minio()
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(content),
        length=len(content),
        content_type=file.content_type or "application/octet-stream",
    )

    file_url = f"minio://{bucket}/{object_name}"

    return ok(UploadResponse(
        file_url=file_url,
        file_hash=actual_hash,
        filename=file.filename or "result",
        size_bytes=len(content),
        content_type=file.content_type or "application/octet-stream",
    ), message="文件上传成功")
