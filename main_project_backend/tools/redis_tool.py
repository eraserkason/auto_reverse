"""
Redis 数据读取工具，供分析专家 Agent 使用。

包含两个 LangChain Tool：
- ReadSessionLogTool：读取指定 session 的操作日志（Redis Stream）
- GetSessionLogWindowTool：按窗口读取指定 session 的操作日志摘要
- ListSessionsTool：列出 Redis 中所有的 session ID
"""

from __future__ import annotations

import json
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from utils.redis_client import (
    get_client,
    session_log_key,
    sessions_set_key,
)


class SessionIdInput(BaseModel):
    session_id: str = Field(description="浏览器会话 ID，格式为 session-<timestamp>")


class SessionLogWindowInput(BaseModel):
    session_id: str = Field(description="浏览器会话 ID，格式为 session-<timestamp>")
    limit: int = Field(default=20, ge=1, le=100, description="返回日志条数上限")
    before_stream_id: str | None = Field(default=None, description="用于继续向更早日志翻页的 Redis stream id")
    tool_name: str | None = Field(default=None, description="按 toolCall.toolName 过滤")
    include_snapshots: bool = Field(default=False, description="是否包含快照预览")


class ReadSessionLogTool(BaseTool):
    """读取指定 session 的操作日志（工具调用记录 + ARIA 快照）。"""

    name: str = "read_session_log"
    description: str = (
        "读取指定浏览器会话（session_id）的操作日志，包含工具调用、用户操作和页面 ARIA 快照。"
        "返回 JSON 格式的操作记录列表。"
    )
    args_schema: Type[BaseModel] = SessionIdInput

    def _run(self, session_id: str) -> str:
        raise NotImplementedError("请使用异步版本 _arun")

    async def _arun(self, session_id: str) -> str:
        client = get_client()
        key = session_log_key(session_id)
        entries = await client.xrange(key, "-", "+")
        records = []
        for _stream_id, fields in entries:
            try:
                records.append(json.loads(fields.get("data", "{}")))
            except json.JSONDecodeError:
                records.append({"raw": fields})
        return json.dumps(records, ensure_ascii=False, indent=2)


def _summarize_session_record(record: dict, *, include_snapshots: bool) -> dict:
    tool_call = record.get("toolCall") if isinstance(record.get("toolCall"), dict) else {}
    user_action = record.get("userAction") if isinstance(record.get("userAction"), dict) else {}
    snapshot = str(record.get("snapshot") or "").strip()
    summarized = {
        "ordinal": record.get("ordinal"),
        "code": str(record.get("code") or "").strip(),
        "tool_name": str(tool_call.get("toolName") or "").strip(),
        "tool_args_keys": sorted(tool_call.get("toolArgs", {}).keys()) if isinstance(tool_call.get("toolArgs"), dict) else [],
        "tool_error": bool(tool_call.get("isError")),
        "user_action": user_action,
    }
    if include_snapshots and snapshot:
        normalized = " ".join(snapshot.split())
        summarized["snapshot_preview"] = normalized[:240] + ("..." if len(normalized) > 240 else "")
    return summarized


def _stream_fields_get_data(fields: object) -> str:
    if isinstance(fields, dict):
        return str(fields.get("data", "{}"))
    if isinstance(fields, list):
        normalized: dict[str, object] = {}
        for index in range(0, len(fields), 2):
            key = fields[index] if index < len(fields) else None
            if key is None:
                continue
            value = fields[index + 1] if index + 1 < len(fields) else ""
            normalized[str(key)] = value
        return str(normalized.get("data", "{}"))
    return "{}"


class GetSessionLogWindowTool(BaseTool):
    """按窗口读取指定 session 的操作日志摘要。"""

    name: str = "get_session_log_window"
    description: str = (
        "按窗口读取指定浏览器会话（session_id）的操作日志摘要，"
        "支持按 tool 名称过滤，并默认不返回完整快照。"
    )
    args_schema: Type[BaseModel] = SessionLogWindowInput

    def _run(self, session_id: str, limit: int = 20, before_stream_id: str | None = None, tool_name: str | None = None, include_snapshots: bool = False) -> str:
        raise NotImplementedError("请使用异步版本 _arun")

    async def _arun(
        self,
        session_id: str,
        limit: int = 20,
        before_stream_id: str | None = None,
        tool_name: str | None = None,
        include_snapshots: bool = False,
    ) -> str:
        client = get_client()
        key = session_log_key(session_id)
        normalized_limit = max(1, min(int(limit or 20), 100))
        matched: list[dict] = []
        cursor = str(before_stream_id or "").strip() or "+"
        batch_size = max(normalized_limit * 3, 30)
        normalized_tool = str(tool_name or "").strip().lower()
        next_cursor: str | None = None

        while len(matched) < normalized_limit:
            rows = await client.execute_command("XREVRANGE", key, cursor, "-", "COUNT", batch_size)
            if not rows:
                next_cursor = None
                break

            consumed = 0
            last_stream_id = None
            for stream_id, fields in rows:
                consumed += 1
                last_stream_id = str(stream_id or "").strip()
                try:
                    record = json.loads(_stream_fields_get_data(fields))
                except json.JSONDecodeError:
                    continue
                if normalized_tool:
                    current_tool = str((record.get("toolCall") or {}).get("toolName") or "").strip().lower()
                    if current_tool != normalized_tool:
                        continue
                matched.append(_summarize_session_record(record, include_snapshots=include_snapshots))
                if len(matched) >= normalized_limit:
                    break

            if not last_stream_id:
                next_cursor = None
                break
            next_cursor = last_stream_id
            cursor = f"({last_stream_id}"
            if consumed < batch_size:
                break

        return json.dumps(
            {
                "session_id": session_id,
                "returned": matched[:normalized_limit],
                "next_cursor": next_cursor,
            },
            ensure_ascii=False,
            indent=2,
        )


class EmptyInput(BaseModel):
    pass


class ListSessionsTool(BaseTool):
    """列出 Redis 中所有已记录的浏览器 session ID。"""

    name: str = "list_sessions"
    description: str = (
        "列出 Redis 中所有已记录的浏览器会话 ID（session_id）列表，"
        "可用于逐一分析每个会话的数据。"
    )
    args_schema: Type[BaseModel] = EmptyInput

    def _run(self) -> str:
        raise NotImplementedError("请使用异步版本 _arun")

    async def _arun(self) -> str:
        client = get_client()
        session_ids = await client.smembers(sessions_set_key())
        return json.dumps(sorted(session_ids), ensure_ascii=False)


def get_analysis_tools() -> list[BaseTool]:
    """返回分析专家 Agent 所需的全部 Redis 工具列表。"""
    return [
        ReadSessionLogTool(),
        GetSessionLogWindowTool(),
        ListSessionsTool(),
    ]
