from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class AutoReverseTask(Base):
    __tablename__ = "auto_reverse_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    browser_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    headless: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    max_concurrent: Mapped[int | None] = mapped_column(nullable=True)
    debug_mode_isolation_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    requested_urls: Mapped[str] = mapped_column(Text, nullable=False)
    requested_mcp_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_models: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_agent_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyse_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
