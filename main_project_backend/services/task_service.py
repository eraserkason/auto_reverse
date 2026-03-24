from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.callbacks.base import AsyncCallbackHandler
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import redis as redis_sync
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from agents.analysis_agent import run_analysis_agent
from agents.browser_agent import BrowserAgentResult, run_browser_agent
from config import MAX_CONCURRENT_BROWSERS, REDIS_URL
from db.session import SessionLocal
from models.analysis_result import AnalysisResult
from models.auto_reverse_task import AutoReverseTask
from models.success_result_archive import SuccessResultArchive
from models.task_stage import TaskStage
from models.task_url_item import TaskUrlItem
from prompts.playwright_standalone import PLAYWRIGHT_STANDALONE_BROWSER_AGENT_SYSTEM_PROMPT
from services import config_service, dashboard_service
from tools.mcp_tool import list_available_servers
from tools.redis_tool import get_analysis_tools
from tools.official_skills_runtime import official_skills_runtime
from tools.skill_registry import SkillRegistry
from tools.tool_registry import ToolRegistry
from utils.redis_client import (
    get_client,
    session_log_key,
    session_meta_key,
    session_network_key,
    sessions_set_key,
)


_running_tasks: set[str] = set()
_task_session_claims: dict[str, set[str]] = {}
_session_claim_lock = asyncio.Lock()
_runtime_loop: asyncio.AbstractEventLoop | None = None


@dataclass
class _PreservedBrowserRuntimeLease:
    release_event: asyncio.Event
    closed_future: asyncio.Future[None]


@dataclass(frozen=True)
class _BrowserCompletionGate:
    require_real_input: bool = False
    require_submit_attempt: bool = False
    require_post_submit_confirmation: bool = False
    keep_browser_open_on_incomplete: bool = False
    source: str = "none"

    @property
    def enabled(self) -> bool:
        return any(
            (
                self.require_real_input,
                self.require_submit_attempt,
                self.require_post_submit_confirmation,
            )
        )


_preserved_browser_runtimes: dict[tuple[str, int], _PreservedBrowserRuntimeLease] = {}
_preserved_browser_runtime_cleanup_tasks: dict[tuple[str, int], asyncio.Task[None]] = {}
TERMINAL_SUCCESS = {"success", "completed"}
TERMINAL_FAILED = {"failed", "error"}
AGENT_KEYS = ("browser_agent", "analyse_agent")
BROWSER_AGENT_FAILURE_PRESERVED_CLOSE_DELAY_SECONDS = 30.0
BROWSER_AGENT_STANDALONE_PRESERVED_CLOSE_DELAY_SECONDS = 300.0
SESSION_CLAIM_TIMEOUT_SECONDS = 8.0
SESSION_CLAIM_POLL_INTERVAL_SECONDS = 0.5
SESSION_CLAIM_GRACE_MS = 5_000
SESSION_SEAL_TIMEOUT_SECONDS = 10.0
SESSION_SEAL_POLL_INTERVAL_SECONDS = 0.25
RECENT_TASK_BATCH_LIMIT = 10
URL_FRAGMENT_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
SNAPSHOT_URL_PATTERN = re.compile(r"/url:\s*([^\s\"'<>]+)")
_COMPLETION_GATE_BLOCK_PATTERN = re.compile(
    r"\[AUTO_REVERSE_COMPLETION_GATE\](.*?)\[/AUTO_REVERSE_COMPLETION_GATE\]",
    re.IGNORECASE | re.DOTALL,
)
_COMPLETION_GATE_TRUE_VALUES = {"1", "true", "yes", "on"}
_POST_SUBMIT_CONFIRM_TOOLS = {"browser_snapshot", "browser_console_messages"}
_REAL_INPUT_TOOLS = {"browser_type", "browser_fill_form"}


def _parse_completion_gate_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in _COMPLETION_GATE_TRUE_VALUES


def _parse_browser_completion_gate(prompt: str | None) -> _BrowserCompletionGate | None:
    text = str(prompt or "").strip()
    if not text:
        return None

    match = _COMPLETION_GATE_BLOCK_PATTERN.search(text)
    if match is None:
        return None

    values: dict[str, bool] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        normalized_key = str(key or "").strip().lower()
        if not normalized_key:
            continue
        values[normalized_key] = _parse_completion_gate_bool(raw_value)

    return _BrowserCompletionGate(
        require_real_input=values.get("require_real_input", False),
        require_submit_attempt=values.get("require_submit_attempt", False),
        require_post_submit_confirmation=values.get("require_post_submit_confirmation", False),
        keep_browser_open_on_incomplete=values.get("keep_browser_open_on_incomplete", False),
        source="prompt_contract",
    )


def _infer_legacy_browser_completion_gate(prompt: str | None) -> _BrowserCompletionGate | None:
    text = str(prompt or "").strip()
    if not text:
        return None

    lower = text.lower()
    has_payment_intent = any(
        marker in text
        for marker in (
            "真实支付/捐赠表单测试",
            "真实支付 / 捐赠表单测试",
            "真实支付",
            "真实提交",
        )
    )
    has_input_expectation = any(
        marker in lower
        for marker in (
            "card number",
            "security code",
            "expiration date",
            "cvv",
        )
    )
    has_post_submit_confirmation = "提交后" in text and any(
        marker in lower
        for marker in (
            "browser_snapshot",
            "browser_console_messages",
            "console",
        )
    )
    if not (has_payment_intent and has_input_expectation and has_post_submit_confirmation):
        return None

    return _BrowserCompletionGate(
        require_real_input=True,
        require_submit_attempt=True,
        require_post_submit_confirmation=True,
        keep_browser_open_on_incomplete=True,
        source="legacy_payment_prompt",
    )


def _resolve_browser_completion_gate(prompt: str | None) -> _BrowserCompletionGate | None:
    parsed = _parse_browser_completion_gate(prompt)
    if parsed is not None and parsed.enabled:
        return parsed
    return _infer_legacy_browser_completion_gate(prompt)


def _format_browser_tool_trace(completed_tool_sequence: tuple[str, ...] | list[str]) -> str:
    normalized = [str(name or "").strip() for name in completed_tool_sequence]
    normalized = [name for name in normalized if name]
    if not normalized:
        return "无"
    return " -> ".join(normalized)


def _evaluate_browser_completion_gate(
    gate: _BrowserCompletionGate | None,
    completed_tool_sequence: tuple[str, ...] | list[str],
) -> str | None:
    if gate is None or not gate.enabled:
        return None

    sequence = [str(name or "").strip() for name in completed_tool_sequence]
    sequence = [name for name in sequence if name]

    first_input_index = next((index for index, name in enumerate(sequence) if name in _REAL_INPUT_TOOLS), None)
    if gate.require_real_input and first_input_index is None:
        return "未进入真实输入阶段（缺少 browser_type 或 browser_fill_form）"

    submit_index: int | None = None
    if gate.require_submit_attempt:
        search_after = first_input_index if first_input_index is not None else -1
        submit_index = next(
            (index for index, name in enumerate(sequence) if index > search_after and name == "browser_click"),
            None,
        )
        if submit_index is None:
            return "未发生真实提交尝试（缺少输入后的 browser_click）"

    if gate.require_post_submit_confirmation:
        search_after = submit_index if submit_index is not None else (first_input_index if first_input_index is not None else -1)
        has_post_submit_confirmation = any(
            index > search_after and name in _POST_SUBMIT_CONFIRM_TOOLS
            for index, name in enumerate(sequence)
        )
        if not has_post_submit_confirmation:
            return "缺少提交后终态确认（缺少提交后的 browser_snapshot 或 browser_console_messages）"

    return None


def _apply_browser_completion_gate(
    result: BrowserAgentResult,
    *,
    browser_prompt: str | None,
    completed_tool_sequence: tuple[str, ...] | list[str],
) -> BrowserAgentResult:
    gate = _resolve_browser_completion_gate(browser_prompt)
    if gate is None or not gate.enabled or not bool(getattr(result, "success", False)):
        return result

    failure_reason = _evaluate_browser_completion_gate(gate, completed_tool_sequence)
    if not failure_reason:
        return result

    detail = (
        f"browser_agent 提前结束：{failure_reason}（gate={gate.source}）；"
        f"工具轨迹={_format_browser_tool_trace(completed_tool_sequence)}"
    )
    if gate.keep_browser_open_on_incomplete:
        detail = f"{detail}；已按未完成任务保留浏览器现场"
    result.success = False
    result.error = detail
    return result


def _preserved_browser_runtime_key(task_id: str, item_id: int) -> tuple[str, int]:
    return (str(task_id), int(item_id))


def _create_preserved_browser_runtime_lease() -> _PreservedBrowserRuntimeLease:
    loop = asyncio.get_running_loop()
    return _PreservedBrowserRuntimeLease(
        release_event=asyncio.Event(),
        closed_future=loop.create_future(),
    )


