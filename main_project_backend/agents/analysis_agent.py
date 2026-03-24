"""
分析专家 Agent：读取 Redis 中指定 session 的浏览器数据包，
对操作日志和网络请求进行分析，输出分析报告。

默认优先使用结构化低上下文流程：
  - overview / statistics / endpoint groups
  - candidate ranking
  - 少量 sample
  - 最终 1-2 条请求升级到 preview detail

只有在所需工具不完整时，才回退到 legacy create_react_agent。
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from newapi_sdk import NewAPIRequestError
from services.config_service import DEFAULT_ANALYSE_PROMPT_TEMPLATE
from services.llm_factory import create_default_llm, create_llm_from_profile


STRUCTURED_REQUIRED_TOOL_NAMES = {
    "get_dataset_overview",
    "extract_api_endpoints",
    "get_request_details",
    "rank_candidate_requests",
    "get_endpoint_group_summary",
    "get_endpoint_group_samples",
}
STRUCTURED_FLOW_CONTROL_TOKENS = (
    "[[structured_analysis]]",
    "[structured_analysis]",
    "#structured_analysis",
)
MAX_ENDPOINT_GROUPS = 3
MAX_SELECTED_REQUESTS = 2
MAX_SEQUENCE_WINDOWS = 1
MAX_TOOL_RESULT_EXCERPT = 280
ANALYSIS_SYNTHESIS_MAX_RETRIES = 2
ANALYSIS_SYNTHESIS_RETRY_BACKOFF_SECONDS = 0.6


@dataclass
class AnalysisReport:
    session_id: str
    report: str
    success: bool
    error: str | None = None
    cleanup_allowed: bool = False


class AnalysisValidationError(RuntimeError):
    """结构化分析拿到异常空结果或缺少关键证据时抛出。"""


@dataclass
class ToolInvocationResult:
    name: str
    args: dict[str, Any]
    normalized: Any
    raw_text: str
    raw_excerpt: str


@dataclass
class AnalysisScratchpad:
    session_id: str
    dataset_id: str
    dataset_overview: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    endpoint_groups: list[dict[str, Any]] = field(default_factory=list)
    endpoint_group_summaries: list[dict[str, Any]] = field(default_factory=list)
    endpoint_group_samples: list[dict[str, Any]] = field(default_factory=list)
    candidate_requests: list[dict[str, Any]] = field(default_factory=list)
    selected_requests: list[dict[str, Any]] = field(default_factory=list)
    sequence_windows: list[dict[str, Any]] = field(default_factory=list)
    session_log_windows: list[dict[str, Any]] = field(default_factory=list)
    evidence_notes: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _extract_message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: list[str] = []
        for item in content:
            if isinstance(item, str):
                fragments.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    fragments.append(str(text))
        return "\n".join(fragment for fragment in fragments if fragment).strip()
    return str(content or "").strip()


def _parse_json_if_possible(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = str(value or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _iter_text_fragments(value: Any) -> list[str]:
    fragments: list[str] = []
    if value is None:
        return fragments
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, (list, tuple, set)):
        for item in value:
            fragments.extend(_iter_text_fragments(item))
        return fragments
    if isinstance(value, dict):
        if value.get("type") == "text" and "text" in value:
            return _iter_text_fragments(value.get("text"))

        preferred_keys = ("text", "content", "output", "result", "message", "artifact")
        for key in preferred_keys:
            if key in value:
                fragments.extend(_iter_text_fragments(value[key]))

        if fragments:
            return fragments
        return fragments

    text = getattr(value, "text", None)
    if text is not None:
        fragments.extend(_iter_text_fragments(text))

    content = getattr(value, "content", None)
    if content is not None:
        fragments.extend(_iter_text_fragments(content))

    if fragments:
        return fragments

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        fragments.extend(_iter_text_fragments(model_dump()))

    if fragments:
        return fragments
    return [str(value)]


def _extract_output_text(value: Any) -> str:
    fragments = [fragment.strip() for fragment in _iter_text_fragments(value) if str(fragment).strip()]
    return "\n".join(fragments).strip()


def _is_tool_wrapper_dict(value: dict[str, Any]) -> bool:
    if "content" not in value:
        return False
    return set(value.keys()).issubset({"content", "artifact", "isError", "status"})


def _is_text_block_list(value: list[Any]) -> bool:
    if not value:
        return False
    for item in value:
        if isinstance(item, str):
            continue
        if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
            continue
        if getattr(item, "text", None) is not None:
            continue
        return False
    return True


def _normalize_tool_result(value: Any) -> Any:
    if isinstance(value, tuple) and value:
        return _normalize_tool_result(value[0])
    if isinstance(value, list):
        if _is_text_block_list(value):
            return _parse_json_if_possible(_extract_output_text(value))
        return value
    if isinstance(value, dict):
        if _is_tool_wrapper_dict(value):
            return _parse_json_if_possible(_extract_output_text(value.get("content")))
        return value
    if isinstance(value, str):
        return _parse_json_if_possible(value)
    content = getattr(value, "content", None)
    if content is not None:
        if isinstance(content, list):
            return _parse_json_if_possible(_extract_output_text(content))
        return _parse_json_if_possible(content)
    return _parse_json_if_possible(str(value))


def _stringify_tool_result(value: Any) -> str:
    if isinstance(value, tuple) and value:
        text = _stringify_tool_result(value[0])
        if text:
            return text
        return _stringify_tool_result(value[1]) if len(value) > 1 else ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and _is_text_block_list(value):
        return _extract_output_text(value)
    if isinstance(value, dict) and _is_tool_wrapper_dict(value):
        return _extract_output_text(value.get("content"))
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return _extract_output_text(value)

    content = getattr(value, "content", None)
    if content is not None:
        if isinstance(content, list):
            return _extract_output_text(content)
        return str(content or "").strip()

    text = getattr(value, "text", None)
    if text is not None:
        return str(text or "").strip()

    return str(value or "").strip()


def _truncate_text(value: str, limit: int = MAX_TOOL_RESULT_EXCERPT) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if not normalized:
        return ""
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


async def _emit_tool_start(callbacks: list[Any] | None, name: str, args: dict[str, Any]) -> None:
    payload = json.dumps(args, ensure_ascii=False) if args else "{}"
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_start", None)
        if callable(handler):
            await handler({"name": name}, payload)


async def _emit_tool_end(callbacks: list[Any] | None, output: Any) -> None:
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_end", None)
        if callable(handler):
            await handler(output)


async def _emit_tool_error(callbacks: list[Any] | None, error: BaseException) -> None:
    for callback in callbacks or []:
        handler = getattr(callback, "on_tool_error", None)
        if callable(handler):
            await handler(error)


def _format_exception_excerpt(exc: BaseException) -> str:
    type_name = exc.__class__.__name__
    message = " ".join(str(exc).split()).strip()
    if not message or message == type_name:
        return type_name
    return f"{type_name}: {message}"


def _iter_exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    depth = 0
    while current is not None and depth < 6:
        chain.append(current)
        next_exc = current.__cause__
        if next_exc is None and not getattr(current, "__suppress_context__", False):
            next_exc = current.__context__
        current = next_exc
        depth += 1
    return chain


def _clear_latest_tool_name(callbacks: list[Any] | None) -> None:
    for callback in callbacks or []:
        handler = getattr(callback, "clear_latest_tool_name", None)
        if callable(handler):
            handler()
            continue
        for attr in ("latest_tool_name", "_latest_tool_name"):
            if hasattr(callback, attr):
                try:
                    setattr(callback, attr, "")
                except Exception:
                    pass


def _is_retryable_synthesis_error(exc: BaseException) -> bool:
    retryable_type_names = {"ConnectError", "ConnectTimeout", "ReadTimeout", "PoolTimeout", "TimeoutException"}
    for current in _iter_exception_chain(exc):
        if isinstance(current, NewAPIRequestError):
            return True
        if current.__class__.__name__ in retryable_type_names:
            return True
        message = str(current).lower()
        if any(keyword in message for keyword in ("connecterror", "connection reset", "connection refused", "readtimeout", "timed out", "temporarily unavailable")):
            return True
    return False


def _extract_latest_tool_name(callbacks: list[Any] | None) -> str:
    for callback in callbacks or []:
        getter = getattr(callback, "get_latest_tool_name", None)
        if callable(getter):
            name = str(getter() or "").strip()
            if name:
                return name
        name = str(getattr(callback, "latest_tool_name", "") or "").strip()
        if name:
            return name
    return ""


def _format_inline_values(values: list[Any] | None, *, limit: int = 5) -> str:
    normalized = [str(value or "").strip() for value in values or []]
    normalized = [value for value in normalized if value]
    if not normalized:
        return "无"
    return "、".join(normalized[:limit])


def _format_frequency_items(items: list[dict[str, Any]] | None, *, limit: int = 4) -> str:
    if not isinstance(items, list):
        return "无"
    rendered: list[str] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        value = str(item.get("value") or "").strip()
        count = item.get("count")
        if not value:
            continue
        rendered.append(f"{value}({count})" if count not in (None, "") else value)
    return "、".join(rendered) if rendered else "无"


def _build_structured_fallback_report(
    *,
    session_id: str,
    scratchpad: AnalysisScratchpad,
    error: BaseException,
) -> str:
    overview = scratchpad.dataset_overview or {}
    lines = [
        "【结构化回退报告】",
        f"- session_id: {session_id}",
        f"- 说明: 结构化工具采集已完成，但模型综合阶段连续重试后仍失败：{_format_exception_excerpt(error)}",
        "- 结论来源: 以下内容基于已收集的 scratchpad 自动整理，可直接继续人工复现或二次分析。",
        "",
        "## 数据集概览",
        f"- page_url: {str(overview.get('page_url') or '').strip() or '未知'}",
        f"- 请求规模: {overview.get('filtered_request_count') or overview.get('raw_request_count') or 0}",
        f"- first_party_hosts: {_format_inline_values(overview.get('first_party_hosts'), limit=6)}",
        f"- top_hosts: {_format_frequency_items(overview.get('top_hosts'), limit=5)}",
        "",
        "## 关键接口候选",
    ]

    if scratchpad.endpoint_groups:
        for item in scratchpad.endpoint_groups[:MAX_ENDPOINT_GROUPS]:
            lines.append(
                "- "
                f"{str(item.get('endpoint') or '').strip() or 'unknown endpoint'}"
                f" | count={item.get('count', 0)}"
                f" | auth={_format_frequency_items(item.get('auth_signal_flags'), limit=3)}"
                f" | interaction={_format_frequency_items(item.get('interaction_signal_flags'), limit=3)}"
            )
    else:
        lines.append("- 无")

    lines.extend(["", "## 最值得复现的请求"])
    if scratchpad.selected_requests:
        for item in scratchpad.selected_requests[:MAX_SELECTED_REQUESTS]:
            request = item.get("request") if isinstance(item.get("request"), dict) else {}
            lines.append(
                "- "
                f"{str(request.get('method') or '').strip() or 'UNKNOWN'} "
                f"{str(request.get('host') or '').strip()}{str(request.get('path') or '').strip()}"
                f" | status={request.get('status', 0)}"
                f" | query_keys={_format_inline_values(request.get('query_keys'), limit=6)}"
                f" | request_body_keys={_format_inline_values(request.get('request_body_keys'), limit=6)}"
                f" | response_body_keys={_format_inline_values(request.get('response_body_keys'), limit=6)}"
                f" | auth={_format_inline_values(request.get('auth_signal_flags'), limit=5)}"
            )
    else:
        lines.append("- 无")

    if scratchpad.sequence_windows:
        window = scratchpad.sequence_windows[0]
        returned = window.get("returned") if isinstance(window.get("returned"), list) else []
        sequence = []
        for item in returned:
            if not isinstance(item, dict):
                continue
            marker = "[anchor]" if item.get("is_anchor") else ""
            sequence.append(
                f"{str(item.get('method') or '').strip() or 'UNKNOWN'} {str(item.get('path') or '').strip() or '/'}{marker}"
            )
        lines.extend([
            "",
            "## 请求时序窗口",
            f"- {' -> '.join(sequence) if sequence else '无'}",
        ])

    return "\n".join(lines).strip()


def _format_agent_exception(exc: BaseException, callbacks: list[Any] | None = None) -> str:
    fragments: list[str] = []
    seen: set[str] = set()
    current: BaseException | None = exc
    depth = 0
    while current is not None and depth < 3:
        excerpt = _format_exception_excerpt(current)
        if excerpt and excerpt not in seen:
            fragments.append(excerpt)
            seen.add(excerpt)
        next_exc = current.__cause__
        if next_exc is None and not getattr(current, "__suppress_context__", False):
            next_exc = current.__context__
        current = next_exc
        depth += 1

    latest_tool = _extract_latest_tool_name(callbacks)
    detail = " <- ".join(fragment for fragment in fragments if fragment).strip() or exc.__class__.__name__
    if latest_tool and latest_tool not in detail:
        detail = f"{detail}（最近工具：{latest_tool}）"
    return detail


async def _invoke_tool(tool: BaseTool, args: dict[str, Any], callbacks: list[Any] | None = None) -> ToolInvocationResult:
    tool_name = str(getattr(tool, "name", "") or "").strip()
    await _emit_tool_start(callbacks, tool_name, args)
    try:
        result = await tool.ainvoke(args)
    except Exception as exc:
        await _emit_tool_error(callbacks, exc)
        raise
    await _emit_tool_end(callbacks, result)
    _clear_latest_tool_name(callbacks)
    raw_text = _stringify_tool_result(result)
    return ToolInvocationResult(
        name=str(getattr(tool, "name", "") or "").strip(),
        args=dict(args),
        normalized=_normalize_tool_result(result),
        raw_text=raw_text,
        raw_excerpt=_truncate_text(raw_text),
    )


def _tool_map(tools: list[BaseTool]) -> dict[str, BaseTool]:
    mapped: dict[str, BaseTool] = {}
    for tool in tools:
        name = str(getattr(tool, "name", "") or "").strip()
        if not name or name in mapped:
            continue
        mapped[name] = tool
    return mapped


def _supports_structured_flow(mapped_tools: dict[str, BaseTool]) -> bool:
    return STRUCTURED_REQUIRED_TOOL_NAMES.issubset(mapped_tools.keys())


def _extract_structured_flow_preference(
    analyse_prompt: str | None,
    *,
    prefer_structured_flow: bool | None = None,
) -> tuple[str, bool]:
    prompt = str(analyse_prompt or "")
    if prefer_structured_flow is not None:
        cleaned = prompt
        for token in STRUCTURED_FLOW_CONTROL_TOKENS:
            cleaned = cleaned.replace(token, "")
        return cleaned.strip(), prefer_structured_flow

    cleaned = prompt
    enabled = False
    lowered = prompt.lower()
    for token in STRUCTURED_FLOW_CONTROL_TOKENS:
        if token.lower() in lowered:
            enabled = True
            cleaned = cleaned.replace(token, "")
    return cleaned.strip(), enabled


def _take_freq_items(value: Any, limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        normalized = {
            "value": str(item.get("value") or "").strip(),
            "count": item.get("count", 0),
        }
        if not normalized["value"]:
            continue
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _take_dict_fields(value: Any, fields: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {field: value.get(field) for field in fields if field in value}


def _compress_overview(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    result = _take_dict_fields(
        payload,
        [
            "dataset_id",
            "page_url",
            "raw_request_count",
            "filtered_request_count",
            "index_available",
            "time_range",
            "first_party_hosts",
        ],
    )
    result["top_hosts"] = _take_freq_items(payload.get("top_hosts"), 5)
    result["methods"] = _take_freq_items(payload.get("methods"), 5)
    result["status_codes"] = _take_freq_items(payload.get("status_codes"), 5)
    result["mime_types"] = _take_freq_items(payload.get("mime_types"), 5)
    return result


def _compress_statistics(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    result = _take_dict_fields(
        payload,
        [
            "dataset_id",
            "total_requests",
            "unique_hosts",
            "unique_paths",
            "avg_duration_ms",
            "max_duration_ms",
        ],
    )
    result["top_endpoints"] = _take_freq_items(payload.get("top_endpoints"), 8)
    return result


def _compress_endpoint_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    endpoints = payload.get("endpoints")
    if not isinstance(endpoints, list):
        return []
    result: list[dict[str, Any]] = []
    for item in endpoints:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "endpoint": str(item.get("endpoint") or "").strip(),
                "method": str(item.get("method") or "").strip(),
                "host": str(item.get("host") or "").strip(),
                "normalized_path": str(item.get("normalized_path") or "").strip(),
                "count": item.get("count", 0),
                "schema_variants": item.get("schema_variants", 0),
                "auth_signal_flags": _take_freq_items(item.get("auth_signal_flags"), 4),
                "interaction_signal_flags": _take_freq_items(item.get("interaction_signal_flags"), 4),
                "sample_request_ids": list(item.get("sample_request_ids") or [])[:3],
            }
        )
    return [item for item in result if item["endpoint"]][:8]


def _compress_candidate_requests(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    ranked = payload.get("ranked_requests")
    if not isinstance(ranked, list):
        return []
    result: list[dict[str, Any]] = []
    for item in ranked:
        if not isinstance(item, dict):
            continue
        request = item.get("request") if isinstance(item.get("request"), dict) else {}
        result.append(
            {
                "endpoint": str(item.get("endpoint") or "").strip(),
                "score": item.get("score", 0),
                "reasons": list(item.get("reasons") or []),
                "request": {
                    "id": str(request.get("id") or "").strip(),
                    "method": str(request.get("method") or "").strip(),
                    "host": str(request.get("host") or "").strip(),
                    "path": str(request.get("path") or "").strip(),
                    "status": request.get("status", 0),
                    "auth_signal_flags": list(request.get("auth_signal_flags") or []),
                    "interaction_signal_flags": list(request.get("interaction_signal_flags") or []),
                    "error_signal_flags": list(request.get("error_signal_flags") or []),
                },
            }
        )
    return [item for item in result if item["request"]["id"]][:8]


def _compress_endpoint_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "endpoint": str(payload.get("endpoint") or summary.get("endpoint") or "").strip(),
        "method": str(summary.get("method") or "").strip(),
        "host": str(summary.get("host") or "").strip(),
        "normalized_path": str(summary.get("normalized_path") or "").strip(),
        "total_samples": summary.get("total_samples", 0),
        "time_range": summary.get("time_range", {}),
        "status_codes": _take_freq_items(summary.get("status_codes"), 5),
        "mime_types": _take_freq_items(summary.get("mime_types"), 5),
        "common_query_keys": _take_freq_items(summary.get("common_query_keys"), 5),
        "common_request_body_keys": _take_freq_items(summary.get("common_request_body_keys"), 6),
        "common_response_body_keys": _take_freq_items(summary.get("common_response_body_keys"), 6),
        "auth_signal_flags": _take_freq_items(summary.get("auth_signal_flags"), 5),
        "interaction_signal_flags": _take_freq_items(summary.get("interaction_signal_flags"), 5),
        "representative_request_ids": list(summary.get("representative_request_ids") or [])[:4],
    }


def _compress_group_samples(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    samples = payload.get("samples")
    if not isinstance(samples, list):
        samples = []
    normalized_samples = []
    for item in samples:
        if not isinstance(item, dict):
            continue
        normalized_samples.append(
            {
                "id": str(item.get("id") or "").strip(),
                "method": str(item.get("method") or "").strip(),
                "host": str(item.get("host") or "").strip(),
                "path": str(item.get("path") or "").strip(),
                "status": item.get("status", 0),
                "request_schema_hash": str(item.get("request_schema_hash") or "").strip(),
                "response_schema_hash": str(item.get("response_schema_hash") or "").strip(),
                "auth_signal_flags": list(item.get("auth_signal_flags") or []),
                "interaction_signal_flags": list(item.get("interaction_signal_flags") or []),
                "error_signal_flags": list(item.get("error_signal_flags") or []),
            }
        )
    return {
        "endpoint": str(payload.get("endpoint") or "").strip(),
        "strategy": str(payload.get("strategy") or "").strip(),
        "samples": [item for item in normalized_samples if item["id"]][:4],
    }


def _compress_request_detail(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    request = payload.get("request") if isinstance(payload.get("request"), dict) else {}
    return {
        "detail_level": str(payload.get("detail_level") or "").strip(),
        "request": {
            "id": str(request.get("id") or "").strip(),
            "method": str(request.get("method") or "").strip(),
            "host": str(request.get("host") or "").strip(),
            "path": str(request.get("path") or "").strip(),
            "status": request.get("status", 0),
            "mime_type": str(request.get("mime_type") or "").strip(),
            "query_keys": list(request.get("query_keys") or []),
            "request_body_keys": list(request.get("request_body_keys") or []),
            "response_body_keys": list(request.get("response_body_keys") or []),
            "request_header_keys": list(request.get("request_header_keys") or []),
            "response_header_keys": list(request.get("response_header_keys") or []),
            "auth_signal_flags": list(request.get("auth_signal_flags") or []),
            "interaction_signal_flags": list(request.get("interaction_signal_flags") or []),
            "error_signal_flags": list(request.get("error_signal_flags") or []),
            "request_body_preview": str(request.get("request_body_preview") or "")[:400],
            "response_body_preview": str(request.get("response_body_preview") or "")[:400],
        },
    }


def _compress_sequence_window(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    returned = payload.get("returned")
    if not isinstance(returned, list):
        returned = []
    return {
        "anchor_request_id": str(payload.get("anchor_request_id") or "").strip(),
        "returned": [
            {
                "id": str(item.get("id") or "").strip(),
                "method": str(item.get("method") or "").strip(),
                "host": str(item.get("host") or "").strip(),
                "path": str(item.get("path") or "").strip(),
                "status": item.get("status", 0),
                "is_anchor": bool(item.get("is_anchor")),
            }
            for item in returned
            if isinstance(item, dict)
        ][:9],
    }


def _compress_session_log_window(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"raw": str(payload)}
    returned = payload.get("returned")
    if not isinstance(returned, list):
        returned = []
    return {
        "session_id": str(payload.get("session_id") or "").strip(),
        "next_cursor": payload.get("next_cursor"),
        "returned": returned[:8],
    }


def _tool_excerpt_or_empty(result: ToolInvocationResult) -> str:
    return result.raw_excerpt or "（空响应）"


def _build_tool_diagnostics(*results: ToolInvocationResult | None) -> str:
    parts: list[str] = []
    for result in results:
        if result is None:
            continue
        name = str(result.name or "").strip() or "unknown_tool"
        parts.append(f"{name}: {_tool_excerpt_or_empty(result)}")
    return " | ".join(parts)


def _extract_request_count(overview: dict[str, Any]) -> int:
    for field in ("filtered_request_count", "raw_request_count"):
        value = overview.get(field)
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0:
            return numeric
    return 0


def _validate_dataset_overview(
    overview: dict[str, Any],
    *,
    result: ToolInvocationResult,
) -> None:
    dataset_id = str(overview.get("dataset_id") or "").strip()
    request_count = _extract_request_count(overview)
    if dataset_id and request_count > 0:
        return
    raise AnalysisValidationError(
        "tool_returned_empty_payload: get_dataset_overview 返回异常空结果或缺少关键字段，"
        f"未识别到有效 dataset_id / request_count。工具返回摘要：{_tool_excerpt_or_empty(result)}"
    )


def _validate_candidate_coverage(
    overview: dict[str, Any],
    endpoint_groups: list[dict[str, Any]],
    candidate_requests: list[dict[str, Any]],
    *,
    endpoint_result: ToolInvocationResult,
    candidate_result: ToolInvocationResult,
) -> None:
    if not bool(overview.get("index_available")):
        return
    if endpoint_groups or candidate_requests:
        return
    raise AnalysisValidationError(
        "tool_payload_shape_invalid: 当前会话已声明 index_available=true，但 extract_api_endpoints "
        "与 rank_candidate_requests 都未返回任何可用结果。"
        f"诊断：{_build_tool_diagnostics(endpoint_result, candidate_result)}"
    )


def _validate_selected_requests(
    selected_requests: list[dict[str, Any]],
    *,
    overview: dict[str, Any],
    candidate_result: ToolInvocationResult,
    sample_results: list[ToolInvocationResult],
) -> None:
    if selected_requests:
        return
    reason = (
        "dataset_without_index"
        if not bool(overview.get("index_available"))
        else "tool_payload_shape_invalid"
    )
    diagnostics = _build_tool_diagnostics(candidate_result, *sample_results[:MAX_ENDPOINT_GROUPS])
    raise AnalysisValidationError(
        f"{reason}: 结构化分析未能锁定任何最终 request_id，无法形成可靠逆向结论。诊断：{diagnostics}"
    )


def _unique_nonempty(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        current = str(value or "").strip()
        if not current or current in seen:
            continue
        seen.add(current)
        result.append(current)
    return result


def _select_endpoint_ids(
    endpoint_groups: list[dict[str, Any]],
    candidate_requests: list[dict[str, Any]],
) -> list[str]:
    from_candidates = [item.get("endpoint", "") for item in candidate_requests]
    from_groups = [item.get("endpoint", "") for item in endpoint_groups]
    return _unique_nonempty(from_candidates + from_groups)[:MAX_ENDPOINT_GROUPS]


def _select_request_ids(
    candidate_requests: list[dict[str, Any]],
    group_samples: list[dict[str, Any]],
) -> list[str]:
    ranked = [((item.get("request") or {}).get("id", "")) for item in candidate_requests]
    sampled = [
        sample.get("id", "")
        for group in group_samples
        for sample in (group.get("samples") or [])
        if isinstance(sample, dict)
    ]
    return _unique_nonempty(ranked + sampled)[:MAX_SELECTED_REQUESTS]


async def _call_named_tool(
    tool_lookup: dict[str, BaseTool],
    name: str,
    args: dict[str, Any],
    callbacks: list[Any] | None = None,
) -> Any:
    tool = tool_lookup.get(name)
    if tool is None:
        raise KeyError(f"缺少工具: {name}")
    return await _invoke_tool(tool, args, callbacks=callbacks)


async def _run_structured_analysis(
    *,
    session_id: str,
    tool_lookup: dict[str, BaseTool],
    analyse_prompt: str,
    runtime_llm: Any,
    callbacks: list[Any] | None = None,
) -> str:
    dataset_id = f"redis:{session_id}"
    scratchpad = AnalysisScratchpad(session_id=session_id, dataset_id=dataset_id)

    overview_result = await _call_named_tool(tool_lookup, "get_dataset_overview", {"dataset_id": dataset_id}, callbacks=callbacks)
    scratchpad.dataset_overview = _compress_overview(overview_result.normalized)
    _validate_dataset_overview(scratchpad.dataset_overview, result=overview_result)

    if "get_statistics" in tool_lookup:
        statistics_result = await _call_named_tool(tool_lookup, "get_statistics", {"dataset_id": dataset_id}, callbacks=callbacks)
        scratchpad.statistics = _compress_statistics(statistics_result.normalized)

    endpoint_groups_result = await _call_named_tool(
        tool_lookup,
        "extract_api_endpoints",
        {"dataset_id": dataset_id, "limit": 20},
        callbacks=callbacks,
    )
    scratchpad.endpoint_groups = _compress_endpoint_list(endpoint_groups_result.normalized)

    candidate_requests_result = await _call_named_tool(
        tool_lookup,
        "rank_candidate_requests",
        {"dataset_id": dataset_id, "limit": 8},
        callbacks=callbacks,
    )
    scratchpad.candidate_requests = _compress_candidate_requests(candidate_requests_result.normalized)
    _validate_candidate_coverage(
        scratchpad.dataset_overview,
        scratchpad.endpoint_groups,
        scratchpad.candidate_requests,
        endpoint_result=endpoint_groups_result,
        candidate_result=candidate_requests_result,
    )

    selected_endpoint_ids = _select_endpoint_ids(scratchpad.endpoint_groups, scratchpad.candidate_requests)
    compressed_group_samples: list[dict[str, Any]] = []
    group_sample_results: list[ToolInvocationResult] = []
    for endpoint_id in selected_endpoint_ids:
        summary_result = await _call_named_tool(
            tool_lookup,
            "get_endpoint_group_summary",
            {"dataset_id": dataset_id, "endpoint": endpoint_id},
            callbacks=callbacks,
        )
        scratchpad.endpoint_group_summaries.append(_compress_endpoint_summary(summary_result.normalized))

        samples_result = await _call_named_tool(
            tool_lookup,
            "get_endpoint_group_samples",
            {
                "dataset_id": dataset_id,
                "endpoint": endpoint_id,
                "strategy": "diverse",
                "limit": 3,
            },
            callbacks=callbacks,
        )
        compressed_group_samples.append(_compress_group_samples(samples_result.normalized))
        group_sample_results.append(samples_result)

    scratchpad.endpoint_group_samples = compressed_group_samples

    selected_request_ids = _select_request_ids(scratchpad.candidate_requests, compressed_group_samples)
    for request_id in selected_request_ids:
        detail_result = await _call_named_tool(
            tool_lookup,
            "get_request_details",
            {
                "dataset_id": dataset_id,
                "request_id": request_id,
                "detail_level": "preview",
            },
            callbacks=callbacks,
        )
        scratchpad.selected_requests.append(_compress_request_detail(detail_result.normalized))

    _validate_selected_requests(
        scratchpad.selected_requests,
        overview=scratchpad.dataset_overview,
        candidate_result=candidate_requests_result,
        sample_results=group_sample_results,
    )

    if scratchpad.selected_requests and "get_request_sequence_window" in tool_lookup:
        anchor_request_id = ((scratchpad.selected_requests[0].get("request") or {}).get("id") or "").strip()
        if anchor_request_id:
            window_result = await _call_named_tool(
                tool_lookup,
                "get_request_sequence_window",
                {
                    "dataset_id": dataset_id,
                    "request_id": anchor_request_id,
                    "before": 3,
                    "after": 3,
                },
            )
            scratchpad.sequence_windows.append(_compress_sequence_window(window_result.normalized))

    synthesis_messages = [
        SystemMessage(
            content=(
                "你是一个低上下文逆向分析总结器。"
                "你只能基于提供的 scratchpad 输出结论，不要杜撰未出现的字段，不要复述大段原始日志。"
                "输出聚焦关键接口、鉴权方式、最值得复现的请求和简短复现建议。"
            )
        ),
        HumanMessage(
            content=(
                f"分析目标 session_id={session_id}。\n"
                f"以下是当前分析要求：\n{analyse_prompt.strip()}\n\n"
                f"以下是结构化 scratchpad：\n{scratchpad.to_json()}"
            )
        ),
    ]
    synthesis_error: BaseException | None = None
    for attempt in range(ANALYSIS_SYNTHESIS_MAX_RETRIES + 1):
        try:
            response = await runtime_llm.ainvoke(synthesis_messages)
            final_text = _extract_message_text(response)
            if final_text:
                return final_text
            return _build_structured_fallback_report(
                session_id=session_id,
                scratchpad=scratchpad,
                error=RuntimeError("模型返回空内容"),
            )
        except Exception as exc:
            synthesis_error = exc
            if not _is_retryable_synthesis_error(exc):
                raise
            if attempt >= ANALYSIS_SYNTHESIS_MAX_RETRIES:
                break
            await asyncio.sleep(ANALYSIS_SYNTHESIS_RETRY_BACKOFF_SECONDS * (attempt + 1))

    if synthesis_error is not None:
        return _build_structured_fallback_report(
            session_id=session_id,
            scratchpad=scratchpad,
            error=synthesis_error,
        )
    return scratchpad.to_json()


async def run_analysis_agent(
    session_id: str,
    tools: list[BaseTool],
    analyse_prompt: str | None = None,
    llm: Any | None = None,
    model_profile: dict | None = None,
    callbacks: list[Any] | None = None,
    agent_middleware: list[Any] | None = None,
    prefer_structured_flow: bool | None = None,
) -> AnalysisReport:
    """
    为指定 session 运行分析专家 Agent，读取 Redis 数据并生成分析报告。

    Args:
        session_id: Redis 中的会话 ID（如 session-1700000000000）
        tools:      由外部组装的工具列表（Redis 工具 + 可选 MCP 工具）

    Returns:
        AnalysisReport，包含分析结果
    """
    if llm is not None:
        runtime_llm = llm
    elif model_profile:
        runtime_llm = create_llm_from_profile(model_profile, temperature=0)
    else:
        runtime_llm = create_default_llm(temperature=0)

    prompt_template = analyse_prompt or DEFAULT_ANALYSE_PROMPT_TEMPLATE
    prompt_template, structured_flow_enabled = _extract_structured_flow_preference(
        prompt_template,
        prefer_structured_flow=prefer_structured_flow,
    )
    prompt = prompt_template.replace("{session_id}", session_id)
    mapped_tools = _tool_map(tools)

    try:
        if agent_middleware:
            agent = create_agent(runtime_llm, tools=tools, middleware=agent_middleware)
            invoke_kwargs = {"config": {"callbacks": callbacks}} if callbacks else {}
            result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]}, **invoke_kwargs)
            report_text = str(result.get("messages", [])[-1].content if result.get("messages") else "")
        elif structured_flow_enabled and _supports_structured_flow(mapped_tools):
            report_text = await _run_structured_analysis(
                session_id=session_id,
                tool_lookup=mapped_tools,
                analyse_prompt=prompt,
                runtime_llm=runtime_llm,
                callbacks=callbacks,
            )
        else:
            agent = create_react_agent(runtime_llm, tools)
            invoke_kwargs = {"config": {"callbacks": callbacks}} if callbacks else {}
            result = await agent.ainvoke({"messages": [("human", prompt)]}, **invoke_kwargs)
            report_text = str(result.get("messages", [])[-1].content if result.get("messages") else "")

        return AnalysisReport(
            session_id=session_id,
            report=report_text,
            success=True,
            cleanup_allowed=True,
        )

    except Exception as exc:
        return AnalysisReport(
            session_id=session_id,
            report="",
            success=False,
            error=_format_agent_exception(exc, callbacks=callbacks),
            cleanup_allowed=False,
        )


async def run_analysis_for_all_sessions(tools: list[BaseTool]) -> list[AnalysisReport]:
    from tools.redis_tool import ListSessionsTool

    list_tool = ListSessionsTool()
    session_ids_json = await list_tool._arun()
    session_ids: list[str] = json.loads(session_ids_json)

    reports = []
    for session_id in session_ids:
        report = await run_analysis_agent(session_id, tools)
        reports.append(report)
    return reports
