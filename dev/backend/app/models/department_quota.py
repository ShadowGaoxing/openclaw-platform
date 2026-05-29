"""department_quotas 表 — 部门配额"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DepartmentQuota(Base):
    __tablename__ = "department_quotas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, default=10)
    max_daily_api_budget: Mapped[float] = mapped_column(Float, nullable=True)  # ¥
    max_daily_upload_mb: Mapped[int] = mapped_column(Integer, default=500)
    max_user_rate: Mapped[int] = mapped_column(Integer, default=5)  # 用户级软限流
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