def _should_preserve_standalone_browser_runtime(
    *,
    headless: bool,
    success: bool,
    latest_tool: str,
) -> bool:
    if headless or success:
        return False
    return latest_tool != "browser_close"


def _consume_background_task_exception(task: asyncio.Task[Any], *, label: str) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        return
    except Exception as exc:
        print(f"[TaskService] 警告：{label} 异常退出 — {exc}")


def _cancel_preserved_browser_runtime_cleanup(task_id: str, item_id: int) -> None:
    cleanup_task = _preserved_browser_runtime_cleanup_tasks.pop(
        _preserved_browser_runtime_key(task_id, item_id),
        None,
    )
    if cleanup_task is not None and not cleanup_task.done():
        cleanup_task.cancel()


async def _close_preserved_browser_runtime_after_delay(
    task_id: str,
    item_id: int,
    *,
    delay_seconds: float,
) -> None:
    key = _preserved_browser_runtime_key(task_id, item_id)
    current_cleanup_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay_seconds)
        if _preserved_browser_runtime_cleanup_tasks.get(key) is not current_cleanup_task:
            return
        _preserved_browser_runtime_cleanup_tasks.pop(key, None)
        await _release_preserved_browser_runtime(task_id, item_id)
    finally:
        if _preserved_browser_runtime_cleanup_tasks.get(key) is current_cleanup_task:
            _preserved_browser_runtime_cleanup_tasks.pop(key, None)


def _schedule_preserved_browser_runtime_cleanup(
    task_id: str,
    item_id: int,
    *,
    delay_seconds: float = BROWSER_AGENT_FAILURE_PRESERVED_CLOSE_DELAY_SECONDS,
) -> None:
    _cancel_preserved_browser_runtime_cleanup(task_id, item_id)
    key = _preserved_browser_runtime_key(task_id, item_id)
    _preserved_browser_runtime_cleanup_tasks[key] = asyncio.create_task(
        _close_preserved_browser_runtime_after_delay(
            task_id,
            item_id,
            delay_seconds=delay_seconds,
        )
    )


async def _release_preserved_browser_runtime(task_id: str, item_id: int) -> None:
    key = _preserved_browser_runtime_key(task_id, item_id)
    _cancel_preserved_browser_runtime_cleanup(task_id, item_id)
    lease = _preserved_browser_runtimes.pop(key, None)
    if lease is None:
        return
    if not lease.release_event.is_set():
        lease.release_event.set()
    await asyncio.shield(lease.closed_future)


def bind_runtime_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    global _runtime_loop
    _runtime_loop = loop


class _TaskItemToolCallbackHandler(AsyncCallbackHandler):
    def __init__(
        self,
        *,
        task_id: str,
        item_id: int,
        agent_tag: str,
        allowed_tool_names: set[str],
    ) -> None:
        super().__init__()
        self._task_id = task_id
        self._item_id = item_id
        self._agent_tag = agent_tag
        self._allowed_tool_names = {name for name in allowed_tool_names if name}
        self._active_tool_name_by_run: dict[str, str] = {}
        self._fallback_tool_name: str | None = None
        self._latest_tool_name: str | None = None
        self._completed_tool_sequence: list[str] = []

    def _normalize_tool_name(self, serialized: dict[str, Any] | None = None) -> str:
        data = serialized or {}
        name = str(data.get("name") or data.get("id") or "").strip()
        if not name or name not in self._allowed_tool_names:
            return ""
        return name

    def _consume_tool_name(self, run_id: Any) -> str:
        key = str(run_id) if run_id is not None else ""
        if key and key in self._active_tool_name_by_run:
            return self._active_tool_name_by_run.pop(key)
        name = self._fallback_tool_name or ""
        self._fallback_tool_name = None
        return name if name in self._allowed_tool_names else ""

    async def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        name = self._normalize_tool_name(serialized)
        if not name:
            return
        run_id = kwargs.get("run_id")
        key = str(run_id) if run_id is not None else ""
        if key:
            self._active_tool_name_by_run[key] = name
        self._fallback_tool_name = name
        self._latest_tool_name = name
        _record_item_tool_event(self._task_id, self._item_id, self._agent_tag, name, "running")

    async def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        name = self._consume_tool_name(kwargs.get("run_id"))
        if not name:
            return
        _record_item_tool_event(self._task_id, self._item_id, self._agent_tag, name, "completed")
        self._completed_tool_sequence.append(name)
        self._latest_tool_name = ""

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        name = self._consume_tool_name(kwargs.get("run_id"))
        if not name:
            return
        _record_item_tool_event(self._task_id, self._item_id, self._agent_tag, name, "failed")

    def get_latest_tool_name(self) -> str:
        return str(self._latest_tool_name or "").strip()

    def get_completed_tool_sequence(self) -> tuple[str, ...]:
        return tuple(self._completed_tool_sequence)

    def clear_latest_tool_name(self) -> None:
        self._latest_tool_name = ""


def _intersect_keep_order(selected: list[str], allowed: list[str]) -> list[str]:
    allowed_set = set(allowed)
    return [item for item in selected if item in allowed_set]


def _normalize_agent_selection(
    *,
    selected_mcp_tools: list[str],
    selected_skills: list[str],
    selected_model_provider: str,
    selected_model_name: str,
    selected_model_profile_key: str,
    allowed_mcp_tools: list[str],
    allowed_skills: list[str],
    force_required_mcp: bool,
    browser_mode: str | None = None,
    excluded_mcp_tools: list[str] | None = None,
) -> dict[str, list[str] | str]:
    normalized_allowed_mcp = config_service.normalize_agent_mcp_tools(
        allowed_mcp_tools,
        include_required=False,
    )
    excluded_mcp_set = {str(item).strip() for item in (excluded_mcp_tools or []) if str(item).strip()}
    requested_mcp = _intersect_keep_order(selected_mcp_tools, normalized_allowed_mcp)
    if excluded_mcp_set:
        requested_mcp = [item for item in requested_mcp if item not in excluded_mcp_set]
    normalized_mcp = config_service.normalize_agent_mcp_tools(
        requested_mcp,
        include_required=force_required_mcp,
        browser_mode=browser_mode,
    )
    normalized_skills = config_service.normalize_skills(
        _intersect_keep_order(selected_skills, config_service.normalize_skills(allowed_skills))
    )
    return {
        "mcp_tools": normalized_mcp,
        "skills": normalized_skills,
        "model_provider": str(selected_model_provider or "").strip(),
        "model_name": str(selected_model_name or "").strip(),
        "model_profile_key": str(selected_model_profile_key or "").strip(),
    }

def _load_requested_mapping(raw: str | None) -> dict[str, list[str]]:
    default_mapping = {key: [] for key in AGENT_KEYS}
    if not raw:
        return default_mapping
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return default_mapping

    if isinstance(data, list):
        normalized = [str(item) for item in data]
        return {key: normalized[:] for key in AGENT_KEYS}

    if not isinstance(data, dict):
        return default_mapping

    result: dict[str, list[str]] = {}
    for key in AGENT_KEYS:
        value = data.get(key, [])
        result[key] = [str(item) for item in value] if isinstance(value, list) else []
    return result


def _load_requested_profiles(raw: str | None) -> dict[str, dict]:
    default_mapping = {key: {} for key in AGENT_KEYS}
    if not raw:
        return default_mapping
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return default_mapping
    if not isinstance(data, dict):
        return default_mapping
    result: dict[str, dict] = {}
    for key in AGENT_KEYS:
        value = data.get(key) or {}
        result[key] = value if isinstance(value, dict) else {}
    return result


def _tool_call_field_name(agent_tag: str) -> str:
    return "browser_tool_calls" if agent_tag == "browser_agent" else "analyse_tool_calls"


def _load_tool_call_entries(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []

    entries: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        status = str(item.get("status") or "completed").strip() or "completed"
        try:
            count = max(1, int(item.get("count") or 1))
        except (TypeError, ValueError):
            count = 1
        updated_at = str(item.get("updated_at") or "").strip()
        entries.append({"name": name, "status": status, "count": count, "updated_at": updated_at})
    return entries


def _dump_tool_call_entries(entries: list[dict[str, Any]]) -> str:
    return json.dumps(entries, ensure_ascii=False)


def _sort_tool_call_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"running": 0, "failed": 1, "completed": 2}
    return sorted(
        entries,
        key=lambda item: (
            priority.get(str(item.get("status") or "").strip(), 3),
            str(item.get("updated_at") or ""),
            str(item.get("name") or ""),
        ),
        reverse=False,
    )


