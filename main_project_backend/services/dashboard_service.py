from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.auto_reverse_task import AutoReverseTask
from models.dashboard_snapshot import DashboardSnapshot
from models.task_url_item import TaskUrlItem


TERMINAL_SUCCESS = {"success", "completed"}
TERMINAL_FAILED = {"failed", "error"}
TREND_POINT_LIMIT = 12
RECENT_TASK_LIMIT = 25


def _normalize_status(value: str | None) -> str:
    return str(value or "").strip().lower()


def _has_stage_progress(statuses: list[str]) -> bool:
    return any(status == "running" or status in TERMINAL_SUCCESS or status in TERMINAL_FAILED for status in statuses)


def _derive_recent_agent_tag(task_status: str | None, items: list[TaskUrlItem]) -> str:
    normalized_task_status = _normalize_status(task_status)
    if normalized_task_status in TERMINAL_SUCCESS or normalized_task_status in TERMINAL_FAILED:
        return "finish"

    analyse_statuses = [_normalize_status(item.analyse_status) for item in items]
    if _has_stage_progress(analyse_statuses):
        return "analyse_agent"

    browser_statuses = [_normalize_status(item.browser_status) for item in items]
    if _has_stage_progress(browser_statuses):
        return "browser_agent"

    return "browser_agent" if items else "unknown"


def _calculate_metrics(db: Session) -> dict[str, int]:
    request_total = db.query(func.count(AutoReverseTask.id)).scalar() or 0
    processing = (
        db.query(func.count(AutoReverseTask.id))
        .filter(AutoReverseTask.status.in_(["pending", "running"]))
        .scalar()
        or 0
    )
    queued = (
        db.query(func.count(TaskUrlItem.id))
        .filter(TaskUrlItem.browser_status == "queued")
        .scalar()
        or 0
    )
    completed = (
        db.query(func.count(AutoReverseTask.id))
        .filter(AutoReverseTask.status == "completed")
        .scalar()
        or 0
    )
    failed = (
        db.query(func.count(AutoReverseTask.id))
        .filter(AutoReverseTask.status.in_(["failed", "error"]))
        .scalar()
        or 0
    )
    return {
        "request_total": int(request_total),
        "processing": int(processing),
        "queued": int(queued),
        "completed": int(completed),
        "failed": int(failed),
    }


def _snapshot_matches(snapshot: DashboardSnapshot, metrics: dict[str, int]) -> bool:
    return (
        snapshot.request_total == metrics["request_total"]
        and snapshot.processing == metrics["processing"]
        and snapshot.queued == metrics["queued"]
        and snapshot.completed == metrics["completed"]
        and snapshot.failed == metrics["failed"]
    )


def _format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def record_dashboard_snapshot(db: Session, *, force: bool = False) -> DashboardSnapshot:
    metrics = _calculate_metrics(db)
    latest = (
        db.query(DashboardSnapshot)
        .order_by(DashboardSnapshot.captured_at.desc(), DashboardSnapshot.id.desc())
        .first()
    )
    if latest is not None and not force and _snapshot_matches(latest, metrics):
        return latest

    snapshot = DashboardSnapshot(
        request_total=metrics["request_total"],
        processing=metrics["processing"],
        queued=metrics["queued"],
        completed=metrics["completed"],
        failed=metrics["failed"],
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_health(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Redis 客户端为异步实现，这里提供轻量健康标记，避免在同步路由中阻塞等待。
    redis_status = "unknown"

    system_status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": system_status,
        "db": db_status,
        "redis": redis_status,
        "time": datetime.now(timezone.utc),
    }


def get_metrics(db: Session) -> dict:
    snapshot = record_dashboard_snapshot(db)
    return {
        "request_total": int(snapshot.request_total or 0),
        "processing": int(snapshot.processing or 0),
        "queued": int(snapshot.queued or 0),
        "completed": int(snapshot.completed or 0),
        "failed": int(snapshot.failed or 0),
    }


def get_trend(db: Session) -> list[dict]:
    record_dashboard_snapshot(db)
    rows = (
        db.query(DashboardSnapshot)
        .order_by(DashboardSnapshot.captured_at.desc(), DashboardSnapshot.id.desc())
        .limit(TREND_POINT_LIMIT)
        .all()
    )
    trend = [
        {
            "timestamp": _format_timestamp(row.captured_at),
            "request_total": int(row.request_total or 0),
            "processing": int(row.processing or 0),
            "queued": int(row.queued or 0),
            "completed": int(row.completed or 0),
            "failed": int(row.failed or 0),
        }
        for row in reversed(rows)
    ]
    return trend


def get_recent_tasks(db: Session) -> list[dict]:
    rows = (
        db.query(AutoReverseTask)
        .order_by(AutoReverseTask.created_at.desc())
        .limit(RECENT_TASK_LIMIT)
        .all()
    )
    payload = []
    for row in rows:
        url = "-"
        try:
            urls = json.loads(row.requested_urls or "[]")
            if isinstance(urls, list) and urls:
                url = str(urls[0])
        except json.JSONDecodeError:
            pass

        items = (
            db.query(TaskUrlItem)
            .filter(TaskUrlItem.task_id == row.id)
            .order_by(TaskUrlItem.url_index.asc(), TaskUrlItem.id.asc())
            .all()
        )
        payload.append(
            {
                "task_id": row.id,
                "url": url,
                "status": row.status,
                "agent_tag": _derive_recent_agent_tag(row.status, items),
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )
    return payload


def get_dashboard_payload(db: Session) -> dict:
    health = get_health(db)
    snapshot = record_dashboard_snapshot(db)
    trend = get_trend(db)
    tasks = get_recent_tasks(db)
    return {
        "stats": {
            "health": health["status"],
            "request_total": int(snapshot.request_total or 0),
            "processing": int(snapshot.processing or 0),
            "queued": int(snapshot.queued or 0),
            "completed": int(snapshot.completed or 0),
            "failed": int(snapshot.failed or 0),
            "snapshot_at": snapshot.captured_at,
        },
        "trend": trend,
        "tasks": tasks,
    }
