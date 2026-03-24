from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class TaskUrlItem(Base):
    __tablename__ = "task_url_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("auto_reverse_tasks.id"), nullable=False, index=True
    )
    url_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    browser_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    browser_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    browser_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    browser_tool_calls: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyse_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    analyse_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyse_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analyse_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analyse_tool_calls: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
