"""shared_results 表 — 成果共享"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SharedResult(Base):
    __tablename__ = "shared_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    source_department_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_department_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    target_user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(16), default="pending")  # pending / approved / rejected
    approved_by: Mapped[str] = mapped_column(String(36), nullable=True)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    output_format: Mapped[str] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
