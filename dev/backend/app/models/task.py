"""tasks 表 — 核心任务表"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    assignee_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1=紧急, 2=高, 3=普通, 4=低
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending / claimed / assigned_auto / processing / completed / failed / dead / suspected
    assignment_strategy: Mapped[str] = mapped_column(String(8), default="manual")  # manual / auto / hybrid
    recommended_model: Mapped[str] = mapped_column(String(64), nullable=True)
    override_model: Mapped[str] = mapped_column(String(64), nullable=True)
    cache_key: Mapped[str] = mapped_column(String(128), nullable=True)
    result_url: Mapped[str] = mapped_column(String(512), nullable=True)
    output_format: Mapped[str] = mapped_column(String(16), nullable=True)  # json / markdown / text / image
    progress_seq: Mapped[int] = mapped_column(Integer, default=0)  # 进度上报幂等 Key
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), nullable=True)
    created_by_role: Mapped[str] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_timeout_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    inactivity_timeout_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    suspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
