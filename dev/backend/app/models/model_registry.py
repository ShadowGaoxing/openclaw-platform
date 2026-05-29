"""model_registry 表 — 模型注册表"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    model_type: Mapped[str] = mapped_column(String(16), nullable=False)  # local / api
    deploy_location: Mapped[str] = mapped_column(String(64), nullable=True)  # main / dept_A / dept_B
    supported_task_types: Mapped[dict] = mapped_column(JSON, nullable=False)  # ["代码审查", "文档摘要", ...]
    cost_per_call: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    avg_latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="online")  # online / offline / degraded
    max_pool_size: Mapped[int] = mapped_column(Integer, nullable=True)
    min_ram_gb: Mapped[float] = mapped_column(Float, nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
