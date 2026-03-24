from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class AppConfig(Base):
    __tablename__ = "app_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    browser_mode: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    mcp_tools: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_profiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_generator: Mapped[str | None] = mapped_column(Text, nullable=True)
    debug_mode_isolation_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    standalone_browser: Mapped[str | None] = mapped_column(Text, nullable=True)
    standalone_executable_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_agent_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    standalone_browser_agent_system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    standalone_browser_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyse_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
