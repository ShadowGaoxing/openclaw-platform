"""MinIO 客户端 — 对象存储，按部门 bucket 隔离"""
from typing import Optional
from minio import Minio
from minio.error import S3Error
from app.core.config import get_settings

_minio_client: Optional[Minio] = None

# 允许上传的文件类型白名单（PRD §6.4）
ALLOWED_CONTENT_TYPES = {
    "text/markdown",
    "application/json",
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "video/mp4",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


def get_minio() -> Minio:
    global _minio_client
    if _minio_client is None:
        settings = get_settings()
        _minio_client = Minio(
            endpoint=f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,  # 内网 HTTP，Nginx 层做 TLS
        )
    return _minio_client


def ensure_bucket(department_id: str) -> str:
    """确保部门 bucket 存在，返回 bucket 名称"""
    bucket_name = "openclaw"
    client = get_minio()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    return bucket_name


def get_object_name(department_id: str, task_id: str, filename: str) -> str:
    """生成隔离路径：bucket/{dept_id}/{task_id}/{filename}"""
    return f"{department_id}/{task_id}/{filename}"
