from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.dashboard import (
    DashboardPayloadResponse,
    HealthResponse,
    MetricsResponse,
    RecentTaskItem,
    TrendItem,
)
from services import dashboard_service


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/health", response_model=HealthResponse)
def health_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> HealthResponse:
    return HealthResponse(**dashboard_service.get_health(db))


@router.get("/payload", response_model=DashboardPayloadResponse)
def payload_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardPayloadResponse:
    return DashboardPayloadResponse(**dashboard_service.get_dashboard_payload(db))


@router.get("/metrics", response_model=MetricsResponse)
def metrics_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MetricsResponse:
    return MetricsResponse(**dashboard_service.get_metrics(db))


@router.get("/trend", response_model=list[TrendItem])
def trend_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TrendItem]:
    return [TrendItem(**item) for item in dashboard_service.get_trend(db)]


@router.get("/recent-tasks", response_model=list[RecentTaskItem])
def recent_tasks_api(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RecentTaskItem]:
    return [RecentTaskItem(**item) for item in dashboard_service.get_recent_tasks(db)]