def _update_tool_call_payload(raw: str | None, *, tool_name: str, status: str) -> str:
    normalized_name = str(tool_name or "").strip()
    if not normalized_name:
        return raw or _dump_tool_call_entries([])

    entries = _load_tool_call_entries(raw)
    now = datetime.now(timezone.utc).isoformat()
    current = next((item for item in entries if item.get("name") == normalized_name), None)
    if current is None:
        current = {"name": normalized_name, "status": status, "count": 0, "updated_at": now}
        entries.append(current)

    if status == "running":
        current["count"] = max(1, int(current.get("count") or 0) + 1)
    else:
        current["count"] = max(1, int(current.get("count") or 0))
    current["status"] = status
    current["updated_at"] = now
    return _dump_tool_call_entries(_sort_tool_call_entries(entries))


def _serialize_tool_call_entries(raw: str | None) -> list[dict[str, Any]]:
    entries = _sort_tool_call_entries(_load_tool_call_entries(raw))
    return [
        {
            "name": str(item.get("name") or "").strip(),
            "status": str(item.get("status") or "completed").strip() or "completed",
            "count": max(1, int(item.get("count") or 1)),
        }
        for item in entries
        if str(item.get("name") or "").strip()
    ]


def _record_item_tool_event(task_id: str, item_id: int, agent_tag: str, tool_name: str, status: str) -> None:
    normalized_name = str(tool_name or "").strip()
    if not normalized_name:
        return

    db = SessionLocal()
    try:
        row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
        if row is None:
            return
        field_name = _tool_call_field_name(agent_tag)
        current_payload = getattr(row, field_name)
        setattr(row, field_name, _update_tool_call_payload(current_payload, tool_name=normalized_name, status=status))
        db.commit()
    finally:
        db.close()


def _resolve_runtime_server_names(requested_mcp_tools: list[str], *, browser_mode: str | None = None) -> list[str]:
    available = set(list_available_servers())
    if not requested_mcp_tools:
        return []

    resolved: list[str] = []
    for name in requested_mcp_tools:
        candidates = config_service.resolve_runtime_server_candidates(name, browser_mode=browser_mode)
        for candidate in candidates:
            if candidate in available and candidate not in resolved:
                resolved.append(candidate)
    return resolved


def _load_skill_tools(skill_registry: SkillRegistry, requested_skills: list[str]) -> list:
    if not requested_skills:
        return []
    try:
        return skill_registry.get_skills(requested_skills)
    except KeyError:
        return []


def _summarize_step(statuses: list[str]) -> dict:
    total = len(statuses)
    skipped = sum(1 for status_value in statuses if status_value == "skipped")
    counts = {
        "total": total,
        "pending": sum(1 for status_value in statuses if status_value == "pending"),
        "queued": sum(1 for status_value in statuses if status_value == "queued"),
        "running": sum(1 for status_value in statuses if status_value == "running"),
        "success": sum(1 for status_value in statuses if status_value in TERMINAL_SUCCESS),
        "failed": sum(1 for status_value in statuses if status_value in TERMINAL_FAILED),
        "skipped": skipped,
    }

    if total == 0:
        summary_status = "pending"
    elif counts["success"] + counts["skipped"] == total:
        summary_status = "success"
    elif counts["failed"] + counts["success"] + counts["skipped"] == total and counts["failed"] > 0:
        summary_status = "failed"
    elif counts["running"] > 0 or counts["queued"] > 0 or counts["success"] > 0 or counts["failed"] > 0 or counts["skipped"] > 0:
        summary_status = "running"
    else:
        summary_status = "pending"

    return {"status": summary_status, **counts}


def _serialize_task_item(row: TaskUrlItem) -> dict:
    return {
        "url": row.url,
        "url_index": row.url_index,
        "session_id": row.session_id,
        "browser_stage": {
            "status": row.browser_status,
            "message": row.browser_message,
            "started_at": row.browser_started_at,
            "completed_at": row.browser_completed_at,
        },
        "analyse_stage": {
            "status": row.analyse_status,
            "message": row.analyse_message,
            "started_at": row.analyse_started_at,
            "completed_at": row.analyse_completed_at,
        },
        "final_status": row.final_status,
        "error": row.error,
        "report_text": row.report_text,
        "browser_tools": _serialize_tool_call_entries(row.browser_tool_calls),
        "analyse_tools": _serialize_tool_call_entries(row.analyse_tool_calls),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _build_task_steps(rows: list[TaskUrlItem]) -> list[dict]:
    browser_summary = _summarize_step([row.browser_status for row in rows])
    analyse_summary = _summarize_step([row.analyse_status for row in rows])
    finish_summary = _summarize_step([row.final_status for row in rows])
    return [
        {"key": "browser_agent", **browser_summary},
        {"key": "analyse_agent", **analyse_summary},
        {"key": "finish", **finish_summary},
    ]


def _normalize_status_text(value: str | None) -> str:
    return str(value or "").strip().lower()


def _is_terminal_task_status(value: str | None) -> bool:
    normalized = _normalize_status_text(value)
    if not normalized:
        return False
    return any(keyword in normalized for keyword in ("success", "complete", "fail", "error"))


def _delete_task_records(db: Session, task_id: str) -> None:
    db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id).delete(synchronize_session=False)
    db.query(TaskStage).filter(TaskStage.task_id == task_id).delete(synchronize_session=False)
    db.query(AutoReverseTask).filter(AutoReverseTask.id == task_id).delete(synchronize_session=False)
    _running_tasks.discard(task_id)


def _collect_session_ids_for_tasks(db: Session, task_ids: list[str]) -> list[str]:
    if not task_ids:
        return []

    rows = (
        db.query(TaskUrlItem.session_id)
        .filter(TaskUrlItem.task_id.in_(task_ids), TaskUrlItem.session_id.isnot(None))
        .all()
    )
    session_ids: list[str] = []
    seen: set[str] = set()
    for (session_id,) in rows:
        if not session_id or session_id in seen:
            continue
        seen.add(session_id)
        session_ids.append(session_id)
    return session_ids


def _collect_orphan_session_ids_for_tasks(db: Session, task_ids: list[str]) -> list[str]:
    candidate_session_ids = _collect_session_ids_for_tasks(db, task_ids)
    if not candidate_session_ids:
        return []

    referenced_rows = (
        db.query(TaskUrlItem.session_id)
        .filter(
            ~TaskUrlItem.task_id.in_(task_ids),
            TaskUrlItem.session_id.in_(candidate_session_ids),
            TaskUrlItem.session_id.isnot(None),
        )
        .distinct()
        .all()
    )
    referenced_session_ids = {session_id for (session_id,) in referenced_rows if session_id}
    return [session_id for session_id in candidate_session_ids if session_id not in referenced_session_ids]


