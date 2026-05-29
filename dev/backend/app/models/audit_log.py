"""audit_logs 表 — 审计日志"""
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(16), nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # create_task / claim_task / submit_task / override_model / lock_model / admin_switch
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)  # task / model / department / agent
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    old_value: Mapped[dict] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
