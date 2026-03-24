"""
Browser Agent：使用注入的 MCP 工具列表访问指定 URL，数据自动流向 Redis。

工具列表由外部（main.py）通过 ToolRegistry 选取后传入，
本模块完全不感知 MCP、npx 或子进程的存在。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from agents.browser_embedded_stripe_payment import (
    _LIGHTWEIGHT_SURFACE_PROBE_SCRIPT,
    _invoke_tool,
    _parse_probe_result,
    _surface_probe_fields_ready,
    _surface_probe_gateway_ready,
    extract_session_id,
    should_use_embedded_stripe_payment_flow,
)
from agents.browser_wait_hooks import WaitHookResult, wait_for_hooks
from agents.browser_tool_runtime import DisableParallelToolCallsMiddleware, bind_browser_tools_serially
from services.llm_factory import create_default_llm, create_llm_from_profile


BROWSER_AGENT_REQUEST_TIMEOUT_SECONDS = 60.0
BROWSER_AGENT_SURFACE_WAIT_TIMEOUT_SECONDS = 15.0
BROWSER_AGENT_SURFACE_WAIT_POLL_INTERVAL_SECONDS = 1.5
_DONATION_SURFACE_HINT_PATTERN = re.compile(r"donat|payment|checkout|card|gift|giving", re.IGNORECASE)
_PAYMENT_SURFACE_SIGNAL_KEYS = (
    "hasCardNumber",
    "hasExpiry",
    "hasSecurity",
    "hasCountry",
    "hasZip",
    "hasSubmit",
    "hasStripeGateway",
)


@dataclass
class BrowserPreparedPage:
    note: str
    session_id: str | None
    wait_result: WaitHookResult[dict[str, Any]] | None = None


@dataclass
class BrowserAgentResult:
    url: str
    session_id: str | None
    success: bool
    output: str
    error: str | None = None


def _iter_exception_chain(exc: BaseException, *, max_depth: int = 6) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    depth = 0
    while current is not None and depth < max_depth:
        chain.append(current)
        next_exc = current.__cause__
        if next_exc is None and not getattr(current, "__suppress_context__", False):
            next_exc = current.__context__
        current = next_exc
        depth += 1
    return chain


def _format_exception_chain(exc: BaseException) -> str:
    parts: list[str] = []
    for current in _iter_exception_chain(exc):
        name = current.__class__.__name__
        message = str(current).strip()
        if message and message != name:
            parts.append(f"{name}: {message}")
        else:
            parts.append(name)
    return " <- ".join(parts) or exc.__class__.__name__


def _has_tool(tools: list[BaseTool], name: str) -> bool:
    return any(str(getattr(tool, "name", "") or "").strip() == name for tool in tools)


def _should_wait_for_surface(url: str, payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    if not bool(current.get("hasIframe")):
        return False

    surface_signals = any(
        bool(current.get(key))
        for key in (
            "hasFirstName",
            "hasLastName",
            "hasEmail",
            "hasCardNumber",
            "hasExpiry",
            "hasSecurity",
            "hasCountry",
            "hasZip",
            "hasSubmit",
            "hasStripeGateway",
        )
    )
    if surface_signals:
        return True

    combined = " ".join(
        str(current.get(key) or "").strip()
        for key in ("pageTitle", "combinedText")
    )
    return bool(_DONATION_SURFACE_HINT_PATTERN.search(f"{url} {combined}"))


def _has_completion_gate_contract(browser_prompt: str | None) -> bool:
    return "[AUTO_REVERSE_COMPLETION_GATE]" in str(browser_prompt or "")


def _should_probe_surface(browser_prompt: str | None) -> bool:
    prompt_text = str(browser_prompt or "").strip()
    if not prompt_text:
        return False
    return _has_completion_gate_contract(prompt_text) or should_use_embedded_stripe_payment_flow(prompt_text)


def _has_payment_surface_wait_target(url: str, payload: dict[str, Any] | None) -> bool:
    current = payload or {}
    if any(bool(current.get(key)) for key in _PAYMENT_SURFACE_SIGNAL_KEYS):
        return True

    combined = " ".join(
        str(current.get(key) or "").strip()
        for key in ("pageTitle", "combinedText")
    )
    return bool(_DONATION_SURFACE_HINT_PATTERN.search(f"{url} {combined}"))


def _should_use_surface_wait(
    url: str,
    browser_prompt: str | None,
    payload: dict[str, Any] | None,
) -> bool:
    if not _should_probe_surface(browser_prompt):
        return False
    if not _should_wait_for_surface(url, payload):
        return False
    return _has_payment_surface_wait_target(url, payload)


def _build_prepared_page_note(
    url: str,
    wait_result: WaitHookResult[dict[str, Any]] | None,
    *,
    did_surface_probe: bool,
) -> str:
    lines = [
        "当前浏览器已经打开目标页面，并完成了轻量页面预热。" if did_surface_probe else "当前浏览器已经打开目标页面。",
        f"目标 URL：{url}",
    ]
    if wait_result is not None:
        lines.extend(
            [
                f"surface wait 命中：{wait_result.matched_hook or 'timeout'}",
                f"surface wait 耗时：{wait_result.elapsed_seconds:.1f}s",
                f"surface wait 轮询次数：{wait_result.attempts}",
            ]
        )
    lines.extend(
        [
            "直接从当前已打开页面开始。",
            "优先调用 browser_snapshot 获取当前最新 ref，再继续后续点击、输入和提交。",
            "除非页面明显失效，请不要重新打开或整页刷新该 URL。",
        ]
    )
    return "\n".join(lines)


async def _prepare_browser_page(
    url: str,
    tools: list[BaseTool],
    *,
    browser_prompt: str | None = None,
    callbacks: list[Any] | None = None,
) -> BrowserPreparedPage | None:
    if not _has_tool(tools, "browser_navigate"):
        return None

    session_id: str | None = None

    def remember_session(value: Any) -> None:
        nonlocal session_id
        session_id = session_id or extract_session_id(value)

    try:
        navigate_text = await _invoke_tool(tools, "browser_navigate", {"url": url}, callbacks=callbacks)
        remember_session(navigate_text)

        wait_result: WaitHookResult[dict[str, Any]] | None = None
        did_surface_probe = False
        if _should_probe_surface(browser_prompt) and _has_tool(tools, "browser_evaluate"):
            did_surface_probe = True
            probe_text = await _invoke_tool(
                tools,
                "browser_evaluate",
                {"function": _LIGHTWEIGHT_SURFACE_PROBE_SCRIPT},
                callbacks=callbacks,
            )
            remember_session(probe_text)
            initial_payload = _parse_probe_result(probe_text) or {}

            if _should_use_surface_wait(url, browser_prompt, initial_payload):
                async def probe_getter() -> dict[str, Any]:
                    current_probe = await _invoke_tool(
                        tools,
                        "browser_evaluate",
                        {"function": _LIGHTWEIGHT_SURFACE_PROBE_SCRIPT},
                        callbacks=callbacks,
                    )
                    remember_session(current_probe)
                    return _parse_probe_result(current_probe) or {}

                wait_result = await wait_for_hooks(
                    probe_getter,
                    [
                        ("payment_fields_visible", _surface_probe_fields_ready),
                        ("payment_gateway_visible", _surface_probe_gateway_ready),
                    ],
                    timeout_seconds=BROWSER_AGENT_SURFACE_WAIT_TIMEOUT_SECONDS,
                    poll_interval_seconds=BROWSER_AGENT_SURFACE_WAIT_POLL_INTERVAL_SECONDS,
                )

            if _has_tool(tools, "browser_snapshot"):
                snapshot_text = await _invoke_tool(tools, "browser_snapshot", callbacks=callbacks)
                remember_session(snapshot_text)

        return BrowserPreparedPage(
            note=_build_prepared_page_note(url, wait_result, did_surface_probe=did_surface_probe),
            session_id=session_id,
            wait_result=wait_result,
        )
    except Exception:
        return None


def _create_runtime_llm(
    *,
    llm: Any | None = None,
    model_profile: dict[str, Any] | None = None,
) -> Any:
    if llm is not None:
        return llm
    if model_profile:
        return create_llm_from_profile(
            model_profile,
            temperature=0,
            request_timeout=BROWSER_AGENT_REQUEST_TIMEOUT_SECONDS,
        )
    return create_default_llm(
        temperature=0,
        request_timeout=BROWSER_AGENT_REQUEST_TIMEOUT_SECONDS,
    )


async def run_browser_agent(
    url: str,
    tools: list[BaseTool],
    browser_system_prompt: str | None = None,
    browser_prompt: str | None = None,
    llm: Any | None = None,
    model_profile: dict | None = None,
    callbacks: list[Any] | None = None,
    agent_middleware: list[Any] | None = None,
) -> BrowserAgentResult:
    """
    为单个 URL 运行 Browser Agent。

    session 数据（操作日志 + 网络数据包）由 MCP 工具自动写入 Redis，
    无需本模块额外处理。

    Args:
        url:   要访问的目标网址
        tools: 由 ToolRegistry.get_tools() 选取的 LangChain 工具列表

    Returns:
        BrowserAgentResult，包含运行结果
    """
    runtime_llm = _create_runtime_llm(llm=llm, model_profile=model_profile)
    serial_runtime_llm = bind_browser_tools_serially(runtime_llm, tools)

    prompt = browser_prompt or "请访问 {url}，完成页面加载与关键要素采集。"
    prompt = prompt.replace("{url}", url)

    prepared_page = await _prepare_browser_page(url, tools, browser_prompt=browser_prompt, callbacks=callbacks)
    if prepared_page is not None:
        prompt = f"{prepared_page.note}\n\n原始任务要求：\n{prompt}"

    if agent_middleware:
        effective_middleware = [*agent_middleware, DisableParallelToolCallsMiddleware()]
        agent = create_agent(
            runtime_llm,
            tools=tools,
            system_prompt=browser_system_prompt.strip() if browser_system_prompt and browser_system_prompt.strip() else None,
            middleware=effective_middleware,
        )
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
    else:
        agent = create_react_agent(serial_runtime_llm, tools)
        messages = []
        if browser_system_prompt and browser_system_prompt.strip():
            messages.append(("system", browser_system_prompt.strip()))
        messages.append(("human", prompt))

    try:
        invoke_kwargs = {"config": {"callbacks": callbacks}} if callbacks else {}
        result = await agent.ainvoke({"messages": messages}, **invoke_kwargs)
        messages = result.get("messages", [])
        output = str(messages[-1].content if messages else "")
        session_id = extract_session_id(messages, output, result) or (prepared_page.session_id if prepared_page else None)
        return BrowserAgentResult(
            url=url,
            session_id=session_id,
            success=True,
            output=output,
        )

    except Exception as exc:
        error_text = _format_exception_chain(exc)
        return BrowserAgentResult(
            url=url,
            session_id=None,
            success=False,
            output="",
            error=error_text,
        )
