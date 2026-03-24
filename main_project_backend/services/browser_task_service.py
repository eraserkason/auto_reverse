from __future__ import annotations

import asyncio
import contextlib
import copy
import json
import re
import uuid
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sqlalchemy.orm import Session

from models.user import User
from prompts.playwright_standalone import PLAYWRIGHT_BROWSER_TASK_SYSTEM_PROMPT
from schemas.browser_task import BrowserTaskSessionStateResponse
from services import config_service
from services.llm_factory import create_llm_from_profile
from tools.mcp_tool import load_browser_task_playwright_config
from tools.official_skills_runtime import official_skills_runtime
from agents.browser_tool_runtime import DisableParallelToolCallsMiddleware, bind_browser_tools_serially
from tools.skill_registry import SkillRegistry
from tools.tool_registry import apply_runtime_tool_defaults


PAGE_URL_PATTERN = re.compile(r"- Page URL: (.+)")
PAGE_TITLE_PATTERN = re.compile(r"- Page Title: (.*)")
OPEN_TAB_PATTERN = re.compile(r"^- \d+:(?: \(current\))? \[(.*)\] \((.*)\)$")
PLAYWRIGHT_DISABLED_FLAGS = {"--save-session", "--log-requests", "--log-session-id"}
SSE_KEEPALIVE_SECONDS = 15.0
BROWSER_TASK_REQUEST_TIMEOUT_SECONDS = 60.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime | None = None) -> str:
    return (value or _utcnow()).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(jsonable_encoder(value), ensure_ascii=False)


def _clean_text(value: Any, *, limit: int = 240) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    compact = " ".join(text.split())
    return compact[:limit].rstrip()


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
        preferred_keys = ("text", "content", "output", "result", "message", "artifact")
        seen_keys: set[str] = set()
        for key in preferred_keys:
            if key in value:
                fragments.extend(_iter_text_fragments(value[key]))
                seen_keys.add(key)
        for key, item in value.items():
            if key in seen_keys:
                continue
            fragments.extend(_iter_text_fragments(item))
        return fragments

    content = getattr(value, "content", None)
    if content is not None:
        fragments.extend(_iter_text_fragments(content))

    additional_kwargs = getattr(value, "additional_kwargs", None)
    if additional_kwargs:
        fragments.extend(_iter_text_fragments(additional_kwargs))

    tool_calls = getattr(value, "tool_calls", None)
    if tool_calls:
        fragments.extend(_iter_text_fragments(tool_calls))

    if fragments:
        return fragments
    return [str(value)]


def _extract_output_text(value: Any) -> str:
    fragments = [fragment.strip() for fragment in _iter_text_fragments(value) if str(fragment).strip()]
    return "\n".join(fragments).strip()


def _extract_agent_output(result: dict[str, Any]) -> str:
    messages = result.get("messages", [])
    if messages:
        return _extract_output_text(messages[-1])
    return _extract_output_text(result)


def _filter_playwright_args(args: list[str]) -> list[str]:
    filtered: list[str] = []
    for item in args:
        current = str(item)
        if current in PLAYWRIGHT_DISABLED_FLAGS:
            continue
        filtered.append(current)
    return filtered


def _build_pure_playwright_params() -> StdioServerParameters:
    params = load_browser_task_playwright_config()
    return StdioServerParameters(
        command=params.command,
        args=list(params.args or []),
        env=dict(params.env or {}),
    )


@dataclass
class BrowserTaskSessionMessage:
    id: str
    role: str
    content: str
    status: str
    created_at: datetime

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class _PurePlaywrightRuntime:
    def __init__(self) -> None:
        self._stack: AsyncExitStack | None = None
        self._tools: list[BaseTool] = []

    async def start(self) -> list[BaseTool]:
        if self._stack is not None:
            return self._tools

        params = _build_pure_playwright_params()
        stack = AsyncExitStack()
        await stack.__aenter__()
        try:
            read, write = await stack.enter_async_context(stdio_client(params))
            session: ClientSession = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._tools = apply_runtime_tool_defaults(await load_mcp_tools(session))
        except Exception:
            await stack.aclose()
            raise

        self._stack = stack
        return self._tools

    async def close(self) -> None:
        if self._stack is None:
            return
        stack = self._stack
        self._stack = None
        self._tools = []
        await stack.aclose()

    def tools(self) -> list[BaseTool]:
        return list(self._tools)


