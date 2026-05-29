"""department_model_locks 表 — 部门模型锁定（决策 4：第三级管理员锁）"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DepartmentModelLock(Base):
    __tablename__ = "department_model_locks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 任务类型
    locked_model: Mapped[str] = mapped_column(String(128), nullable=False)
    locked_by: Mapped[str] = mapped_column(String(36), nullable=False)  # admin/dept_head user_id
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
