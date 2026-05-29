"""agents 表 — 分节点 Agent 注册与心跳状态

PRD V2.2 §6.2：Agent 启动时注册，心跳每 30s 一次（实际心跳写 Redis，状态变更才入库）。
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)  # 绑定的员工
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=True)  # Agent 版本号
    status: Mapped[str] = mapped_column(
        String(24), default="offline", index=True
    )  # online / offline / reconnecting / stale / suspected_failure
    current_concurrency: Mapped[int] = mapped_column(Integer, default=0)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=2)
    cpu_pct: Mapped[float] = mapped_column(Float, nullable=True)
    mem_pct: Mapped[float] = mapped_column(Float, nullable=True)
    gpu_pct: Mapped[float] = mapped_column(Float, nullable=True)
    available_models: Mapped[list] = mapped_column(JSON, nullable=True)  # ["qwen2.5-7b", "deepseek-coder-7b"]
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