class _BrowserTaskCallbackHandler(AsyncCallbackHandler):
    def __init__(
        self,
        session: BrowserTaskSession,
        *,
        assistant_message_id: str | None,
        stream_text: bool,
    ) -> None:
        super().__init__()
        self._session = session
        self._assistant_message_id = assistant_message_id
        self._stream_text = stream_text

    async def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        name = str(serialized.get("name") or serialized.get("id") or "tool").strip()
        await self._session.note_tool_started(name, input_str)

    async def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
        await self._session.note_tool_finished(output)

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        await self._session.emit("tool.finished", {"ok": False, "summary": str(error)})

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        if not self._stream_text or not self._assistant_message_id:
            return
        chunk = kwargs.get("chunk")
        if isinstance(chunk, AIMessageChunk):
            tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
            if tool_call_chunks:
                return
        if token == "":
            return
        await self._session.note_assistant_delta(self._assistant_message_id, token)
        await self._session.emit(
            "assistant.delta",
            {
                "message_id": self._assistant_message_id,
                "delta": token,
            },
        )


class BrowserTaskSession:
    def __init__(
        self,
        *,
        owner_id: int,
        model_profile: dict[str, Any],
        selected_skills: list[str],
        start_url: str | None,
        browser_system_prompt: str,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.model_profile = copy.deepcopy(model_profile)
        self.selected_skills = list(selected_skills)
        self.start_url = str(start_url or "").strip() or None
        self.browser_system_prompt = browser_system_prompt.strip()
        self.status = "idle"
        self.current_url: str | None = None
        self.page_title: str | None = None
        self.tab_count = 0
        self.last_tool_name: str | None = None
        self.last_tool_summary: str | None = None
        self.created_at = _utcnow()
        self.updated_at = self.created_at

        self._messages: list[BrowserTaskSessionMessage] = []
        self._events: list[tuple[str, dict[str, Any]]] = []
        self._condition = asyncio.Condition()
        self._closed = False
        self._stop_requested = False
        self._skill_registry = SkillRegistry()
        self._active_task: asyncio.Task[Any] | None = None
        self._run_lock = asyncio.Lock()
        self._runtime = _PurePlaywrightRuntime()
        self._run_last_tool_name: str | None = None

    @staticmethod
    def _consume_background_task_result(task: asyncio.Task[Any]) -> None:
        with contextlib.suppress(asyncio.CancelledError, Exception):
            task.exception()

    def _start_background_task(self, coro: Any) -> None:
        task = asyncio.create_task(coro)
        task.add_done_callback(self._consume_background_task_result)
        self._active_task = task

    def state_payload(self) -> dict[str, Any]:
        return BrowserTaskSessionStateResponse(
            session_id=self.id,
            status=self.status,
            start_url=self.start_url,
            current_url=self.current_url,
            page_title=self.page_title,
            tab_count=self.tab_count,
            last_tool_name=self.last_tool_name,
            last_tool_summary=self.last_tool_summary,
            message_count=len(self._messages),
            created_at=self.created_at,
            updated_at=self.updated_at,
        ).model_dump(mode="json")

    def events_count(self) -> int:
        return len(self._events)

    async def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        async with self._condition:
            enriched = {"session_id": self.id, "timestamp": _isoformat(), **payload}
            self._events.append((event_name, enriched))
            self._condition.notify_all()

    async def emit_state(self) -> None:
        await self.emit("session.state", {"state": self.state_payload()})

    async def append_message(
        self,
        role: str,
        content: str,
        *,
        status_text: str = "done",
        message_id: str | None = None,
    ) -> BrowserTaskSessionMessage:
        message = BrowserTaskSessionMessage(
            id=message_id or str(uuid.uuid4()),
            role=role,
            content=content,
            status=status_text,
            created_at=_utcnow(),
        )
        self._messages.append(message)
        self.updated_at = _utcnow()
        return message

    def _find_message(self, message_id: str | None) -> BrowserTaskSessionMessage | None:
        if not message_id:
            return None
        for message in reversed(self._messages):
            if message.id == message_id:
                return message
        return None

    async def note_assistant_delta(self, message_id: str, delta: str) -> None:
        message = self._find_message(message_id)
        if message is None:
            message = await self.append_message("assistant", "", status_text="streaming", message_id=message_id)
        message.content = f"{message.content}{delta}"
        message.status = "streaming"
        self.updated_at = _utcnow()

    async def finalize_assistant_message(
        self,
        message_id: str | None,
        *,
        content: str | None = None,
        status_text: str,
    ) -> BrowserTaskSessionMessage | None:
        if not message_id:
            return None
        message = self._find_message(message_id)
        next_content = content
        if message is None:
            if not (next_content or "").strip():
                return None
            message = await self.append_message("assistant", next_content or "", status_text=status_text, message_id=message_id)
        else:
            if next_content is not None:
                message.content = next_content
            message.status = status_text
            self.updated_at = _utcnow()
        await self.emit("assistant.message", message.to_payload())
        await self.emit_state()
        return message

    async def note_tool_started(self, name: str, input_text: str) -> None:
        self.last_tool_name = name
        self._run_last_tool_name = name
        self.last_tool_summary = _clean_text(input_text, limit=180) or "执行中"
        self.updated_at = _utcnow()
        await self.emit("tool.started", {"tool_name": name, "input": _clean_text(input_text, limit=500)})
        await self.emit_state()

    async def note_tool_finished(self, output: Any) -> None:
        summary = _clean_text(_extract_output_text(output), limit=220) or "已完成"
        self.last_tool_summary = summary
        self.updated_at = _utcnow()
        await self.emit("tool.finished", {"tool_name": self.last_tool_name, "ok": True, "summary": summary})
        await self.emit_state()

    async def _ensure_runtime_tools(self, runtime: _PurePlaywrightRuntime) -> list[BaseTool]:
        return apply_runtime_tool_defaults(await runtime.start())

    async def _invoke_playwright_tool(
        self,
        runtime: _PurePlaywrightRuntime,
        name: str,
        args: dict[str, Any] | None = None,
    ) -> str:
        for tool in runtime.tools():
            tool_name = getattr(tool, "name", "").strip()
            if tool_name != name:
                continue
            result = await tool.ainvoke(args or {})
            return _extract_output_text(result)
        return ""

    async def _sync_browser_state(self, runtime: _PurePlaywrightRuntime) -> None:
        tab_list_text = await self._invoke_playwright_tool(runtime, "browser_tab_list")
        snapshot_text = await self._invoke_playwright_tool(runtime, "browser_snapshot")

        tab_count = 0
        current_url: str | None = None
        page_title: str | None = None

        for line in tab_list_text.splitlines():
            match = OPEN_TAB_PATTERN.match(line.strip())
            if not match:
                continue
            tab_count += 1
            title, url = match.groups()
            if "(current)" in line or current_url is None:
                page_title = title or page_title
                current_url = url or current_url

        url_match = PAGE_URL_PATTERN.search(snapshot_text)
        title_match = PAGE_TITLE_PATTERN.search(snapshot_text)
        if url_match:
            current_url = url_match.group(1).strip()
        if title_match:
            page_title = title_match.group(1).strip()

        self.tab_count = tab_count
        self.current_url = current_url
        self.page_title = page_title
        self.updated_at = _utcnow()
        await self.emit_state()

    async def _refresh_browser_state_after_run(self, runtime: _PurePlaywrightRuntime) -> None:
        if self._run_last_tool_name == "browser_close":
            self.tab_count = 0
            self.current_url = None
            self.page_title = None
            self.updated_at = _utcnow()
            await self.emit_state()
            return
        await self._sync_browser_state(runtime)

    def _build_agent_messages(self, content: str) -> list[tuple[str, str]]:
        messages: list[tuple[str, str]] = []
        if self.browser_system_prompt:
            messages.append(("system", self.browser_system_prompt))
        messages.append(("human", content))
        return messages

    def _create_runtime_llm(self, *, stream_text: bool) -> Any:
        return create_llm_from_profile(
            self.model_profile,
            temperature=0,
            streaming=stream_text,
            request_timeout=BROWSER_TASK_REQUEST_TIMEOUT_SECONDS,
        )

    async def _run_agent_turn(
        self,
        *,
        content: str,
        run_kind: str,
        emit_user_message: bool,
        stream_text: bool,
        user_message_id: str | None = None,
    ) -> None:
        async with self._run_lock:
            runtime = self._runtime
            assistant_message_id = str(uuid.uuid4()) if stream_text and run_kind != "bootstrap" else None
            self._run_last_tool_name = None
            try:
                with official_skills_runtime(self._skill_registry, self.selected_skills) as skills_runtime:
                    tools = await self._ensure_runtime_tools(runtime)
                    self.status = "bootstrapping" if run_kind == "bootstrap" else "running"
                    self.updated_at = _utcnow()
                    await self.emit("run.started", {"kind": run_kind, "message_id": user_message_id})
                    await self.emit_state()

                    if emit_user_message:
                        user_message = await self.append_message("user", content, message_id=user_message_id)
                        user_message_id = user_message.id
                        await self.emit("message.user", user_message.to_payload())
                        await self.emit_state()

                    callback_handler = _BrowserTaskCallbackHandler(
                        self,
                        assistant_message_id=assistant_message_id,
                        stream_text=stream_text,
                    )
                    llm = self._create_runtime_llm(stream_text=stream_text)
                    serial_llm = bind_browser_tools_serially(llm, tools)
                    if skills_runtime is not None:
                        agent = create_agent(
                            llm,
                            tools=tools,
                            system_prompt=self.browser_system_prompt or None,
                            middleware=[*list(skills_runtime.middleware), DisableParallelToolCallsMiddleware()],
                        )
                        result = await agent.ainvoke(
                            {"messages": [{"role": "user", "content": content}]},
                            config={"callbacks": [callback_handler]},
                        )
                    else:
                        agent = create_react_agent(serial_llm, tools)
                        result = await agent.ainvoke(
                            {"messages": self._build_agent_messages(content)},
                            config={"callbacks": [callback_handler]},
                        )
                output = _extract_agent_output(result)

                if run_kind != "bootstrap":
                    await self.finalize_assistant_message(
                        assistant_message_id or str(uuid.uuid4()),
                        content=output,
                        status_text="done",
                    )

                await self._refresh_browser_state_after_run(runtime)
                self.status = "ready"
                self.updated_at = _utcnow()
                await self.emit("run.completed", {"kind": run_kind, "message_id": user_message_id})
                await self.emit_state()
            except asyncio.CancelledError:
                with contextlib.suppress(Exception):
                    await self._refresh_browser_state_after_run(runtime)
                if self._stop_requested and not self._closed:
                    await self.finalize_assistant_message(assistant_message_id, status_text="stopped")
                    self.status = "ready"
                    self.updated_at = _utcnow()
                    await self.emit(
                        "run.stopped",
                        {
                            "kind": run_kind,
                            "message_id": user_message_id,
                            "assistant_message_id": assistant_message_id,
                            "summary": "当前任务已停止，浏览器现场继续保留。",
                        },
                    )
                    await self.emit_state()
                raise
            except Exception as exc:
                with contextlib.suppress(Exception):
                    await self._refresh_browser_state_after_run(runtime)
                await self.finalize_assistant_message(assistant_message_id, status_text="error")
                self.status = "error"
                self.updated_at = _utcnow()
                await self.emit("run.failed", {"kind": run_kind, "message": str(exc)})
                await self.emit_state()
                raise
            finally:
                self._active_task = None
                self._run_last_tool_name = None

    async def start_bootstrap(self) -> bool:
        if not self.start_url:
            return False
        if self._active_task is not None:
            return False

        prompt = f"打开并停留在 {self.start_url}，等待页面稳定后停止，不要做额外操作。"
        self._start_background_task(
            self._run_agent_turn(
                content=prompt,
                run_kind="bootstrap",
                emit_user_message=False,
                stream_text=False,
            )
        )
        return True

    async def enqueue_user_message(self, content: str) -> str:
        message = str(content or "").strip()
        if not message:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="消息不能为空")
        if self._closed:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="会话已关闭")
        if self._active_task is not None and not self._active_task.done():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前浏览器仍在执行上一条指令")

        user_message_id = str(uuid.uuid4())
        self._start_background_task(
            self._run_agent_turn(
                content=message,
                run_kind="message",
                emit_user_message=True,
                stream_text=True,
                user_message_id=user_message_id,
            )
        )
        return user_message_id

    async def stop_current_run(self) -> None:
        if self._closed:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="会话已关闭")
        if self._active_task is None or self._active_task.done():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前没有可停止的浏览器任务")
        self._stop_requested = True
        self.status = "stopping"
        self.updated_at = _utcnow()
        await self.emit_state()
        self._active_task.cancel()
        try:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._active_task
        finally:
            self._stop_requested = False

    async def stream(self, last_index: int = 0):
        cursor = max(0, last_index)
        while True:
            async with self._condition:
                if cursor >= len(self._events) and not self._closed:
                    try:
                        await asyncio.wait_for(self._condition.wait(), timeout=SSE_KEEPALIVE_SECONDS)
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
                        continue

                pending = self._events[cursor:]

            for event_name, payload in pending:
                cursor += 1
                yield f"event: {event_name}\n"
                yield f"data: {_json_dumps(payload)}\n\n"
                if event_name == "session.closed":
                    return

            if self._closed and cursor >= len(self._events):
                return

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stop_requested = False
        if self._active_task is not None and not self._active_task.done():
            self._active_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._active_task
        with contextlib.suppress(Exception):
            await self._runtime.close()
        self.tab_count = 0
        self.status = "closed"
        self.updated_at = _utcnow()
        await self.emit("session.closed", {"state": self.state_payload()})


class BrowserTaskSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, BrowserTaskSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        *,
        owner: User,
        model_profile: dict[str, Any],
        selected_skills: list[str],
        start_url: str | None,
        browser_system_prompt: str,
    ) -> BrowserTaskSession:
        session = BrowserTaskSession(
            owner_id=owner.id,
            model_profile=model_profile,
            selected_skills=selected_skills,
            start_url=start_url,
            browser_system_prompt=browser_system_prompt,
        )
        async with self._lock:
            self._sessions[session.id] = session
        await session.emit("session.created", {"state": session.state_payload()})
        await session.emit_state()
        return session

    async def get_session(self, session_id: str, owner: User) -> BrowserTaskSession:
        async with self._lock:
            session = self._sessions.get(session_id)
        if session is None or session.owner_id != owner.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
        return session

    async def close_session(self, session_id: str, owner: User) -> BrowserTaskSession:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.owner_id != owner.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
            self._sessions.pop(session_id, None)
        await session.close()
        return session

    async def stop_session(self, session_id: str, owner: User) -> BrowserTaskSession:
        session = await self.get_session(session_id, owner)
        await session.stop_current_run()
        return session

    async def close_all(self) -> None:
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            with contextlib.suppress(Exception):
                await session.close()


_manager = BrowserTaskSessionManager()