def _delete_redis_sessions(session_ids: list[str]) -> list[str]:
    normalized_session_ids: list[str] = []
    seen: set[str] = set()
    for session_id in session_ids:
        normalized = str(session_id or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_session_ids.append(normalized)

    if not normalized_session_ids:
        return []

    client = redis_sync.Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        pipeline = client.pipeline(transaction=False)
        sessions_key = sessions_set_key()
        for session_id in normalized_session_ids:
            index_keys = list(client.scan_iter(match=f"{session_network_key(session_id)}:index*"))
            pipeline.srem(sessions_key, session_id)
            pipeline.delete(
                session_meta_key(session_id),
                session_log_key(session_id),
                session_network_key(session_id),
            )
            if index_keys:
                pipeline.delete(*index_keys)
        pipeline.execute()
    finally:
        client.close()

    return normalized_session_ids


def _seed_browser_queue_states(
    db: Session,
    rows: list[TaskUrlItem],
    *,
    effective_concurrent: int,
) -> None:
    concurrency_limit = max(1, effective_concurrent)
    changed = False
    for index, row in enumerate(rows):
        next_status = "pending" if index < concurrency_limit else "queued"
        next_message = None if next_status == "pending" else "等待并发槽位"
        if row.browser_status != next_status:
            row.browser_status = next_status
            changed = True
        if row.browser_message != next_message:
            row.browser_message = next_message
            changed = True
    if changed:
        db.commit()


def _set_item_browser_state(
    db: Session,
    row: TaskUrlItem,
    *,
    status_text: str,
    message: str | None = None,
    session_id: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    now = datetime.now(timezone.utc)
    row.browser_status = status_text
    row.browser_message = message
    if session_id is not None:
        row.session_id = session_id
    if started:
        row.browser_tool_calls = _dump_tool_call_entries([])
        if row.browser_started_at is None:
            row.browser_started_at = now
    if completed:
        row.browser_completed_at = now
    if row.final_status == "pending":
        row.final_status = "running"
    db.commit()


def _set_item_analyse_state(
    db: Session,
    row: TaskUrlItem,
    *,
    status_text: str,
    message: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    now = datetime.now(timezone.utc)
    row.analyse_status = status_text
    row.analyse_message = message
    if started:
        row.analyse_tool_calls = _dump_tool_call_entries([])
        if row.analyse_started_at is None:
            row.analyse_started_at = now
    if completed:
        row.analyse_completed_at = now
    if row.final_status == "pending":
        row.final_status = "running"
    db.commit()


def _set_item_final_state(
    db: Session,
    row: TaskUrlItem,
    *,
    status_text: str,
    error: str | None = None,
    report_text: str | None = None,
) -> None:
    row.final_status = status_text
    row.error = error
    if report_text is not None:
        row.report_text = report_text
    db.commit()


def _format_failure_message(prefix: str, detail: str | None, *, default_detail: str = "未返回详细错误信息") -> str:
    normalized = str(detail or "").strip() or default_detail
    return f"{prefix}: {normalized}"


async def _list_session_ids() -> set[str]:
    client = get_client()
    raw = await client.smembers(sessions_set_key())
    return set(raw)


async def _read_session_records(session_id: str) -> list[dict]:
    client = get_client()
    entries = await client.xrange(session_log_key(session_id), "-", "+")
    records: list[dict] = []
    for _stream_id, fields in entries:
        data = fields.get("data")
        if not data:
            continue
        try:
            record = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


async def _read_session_network_records(session_id: str) -> list[dict]:
    client = get_client()
    entries = await client.xrange(session_network_key(session_id), "-", "+")
    records: list[dict] = []
    for _stream_id, fields in entries:
        data = fields.get("data")
        if not data:
            continue
        try:
            record = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


async def _read_stream_state(key: str) -> tuple[int, str | None]:
    client = get_client()
    count = await client.xlen(key)
    if count <= 0:
        return 0, None
    latest = await client.xrevrange(key, "+", "-", count=1)
    latest_id = latest[0][0] if latest else None
    return count, latest_id


async def _read_session_meta(session_id: str) -> dict[str, str]:
    client = get_client()
    return {
        str(key): str(value)
        for key, value in (await client.hgetall(session_meta_key(session_id))).items()
    }


async def _session_id_materialized(session_id: str) -> bool:
    normalized = str(session_id or "").strip()
    if not normalized:
        return False

    if normalized in await _list_session_ids():
        return True

    if await _read_session_meta(normalized):
        return True

    log_count, _ = await _read_stream_state(session_log_key(normalized))
    if log_count > 0:
        return True

    network_count, _ = await _read_stream_state(session_network_key(normalized))
    return network_count > 0


async def _wait_for_session_to_seal(session_id: str) -> dict[str, str]:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + SESSION_SEAL_TIMEOUT_SECONDS

    while True:
        meta = await _read_session_meta(session_id)
        status_value = _normalize_status_text(meta.get("status"))
        if status_value == "sealed":
            return meta
        if status_value == "failed":
            detail = meta.get("error") or "browser session 收口失败"
            raise RuntimeError(detail)
        if loop.time() >= deadline:
            raise RuntimeError("等待 browser session sealed 超时")
        await asyncio.sleep(SESSION_SEAL_POLL_INTERVAL_SECONDS)


async def _prepare_session_for_analysis(task_id: str, item_id: int, session_id: str) -> dict[str, str]:
    # Standalone browser mode may preserve the runtime after browser_agent returns.
    # Releasing it here lets dispose() complete and write the final sealed meta
    # before analyse_agent begins consuming the session.
    await _release_preserved_browser_runtime(task_id, item_id)
    return await _wait_for_session_to_seal(session_id)


def _normalize_url_for_match(url: str) -> str:
    candidate = str(url or "").strip()
    if not candidate:
        return ""
    parsed = urlsplit(candidate)
    if not parsed.scheme and not parsed.netloc:
        return candidate.rstrip("/")
    path = parsed.path or "/"
    normalized_path = path.rstrip("/") or "/"
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            parsed.query,
            "",
        )
    )


def _normalize_url_path_for_match(url: str) -> str:
    candidate = str(url or "").strip()
    if not candidate:
        return ""
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        path = parsed.path or "/"
    else:
        path = candidate
    return (path.rstrip("/") or "/").lower()


def _iter_record_text_fragments(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, (list, tuple, set)):
        fragments: list[str] = []
        for item in value:
            fragments.extend(_iter_record_text_fragments(item))
        return fragments
    if isinstance(value, dict):
        preferred_keys = (
            "url",
            "location",
            "href",
            "referrer",
            "snapshot",
            "code",
            "result",
            "request",
            "response",
            "toolArgs",
            "toolCall",
            "page",
            "data",
            "body",
            "content",
        )
        fragments: list[str] = []
        seen_keys: set[str] = set()
        for key in preferred_keys:
            if key in value:
                fragments.extend(_iter_record_text_fragments(value[key]))
                seen_keys.add(key)
        for key, item in value.items():
            if key in seen_keys:
                continue
            fragments.extend(_iter_record_text_fragments(item))
        return fragments
    return [str(value)]


def _extract_candidate_urls(value: object) -> list[str]:
    candidates: list[str] = []
    for fragment in _iter_record_text_fragments(value):
        text = fragment.strip()
        if not text:
            continue
        candidates.append(text)
        candidates.extend(match.group(0).rstrip(").,;\"'") for match in URL_FRAGMENT_PATTERN.finditer(text))
        candidates.extend(match.group(1).rstrip(").,;\"'") for match in SNAPSHOT_URL_PATTERN.finditer(text))
    return candidates


def _records_reference_target_url(records: list[dict], target_url: str) -> bool:
    target = _normalize_url_for_match(target_url)
    target_path = _normalize_url_path_for_match(target_url)
    if not target:
        return False

    for record in records:
        for candidate in _extract_candidate_urls(record):
            normalized_candidate = _normalize_url_for_match(candidate)
            if normalized_candidate and normalized_candidate == target:
                return True
            if candidate.startswith("/") and _normalize_url_path_for_match(candidate) == target_path:
                return True
    return False


def _session_targets_url(records: list[dict], target_url: str) -> bool:
    target = _normalize_url_for_match(target_url)
    if not target:
        return False

    for record in records:
        tool_call = record.get("toolCall")
        if not isinstance(tool_call, dict):
            continue
        tool_args = tool_call.get("toolArgs")
        if not isinstance(tool_args, dict):
            continue
        candidate_url = tool_args.get("url")
        if isinstance(candidate_url, str) and _normalize_url_for_match(candidate_url) == target:
            return True
    return _records_reference_target_url(records, target_url)


def _parse_session_timestamp(session_id: str) -> int:
    if not session_id.startswith("session-"):
        return 0
    _, _, suffix = session_id.partition("-")
    return int(suffix) if suffix.isdigit() else 0


async def _reserve_session_id(task_id: str, session_id: str) -> bool:
    async with _session_claim_lock:
        for claimed in _task_session_claims.values():
            if session_id in claimed:
                return False
        _task_session_claims.setdefault(task_id, set()).add(session_id)
        return True


async def _release_task_session_claims(task_id: str) -> None:
    async with _session_claim_lock:
        _task_session_claims.pop(task_id, None)


async def _claim_session_id_for_url(
    task_id: str,
    *,
    url: str,
    browser_started_at: datetime,
    preferred_session_id: str | None = None,
) -> str | None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + SESSION_CLAIM_TIMEOUT_SECONDS
    min_timestamp = int(browser_started_at.timestamp() * 1000) - SESSION_CLAIM_GRACE_MS
    preferred_timestamp = _parse_session_timestamp(preferred_session_id) if preferred_session_id else 0

    while True:
        if preferred_session_id and (not preferred_timestamp or preferred_timestamp >= min_timestamp):
            if await _session_id_materialized(preferred_session_id):
                if await _reserve_session_id(task_id, preferred_session_id):
                    return preferred_session_id

        session_ids = sorted(await _list_session_ids(), key=_parse_session_timestamp, reverse=True)
        if preferred_session_id and preferred_session_id in session_ids:
            session_ids = [preferred_session_id, *[item for item in session_ids if item != preferred_session_id]]

        candidate_sessions: list[str] = []
        for session_id in session_ids:
            session_timestamp = _parse_session_timestamp(session_id)
            if session_timestamp and session_timestamp < min_timestamp:
                continue
            records = await _read_session_records(session_id)
            network_records: list[dict] = []
            if records and _session_targets_url(records, url):
                if await _reserve_session_id(task_id, session_id):
                    return session_id
                continue

            network_records = await _read_session_network_records(session_id)
            if network_records and _records_reference_target_url(network_records, url):
                if await _reserve_session_id(task_id, session_id):
                    return session_id
                continue

            if records or network_records:
                candidate_sessions.append(session_id)

        unique_candidates = list(dict.fromkeys(candidate_sessions))
        if len(unique_candidates) == 1 and await _reserve_session_id(task_id, unique_candidates[0]):
            return unique_candidates[0]

        if loop.time() >= deadline:
            break
        await asyncio.sleep(SESSION_CLAIM_POLL_INTERVAL_SECONDS)

    if preferred_session_id and await _session_id_materialized(preferred_session_id):
        if await _reserve_session_id(task_id, preferred_session_id):
            return preferred_session_id
    return None


def _summary_message(label: str, summary: dict) -> str:
    skipped_suffix = f"，已跳过 {summary['skipped']}" if summary.get("skipped", 0) > 0 else ""
    return (
        f"{label}：共 {summary['total']} 项，成功 {summary['success']}，失败 {summary['failed']}，"
        f"运行中 {summary['running']}，队列等待 {summary.get('queued', 0)}，待开始 {summary['pending']}{skipped_suffix}"
    )


def _derive_task_status(browser_summary: dict, analyse_summary: dict, final_summary: dict) -> str:
    pending_count = final_summary["pending"] + final_summary.get("queued", 0)
    active_count = final_summary["running"] + final_summary.get("queued", 0)
    stage_started = any(
        summary["running"] > 0
        or summary.get("queued", 0) > 0
        or summary["success"] > 0
        or summary["failed"] > 0
        for summary in (browser_summary, analyse_summary, final_summary)
    )
    if final_summary["total"] == 0:
        return "pending"
    if pending_count == 0 and active_count == 0:
        return "completed" if final_summary["failed"] == 0 else "failed"
    if stage_started:
        return "running"
    return "pending"


def _debug_export_root() -> Path:
    return Path(__file__).resolve().parents[2] / "worklog" / "archive" / "frontend-backend" / "debug-exports"


def _render_markdown_section(title: str, payload: object) -> str:
    return f"## {title}\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"


async def _export_debug_session_markdown(
    *,
    task_id: str,
    item_id: int,
    url: str,
    browser_mode: str,
    session_id: str,
) -> str:
    meta = await _read_session_meta(session_id)
    log_records = await _read_session_records(session_id)
    network_records = await _read_session_network_records(session_id)

    export_root = _debug_export_root()
    export_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = export_root / f"{timestamp}-task-{task_id[:8]}-item-{item_id}-debug-session-{session_id}.md"

    content = [
        "# Debug Session Export",
        "",
        f"- task_id: `{task_id}`",
        f"- item_id: `{item_id}`",
        f"- url: `{url}`",
        f"- browser_mode: `{browser_mode}`",
        f"- session_id: `{session_id}`",
        f"- exported_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- meta_key: `{session_meta_key(session_id)}`",
        f"- log_key: `{session_log_key(session_id)}`",
        f"- network_key: `{session_network_key(session_id)}`",
        f"- log_count: `{len(log_records)}`",
        f"- network_count: `{len(network_records)}`",
        "",
        _render_markdown_section("Session Meta", meta),
        _render_markdown_section("Session Log", log_records),
        _render_markdown_section("Session Network", network_records),
    ]
    file_path.write_text("\n".join(content), encoding="utf-8")
    return str(file_path.resolve())


def _apply_stage_summary(stage: TaskStage, summary: dict, message: str) -> None:
    now = datetime.now(timezone.utc)
    stage.status = summary["status"]
    stage.message = message
    if summary["status"] != "pending" and stage.started_at is None:
        stage.started_at = now
    is_terminal = summary["total"] > 0 and summary["pending"] == 0 and summary.get("queued", 0) == 0 and summary["running"] == 0
    if is_terminal:
        if stage.completed_at is None:
            stage.completed_at = now
    else:
        stage.completed_at = None


def _refresh_task_runtime(task_id: str) -> None:
    db = SessionLocal()
    try:
        task = db.query(AutoReverseTask).filter(AutoReverseTask.id == task_id).first()
        if task is None:
            return
        items = (
            db.query(TaskUrlItem)
            .filter(TaskUrlItem.task_id == task_id)
            .order_by(TaskUrlItem.url_index.asc(), TaskUrlItem.id.asc())
            .all()
        )
        stages = {
            stage.agent_tag: stage
            for stage in db.query(TaskStage).filter(TaskStage.task_id == task_id).all()
        }
        browser_summary = _summarize_step([item.browser_status for item in items])
        analyse_summary = _summarize_step([item.analyse_status for item in items])
        finish_summary = _summarize_step([item.final_status for item in items])

        if "browser_agent" in stages:
            _apply_stage_summary(stages["browser_agent"], browser_summary, _summary_message("browser_agent", browser_summary))
        if "analyse_agent" in stages:
            _apply_stage_summary(stages["analyse_agent"], analyse_summary, _summary_message("analyse_agent", analyse_summary))
        if "finish" in stages:
            _apply_stage_summary(stages["finish"], finish_summary, _summary_message("finish", finish_summary))

        task.status = _derive_task_status(browser_summary, analyse_summary, finish_summary)
        db.commit()
        dashboard_service.record_dashboard_snapshot(db)
    finally:
        db.close()


def _update_stage(
    db: Session,
    *,
    task_id: str,
    agent_tag: str,
    status_text: str,
    message: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    stage = db.query(TaskStage).filter(TaskStage.task_id == task_id, TaskStage.agent_tag == agent_tag).first()
    if not stage:
        return

    stage.status = status_text
    stage.message = message
    now = datetime.now(timezone.utc)
    if started and stage.started_at is None:
        stage.started_at = now
    if completed:
        stage.completed_at = now
    db.commit()


def _update_task_status(db: Session, task_id: str, status_text: str) -> None:
    task = db.query(AutoReverseTask).filter(AutoReverseTask.id == task_id).first()
    if not task:
        return
    task.status = status_text
    db.commit()


def _add_analysis_result(
    db: Session,
    *,
    task_id: str,
    url: str,
    session_id: str | None,
    success: bool,
    report_text: str,
    error: str | None,
) -> None:
    db.add(
        AnalysisResult(
            task_id=task_id,
            url=url,
            session_id=session_id,
            success=success,
            report_text=report_text,
            error=error,
        )
    )
    db.commit()


def _archive_success_result(
    db: Session,
    *,
    task_id: str,
    url: str,
    session_id: str | None,
    report_text: str,
) -> None:
    db.add(
        SuccessResultArchive(
            task_id=task_id,
            url=url,
            session_id=session_id,
            report_text=report_text,
        )
    )
    db.commit()


async def _run_browser_with_runtime(
    *,
    task_id: str,
    item_id: int,
    url: str,
    browser_mode: str,
    headless: bool = False,
    requested_mcp_tools: list[str],
    requested_skills: list[str],
    browser_system_prompt: str | None,
    browser_prompt: str | None,
    model_profile: dict | None,
    skill_registry: SkillRegistry,
) -> BrowserAgentResult:
    runtime_servers = _resolve_runtime_server_names(requested_mcp_tools, browser_mode=browser_mode)

    with official_skills_runtime(skill_registry, requested_skills) as skills_runtime:

        async def _run_with_registry(registry: ToolRegistry) -> tuple[BrowserAgentResult, str, tuple[str, ...]]:
            mcp_tools = registry.get_tools()
            allowed_tool_names = {str(getattr(tool, "name", "") or "").strip() for tool in mcp_tools}
            if skills_runtime is not None:
                allowed_tool_names.update(skills_runtime.tool_names)
            callback_handler = _TaskItemToolCallbackHandler(
                task_id=task_id,
                item_id=item_id,
                agent_tag="browser_agent",
                allowed_tool_names=allowed_tool_names,
            )
            result = await run_browser_agent(
                url,
                mcp_tools,
                browser_system_prompt=browser_system_prompt,
                browser_prompt=browser_prompt,
                model_profile=model_profile,
                callbacks=[callback_handler],
                agent_middleware=list(skills_runtime.middleware) if skills_runtime is not None else None,
            )
            latest_tool = callback_handler.get_latest_tool_name()
            completed_tool_sequence = callback_handler.get_completed_tool_sequence()
            return result, latest_tool, completed_tool_sequence

        def _finalize_browser_result(
            result: BrowserAgentResult,
            latest_tool: str,
            completed_tool_sequence: tuple[str, ...],
        ) -> BrowserAgentResult:
            result = _apply_browser_completion_gate(
                result,
                browser_prompt=browser_prompt,
                completed_tool_sequence=completed_tool_sequence,
            )
            if result.success:
                return result
            normalized_error = str(result.error or "").strip()
            if latest_tool and latest_tool != "browser_close" and "last tool=" not in normalized_error:
                normalized_error = f"{normalized_error or result.error or 'browser_agent failed'} (last tool={latest_tool})".strip()
            result.error = normalized_error or result.error
            return result

        if runtime_servers:
            await _release_preserved_browser_runtime(task_id, item_id)

            if browser_mode == "standalone":
                loop = asyncio.get_running_loop()
                result_future: asyncio.Future[BrowserAgentResult] = loop.create_future()
                key = _preserved_browser_runtime_key(task_id, item_id)

                async def _run_standalone_runtime_owner() -> None:
                    lease: _PreservedBrowserRuntimeLease | None = None
                    result: BrowserAgentResult | None = None
                    try:
                        async with ToolRegistry(runtime_servers, headless=headless, isolated=True) as registry:
                            result, latest_tool, completed_tool_sequence = await _run_with_registry(registry)
                            result = _finalize_browser_result(result, latest_tool, completed_tool_sequence)
                            if _should_preserve_standalone_browser_runtime(
                                headless=headless,
                                success=result.success,
                                latest_tool=latest_tool,
                            ):
                                lease = _create_preserved_browser_runtime_lease()
                                _preserved_browser_runtimes[key] = lease
                                _schedule_preserved_browser_runtime_cleanup(
                                    task_id,
                                    item_id,
                                    delay_seconds=BROWSER_AGENT_STANDALONE_PRESERVED_CLOSE_DELAY_SECONDS,
                                )
                                if not result_future.done():
                                    result_future.set_result(result)
                                await lease.release_event.wait()
                        if result is not None and not result_future.done():
                            result_future.set_result(result)
                    except Exception as exc:
                        if not result_future.done():
                            result_future.set_exception(exc)
                        if lease is not None and not lease.closed_future.done():
                            lease.closed_future.set_exception(exc)
                        raise
                    finally:
                        if lease is not None:
                            if _preserved_browser_runtimes.get(key) is lease:
                                _preserved_browser_runtimes.pop(key, None)
                            if not lease.closed_future.done():
                                lease.closed_future.set_result(None)

                runtime_owner_task = asyncio.create_task(_run_standalone_runtime_owner())
                runtime_owner_task.add_done_callback(
                    lambda task: _consume_background_task_exception(task, label=f"browser runtime owner {task_id}/{item_id}")
                )
                return await result_future

            async with ToolRegistry(runtime_servers, headless=headless) as registry:
                result, latest_tool, completed_tool_sequence = await _run_with_registry(registry)
                return _finalize_browser_result(result, latest_tool, completed_tool_sequence)

        result = await run_browser_agent(
            url,
            [],
            browser_system_prompt=browser_system_prompt,
            browser_prompt=browser_prompt,
            model_profile=model_profile,
            agent_middleware=list(skills_runtime.middleware) if skills_runtime is not None else None,
        )
        return _apply_browser_completion_gate(
            result,
            browser_prompt=browser_prompt,
            completed_tool_sequence=(),
        )


async def _run_analysis_with_runtime(
    *,
    task_id: str,
    item_id: int,
    session_id: str,
    requested_mcp_tools: list[str],
    requested_skills: list[str],
    analyse_prompt: str | None,
    model_profile: dict | None,
    skill_registry: SkillRegistry,
):
    base_tools = get_analysis_tools()
    runtime_servers = _resolve_runtime_server_names(requested_mcp_tools)
    normalized_analyse_prompt = config_service.normalize_analyse_prompt(analyse_prompt)
    if normalized_analyse_prompt and normalized_analyse_prompt.strip():
        effective_analyse_prompt = normalized_analyse_prompt.strip()
    else:
        effective_analyse_prompt = (
            "请围绕 redis:{session_id} 做逆向分析，优先用轻量工具快速缩小范围，再按需查看更细的 endpoint、sample、detail 与 sequence 信息；"
            "不要无差别展开整份 Redis network，也不要调用任何 legacy 的 read_network_log 工具；"
            "只有在你确认值得深挖时，才继续调用更重的详情工具；"
            "输出聚焦关键接口、鉴权方式、核心请求参数、关键响应字段与可复现建议。"
        )

    with official_skills_runtime(skill_registry, requested_skills) as skills_runtime:
        if runtime_servers:
            async with ToolRegistry(runtime_servers) as registry:
                mcp_tools = registry.get_tools(runtime_servers)
                allowed_tool_names = {str(getattr(tool, "name", "") or "").strip() for tool in mcp_tools}
                if skills_runtime is not None:
                    allowed_tool_names.update(skills_runtime.tool_names)
                callback_handler = _TaskItemToolCallbackHandler(
                    task_id=task_id,
                    item_id=item_id,
                    agent_tag="analyse_agent",
                    allowed_tool_names=allowed_tool_names,
                )
                tools = base_tools + mcp_tools
                return await run_analysis_agent(
                    session_id,
                    tools,
                    analyse_prompt=effective_analyse_prompt,
                    model_profile=model_profile,
                    callbacks=[callback_handler],
                    agent_middleware=list(skills_runtime.middleware) if skills_runtime is not None else None,
                )

        return await run_analysis_agent(
            session_id,
            base_tools,
            analyse_prompt=effective_analyse_prompt,
            model_profile=model_profile,
            agent_middleware=list(skills_runtime.middleware) if skills_runtime is not None else None,
        )


async def _mark_item_failed_from_exception(task_id: str, item_id: int, error: str) -> None:
    db = SessionLocal()
    try:
        row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
        if row is None:
            return
        session_id = row.session_id
        url = row.url
        browser_error = _format_failure_message("browser_agent 异常", error)
        analyse_error = _format_failure_message("analyse_agent 异常", error)
        final_error = _format_failure_message("流水线异常", error)
        if row.browser_status == "pending":
            row.browser_status = "failed"
            row.browser_message = browser_error
            row.browser_started_at = row.browser_started_at or datetime.now(timezone.utc)
            row.browser_completed_at = datetime.now(timezone.utc)
        elif row.browser_status == "running":
            row.browser_status = "failed"
            row.browser_message = browser_error
            row.browser_completed_at = datetime.now(timezone.utc)

        if row.analyse_status == "pending":
            row.analyse_status = "failed"
            row.analyse_message = analyse_error
            row.analyse_started_at = row.analyse_started_at or datetime.now(timezone.utc)
            row.analyse_completed_at = datetime.now(timezone.utc)
        elif row.analyse_status == "running":
            row.analyse_status = "failed"
            row.analyse_message = analyse_error
            row.analyse_completed_at = datetime.now(timezone.utc)

        row.final_status = "failed"
        row.error = final_error
        db.commit()
        db.add(
            AnalysisResult(
                task_id=task_id,
                url=url,
                session_id=session_id,
                success=False,
                report_text="",
                error=final_error,
            )
        )
        db.commit()
    finally:
        db.close()
    _refresh_task_runtime(task_id)


async def _run_task_item(
    task_id: str,
    item_id: int,
    *,
    url: str,
    browser_mode: str,
    headless: bool = False,
    browser_system_prompt: str | None,
    browser_prompt: str | None,
    analyse_prompt: str | None,
    requested_mcp_tools: dict[str, list[str]],
    requested_skills: dict[str, list[str]],
    requested_models: dict[str, dict],
    debug_mode_isolation_enabled: bool,
    semaphore: asyncio.Semaphore,
    skill_registry: SkillRegistry,
) -> None:
    async with semaphore:
        db = SessionLocal()
        browser_started_at = datetime.now(timezone.utc)
        try:
            row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
            if row is None:
                return

            _set_item_browser_state(
                db,
                row,
                status_text="running",
                message="browser_agent 正在访问目标 URL",
                started=True,
            )
            _refresh_task_runtime(task_id)

            browser_result = await _run_browser_with_runtime(
                task_id=task_id,
                item_id=item_id,
                url=url,
                browser_mode=browser_mode,
                headless=headless,
                requested_mcp_tools=requested_mcp_tools["browser_agent"],
                requested_skills=requested_skills["browser_agent"],
                browser_system_prompt=browser_system_prompt,
                browser_prompt=browser_prompt,
                model_profile=requested_models.get("browser_agent"),
                skill_registry=skill_registry,
            )
            session_id = None
            if browser_result.success:
                session_id = await _claim_session_id_for_url(
                    task_id,
                    url=url,
                    browser_started_at=browser_started_at,
                    preferred_session_id=browser_result.session_id,
                )

            row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
            if row is None:
                return
            browser_failure_message = _format_failure_message("browser_agent 失败", browser_result.error)
            _set_item_browser_state(
                db,
                row,
                status_text="success" if browser_result.success else "failed",
                message="browser_agent 阶段完成"
                if browser_result.success
                else browser_failure_message,
                session_id=session_id,
                completed=True,
            )
            _refresh_task_runtime(task_id)

            row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
            if row is None:
                return

            if not browser_result.success:
                error = browser_failure_message
                _set_item_analyse_state(
                    db,
                    row,
                    status_text="failed",
                    message="browser_agent 失败，analyse_agent 已跳过",
                    completed=True,
                )
                _set_item_final_state(
                    db,
                    row,
                    status_text="failed",
                    error=error,
                    report_text="",
                )
                _add_analysis_result(
                    db,
                    task_id=task_id,
                    url=url,
                    session_id=session_id,
                    success=False,
                    report_text="",
                    error=error,
                )
                _refresh_task_runtime(task_id)
                return

            if not session_id:
                error = "未捕获到 session_id，无法调用 analyse_agent"
                _set_item_analyse_state(
                    db,
                    row,
                    status_text="failed",
                    message=error,
                    completed=True,
                )
                _set_item_final_state(
                    db,
                    row,
                    status_text="failed",
                    error=error,
                    report_text="",
                )
                _add_analysis_result(
                    db,
                    task_id=task_id,
                    url=url,
                    session_id=None,
                    success=False,
                    report_text="",
                    error=error,
                )
                _refresh_task_runtime(task_id)
                return

            await _prepare_session_for_analysis(task_id, item_id, session_id)

            _set_item_analyse_state(
                db,
                row,
                status_text="running",
                message="analyse_agent 正在分析会话数据",
                started=True,
            )
            _refresh_task_runtime(task_id)

            report = await _run_analysis_with_runtime(
                task_id=task_id,
                item_id=item_id,
                session_id=session_id,
                requested_mcp_tools=requested_mcp_tools["analyse_agent"],
                requested_skills=requested_skills["analyse_agent"],
                analyse_prompt=analyse_prompt,
                model_profile=requested_models.get("analyse_agent"),
                skill_registry=skill_registry,
            )

            row = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id, TaskUrlItem.id == item_id).first()
            if row is None:
                return
            analyse_failure_message = _format_failure_message("analyse_agent 失败", report.error)
            _set_item_analyse_state(
                db,
                row,
                status_text="success" if report.success else "failed",
                message="analyse_agent 阶段完成"
                if report.success
                else analyse_failure_message,
                completed=True,
            )
            _set_item_final_state(
                db,
                row,
                status_text="success" if report.success else "failed",
                error=None if report.success else analyse_failure_message,
                report_text=report.report,
            )
            _add_analysis_result(
                db,
                task_id=task_id,
                url=url,
                session_id=session_id,
                success=report.success,
                report_text=report.report,
                error=None if report.success else analyse_failure_message,
            )
            if report.success and report.cleanup_allowed:
                _archive_success_result(
                    db,
                    task_id=task_id,
                    url=url,
                    session_id=session_id,
                    report_text=report.report,
                )
                if session_id:
                    try:
                        _delete_redis_sessions([session_id])
                    except Exception as cleanup_error:
                        print(f"[TaskService] 警告：analyse 成功后清理 Redis session 失败 {session_id} — {cleanup_error}")
            _refresh_task_runtime(task_id)
        except Exception as exc:
            await _mark_item_failed_from_exception(task_id, item_id, str(exc))
        finally:
            db.close()


def create_task(
    db: Session,
    *,
    urls: list[str],
    browser_config: dict,
    analyse_config: dict,
    browser_prompt: str | None = None,
    analyse_prompt: str | None = None,
    headless: bool = False,
    max_concurrent: int | None = None,
) -> AutoReverseTask:
    if not urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="urls 不能为空")

    cfg = config_service.get_config_payload(db)
    browser_mode = config_service.normalize_browser_mode(browser_config.get("browser_mode") or cfg.get("browser_mode"))
    allowed_mcp_tools = cfg.get("mcp_tools") or config_service.REQUIRED_MCP_TOOLS
    allowed_skills = cfg.get("skills") or []
    browser_excluded_mcp_tools = [config_service.ROXYBROWSER_MCP_TOOL] if browser_mode == "standalone" else []

    final_browser_config = _normalize_agent_selection(
        selected_mcp_tools=list(browser_config.get("mcp_tools") or []),
        selected_skills=list(browser_config.get("skills") or []),
        selected_model_provider=str(browser_config.get("model_provider") or ""),
        selected_model_name=str(browser_config.get("model_name") or ""),
        selected_model_profile_key=str(browser_config.get("model_profile_key") or ""),
        allowed_mcp_tools=allowed_mcp_tools,
        allowed_skills=allowed_skills,
        force_required_mcp=True,
        browser_mode=browser_mode,
        excluded_mcp_tools=browser_excluded_mcp_tools,
    )
    final_analyse_config = _normalize_agent_selection(
        selected_mcp_tools=list(analyse_config.get("mcp_tools") or []),
        selected_skills=list(analyse_config.get("skills") or []),
        selected_model_provider=str(analyse_config.get("model_provider") or ""),
        selected_model_name=str(analyse_config.get("model_name") or ""),
        selected_model_profile_key=str(analyse_config.get("model_profile_key") or ""),
        allowed_mcp_tools=allowed_mcp_tools,
        allowed_skills=allowed_skills,
        force_required_mcp=False,
    )

    try:
        requested_models = {
            "browser_agent": config_service.build_model_selection_snapshot(
                db,
                provider=str(final_browser_config["model_provider"]),
                model_name=str(final_browser_config["model_name"]),
                profile_key=str(final_browser_config["model_profile_key"]),
            ),
            "analyse_agent": config_service.build_model_selection_snapshot(
                db,
                provider=str(final_analyse_config["model_provider"]),
                model_name=str(final_analyse_config["model_name"]),
                profile_key=str(final_analyse_config["model_profile_key"]),
            ),
        }
    except config_service.ConfigValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    final_browser_prompt = (
        browser_prompt
        if browser_prompt is not None
        else (
            cfg.get("standalone_browser_prompt") or cfg.get("browser_prompt")
            if browser_mode == "standalone"
            else cfg.get("browser_prompt")
        )
    )
    raw_analyse_prompt = analyse_prompt if analyse_prompt is not None else cfg.get("analyse_prompt")
    final_analyse_prompt = (
        config_service.normalize_analyse_prompt(raw_analyse_prompt)
        or config_service.DEFAULT_ANALYSE_PROMPT_TEMPLATE
    )
    final_browser_system_prompt = (
        cfg.get("standalone_browser_agent_system_prompt") or PLAYWRIGHT_STANDALONE_BROWSER_AGENT_SYSTEM_PROMPT
        if browser_mode == "standalone"
        else cfg.get("browser_agent_system_prompt")
    )
    debug_mode_isolation_enabled = bool(cfg.get("debug_mode_isolation_enabled", config_service.DEFAULT_DEBUG_MODE_ISOLATION_ENABLED))

    task = AutoReverseTask(
        id=str(uuid.uuid4()),
        status="pending",
        browser_mode=browser_mode,
        headless=headless,
        max_concurrent=max_concurrent,
        debug_mode_isolation_enabled=debug_mode_isolation_enabled,
        requested_urls=json.dumps(urls, ensure_ascii=False),
        requested_mcp_tools=json.dumps(
            {
                "browser_agent": final_browser_config["mcp_tools"],
                "analyse_agent": final_analyse_config["mcp_tools"],
            },
            ensure_ascii=False,
        ),
        requested_skills=json.dumps(
            {
                "browser_agent": final_browser_config["skills"],
                "analyse_agent": final_analyse_config["skills"],
            },
            ensure_ascii=False,
        ),
        requested_models=json.dumps(requested_models, ensure_ascii=False),
        browser_agent_system_prompt=final_browser_system_prompt,
        browser_prompt=final_browser_prompt,
        analyse_prompt=final_analyse_prompt,
    )
    db.add(task)
    db.flush()

    db.add_all(
        [
            TaskStage(task_id=task.id, agent_tag="browser_agent", status="pending"),
            TaskStage(task_id=task.id, agent_tag="analyse_agent", status="pending"),
            TaskStage(task_id=task.id, agent_tag="finish", status="pending"),
        ]
    )
    db.add_all(
        [TaskUrlItem(task_id=task.id, url=url, url_index=index) for index, url in enumerate(urls)]
    )
    db.commit()
    db.refresh(task)
    dashboard_service.record_dashboard_snapshot(db)
    return task


