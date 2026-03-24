from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queued: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