def get_manager() -> BrowserTaskSessionManager:
    return _manager


def get_bootstrap_payload(db: Session) -> dict[str, Any]:
    payload = config_service.get_config_payload(db, discover_model_pool=False)
    return {
        "skills": payload["skills"],
        "skills_enabled": payload["skills_enabled"],
        "model_profiles": payload["model_profiles"],
        "runtime_mode": "standalone",
        "persistence_mode": "memory_only",
        "mcp_selector_hidden": True,
        "system_prompt_source": "builtin_playwright_standalone",
    }


async def create_browser_task_session_async(
    db: Session,
    *,
    owner: User,
    model_profile_key: str,
    skills: list[str],
) -> tuple[BrowserTaskSession, bool]:
    payload = config_service.get_config_payload(db)
    skill_pool = set(payload["skills"] if payload["skills_enabled"] else [])
    selected_skills = [item for item in config_service.normalize_skills(skills) if item in skill_pool]
    model_profile = config_service.build_model_profile_snapshot(db, model_profile_key)
    session_obj = await _manager.create_session(
        owner=owner,
        model_profile=model_profile,
        selected_skills=selected_skills,
        start_url=None,
        browser_system_prompt=PLAYWRIGHT_BROWSER_TASK_SYSTEM_PROMPT,
    )
    return session_obj, False


async def enqueue_browser_task_message(session_id: str, owner: User, content: str) -> tuple[BrowserTaskSession, str]:
    session = await _manager.get_session(session_id, owner)
    message_id = await session.enqueue_user_message(content)
    return session, message_id


async def stream_browser_task_session(session_id: str, owner: User):
    session = await _manager.get_session(session_id, owner)
    return session.stream()


async def close_browser_task_session(session_id: str, owner: User) -> BrowserTaskSession:
    return await _manager.close_session(session_id, owner)


async def stop_browser_task_session(session_id: str, owner: User) -> BrowserTaskSession:
    return await _manager.stop_session(session_id, owner)


async def close_all_sessions() -> None:
    await _manager.close_all()
