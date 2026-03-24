from datetime import datetime

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    health: str
    request_total: int
    processing: int
    completed: int
    failed: int
    snapshot_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    time: datetime


class MetricsResponse(BaseModel):
    request_total: int
    processing: int
    completed: int
    failed: int


class TrendItem(BaseModel):
    timestamp: str
    request_total: int
    processing: int
    completed: int
    failed: int = 0


class RecentTaskItem(BaseModel):
    task_id: str
    url: str
    status: str
    agent_tag: str
    created_at: datetime
    updated_at: datetime


class DashboardPayloadResponse(BaseModel):
    stats: DashboardStatsResponse
    trend: list[TrendItem]
    tasks: list[RecentTaskItem]