def get_task_or_404(db: Session, task_id: str) -> AutoReverseTask:
    task = db.query(AutoReverseTask).filter(AutoReverseTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


def delete_task(db: Session, task_id: str) -> dict:
    task = get_task_or_404(db, task_id)
    if not _is_terminal_task_status(task.status):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前任务仍在执行中，暂不支持删除")

    try:
        _delete_task_records(db, task_id)
        db.commit()
        dashboard_service.record_dashboard_snapshot(db)
    except Exception:
        db.rollback()
        raise

    return {"task_id": task_id, "deleted": True}


def clear_recent_tasks(db: Session, limit: int = RECENT_TASK_BATCH_LIMIT) -> dict:
    effective_limit = max(1, min(int(limit or RECENT_TASK_BATCH_LIMIT), 50))
    rows = (
        db.query(AutoReverseTask)
        .order_by(AutoReverseTask.created_at.desc())
        .limit(effective_limit)
        .all()
    )

    deleted_task_ids: list[str] = []
    skipped_task_ids: list[str] = []

    try:
        for task in rows:
            if _is_terminal_task_status(task.status):
                _delete_task_records(db, task.id)
                deleted_task_ids.append(task.id)
            else:
                skipped_task_ids.append(task.id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "requested": len(rows),
        "deleted": len(deleted_task_ids),
        "skipped": len(skipped_task_ids),
        "deleted_task_ids": deleted_task_ids,
        "skipped_task_ids": skipped_task_ids,
    }


def clear_failed_tasks(db: Session) -> dict:
    rows = (
        db.query(AutoReverseTask)
        .filter(AutoReverseTask.status.in_(["failed", "error"]))
        .order_by(AutoReverseTask.updated_at.desc())
        .all()
    )

    deleted_task_ids: list[str] = []
    task_ids = [task.id for task in rows]
    deleted_session_ids = _collect_orphan_session_ids_for_tasks(db, task_ids)

    try:
        _delete_redis_sessions(deleted_session_ids)
        for task in rows:
            _delete_task_records(db, task.id)
            deleted_task_ids.append(task.id)
        db.commit()
        dashboard_service.record_dashboard_snapshot(db)
    except Exception:
        db.rollback()
        raise

    return {
        "requested": len(rows),
        "deleted": len(deleted_task_ids),
        "skipped": 0,
        "deleted_task_ids": deleted_task_ids,
        "skipped_task_ids": [],
        "deleted_session_count": len(deleted_session_ids),
        "deleted_session_ids": deleted_session_ids,
    }


def clear_all_tasks(db: Session) -> dict:
    rows = (
        db.query(AutoReverseTask)
        .order_by(AutoReverseTask.updated_at.desc(), AutoReverseTask.created_at.desc())
        .all()
    )

    deleted_task_ids: list[str] = []
    task_ids = [task.id for task in rows]
    deleted_session_ids = _collect_orphan_session_ids_for_tasks(db, task_ids)

    try:
        _delete_redis_sessions(deleted_session_ids)
        for task in rows:
            _delete_task_records(db, task.id)
            deleted_task_ids.append(task.id)
        db.commit()
        dashboard_service.record_dashboard_snapshot(db)
    except Exception:
        db.rollback()
        raise

    return {
        "requested": len(rows),
        "deleted": len(deleted_task_ids),
        "skipped": 0,
        "deleted_task_ids": deleted_task_ids,
        "skipped_task_ids": [],
        "deleted_session_count": len(deleted_session_ids),
        "deleted_session_ids": deleted_session_ids,
    }


def get_task_status_payload(db: Session, task_id: str) -> dict:
    task = get_task_or_404(db, task_id)
    stages = db.query(TaskStage).filter(TaskStage.task_id == task_id).order_by(TaskStage.id.asc()).all()
    items = (
        db.query(TaskUrlItem)
        .filter(TaskUrlItem.task_id == task_id)
        .order_by(TaskUrlItem.url_index.asc(), TaskUrlItem.id.asc())
        .all()
    )
    return {
        "task_id": task.id,
        "status": task.status,
        "urls": json.loads(task.requested_urls),
        "steps": _build_task_steps(items),
        "items": [_serialize_task_item(item) for item in items],
        "stages": [
            {
                "agent_tag": stage.agent_tag,
                "status": stage.status,
                "message": stage.message,
                "started_at": stage.started_at,
                "completed_at": stage.completed_at,
            }
            for stage in stages
        ],
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def get_task_results_payload(db: Session, task_id: str) -> list[dict]:
    _ = get_task_or_404(db, task_id)
    rows = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).order_by(AnalysisResult.id.asc()).all()
    return [
        {
            "url": row.url,
            "session_id": row.session_id,
            "success": row.success,
            "report_text": row.report_text,
            "error": row.error,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def list_success_result_archives(db: Session, *, task_id: str | None = None, limit: int | None = None) -> list[dict]:
    query = db.query(SuccessResultArchive)
    if task_id:
        query = query.filter(SuccessResultArchive.task_id == task_id)
    query = query.order_by(SuccessResultArchive.created_at.desc(), SuccessResultArchive.id.desc())
    if limit is not None:
        query = query.limit(max(1, min(int(limit or 1), 500)))
    rows = query.all()
    return [
        {
            "id": row.id,
            "task_id": row.task_id,
            "url": row.url,
            "session_id": row.session_id,
            "report_text": row.report_text,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def launch_task(task_id: str) -> None:
    if task_id in _running_tasks:
        return
    _running_tasks.add(task_id)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        if _runtime_loop is None or not _runtime_loop.is_running():
            _running_tasks.discard(task_id)
            raise RuntimeError("Auto Reverse 后台事件循环不可用")
        try:
            _runtime_loop.call_soon_threadsafe(_schedule_task_pipeline, task_id)
        except RuntimeError:
            _running_tasks.discard(task_id)
            raise RuntimeError("Auto Reverse 后台事件循环不可用")
        return

    try:
        loop.create_task(_run_task_pipeline(task_id))
    except RuntimeError:
        _running_tasks.discard(task_id)
        raise RuntimeError("Auto Reverse 后台事件循环不可用")


def _schedule_task_pipeline(task_id: str) -> None:
    asyncio.create_task(_run_task_pipeline(task_id))


async def _run_task_pipeline(task_id: str) -> None:
    db = SessionLocal()
    try:
        task = db.query(AutoReverseTask).filter(AutoReverseTask.id == task_id).first()
        if task is None:
            return

        requested_mcp_tools = _load_requested_mapping(task.requested_mcp_tools)
        requested_skills = _load_requested_mapping(task.requested_skills)
        requested_models = _load_requested_profiles(task.requested_models)
        browser_mode = config_service.normalize_browser_mode(task.browser_mode)
        headless = bool(task.headless) if task.headless is not None else False
        effective_concurrent = task.max_concurrent if task.max_concurrent else MAX_CONCURRENT_BROWSERS
        debug_mode_isolation_enabled = (
            config_service.DEFAULT_DEBUG_MODE_ISOLATION_ENABLED
            if task.debug_mode_isolation_enabled is None
            else bool(task.debug_mode_isolation_enabled)
        )
        browser_system_prompt = task.browser_agent_system_prompt
        browser_prompt = task.browser_prompt
        analyse_prompt = task.analyse_prompt
        item_rows = (
            db.query(TaskUrlItem)
            .filter(TaskUrlItem.task_id == task_id)
            .order_by(TaskUrlItem.url_index.asc(), TaskUrlItem.id.asc())
            .all()
        )
        _seed_browser_queue_states(db, item_rows, effective_concurrent=effective_concurrent)
        item_payloads = [
            {"id": item.id, "url": item.url}
            for item in item_rows
        ]

        _update_task_status(db, task_id, "running")
        _update_stage(
            db,
            task_id=task_id,
            agent_tag="browser_agent",
            status_text="running",
            message="browser_agent 已启动，超出并发上限的 URL 将进入队列等待",
            started=True,
        )
        _refresh_task_runtime(task_id)

        semaphore = asyncio.Semaphore(max(1, effective_concurrent))
        skill_registry = SkillRegistry()
        await asyncio.gather(
            *(
                _run_task_item(
                    task_id,
                    item["id"],
                    url=item["url"],
                    browser_mode=browser_mode,
                    headless=headless,
                    browser_system_prompt=browser_system_prompt,
                    browser_prompt=browser_prompt,
                    analyse_prompt=analyse_prompt,
                    requested_mcp_tools=requested_mcp_tools,
                    requested_skills=requested_skills,
                    requested_models=requested_models,
                    debug_mode_isolation_enabled=debug_mode_isolation_enabled,
                    semaphore=semaphore,
                    skill_registry=skill_registry,
                )
                for item in item_payloads
            )
        )
        _refresh_task_runtime(task_id)

    except Exception as exc:
        pipeline_error = _format_failure_message("流水线异常", str(exc))
        _update_stage(
            db,
            task_id=task_id,
            agent_tag="browser_agent",
            status_text="failed",
            message=pipeline_error,
            completed=True,
        )
        _update_stage(
            db,
            task_id=task_id,
            agent_tag="analyse_agent",
            status_text="failed",
            message=pipeline_error,
            completed=True,
        )
        _update_stage(
            db,
            task_id=task_id,
            agent_tag="finish",
            status_text="failed",
            message=pipeline_error,
            started=True,
            completed=True,
        )
        rows = db.query(TaskUrlItem).filter(TaskUrlItem.task_id == task_id).all()
        for row in rows:
            if row.final_status in TERMINAL_SUCCESS | TERMINAL_FAILED:
                continue
            if row.browser_status == "running":
                row.browser_status = "failed"
            if row.analyse_status == "running":
                row.analyse_status = "failed"
            row.final_status = "failed"
            row.error = pipeline_error
        db.commit()
        _update_task_status(db, task_id, "failed")
    finally:
        _running_tasks.discard(task_id)
        await _release_task_session_claims(task_id)
        db.close()
