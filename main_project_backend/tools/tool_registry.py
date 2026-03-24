"""
Tool Registry：MCP 工具注册表，程序启动时按需加载配置中的 MCP 服务工具。

使用方式::

    async with ToolRegistry() as registry:
        print("已加载服务:", registry.available_servers())

        # 相当于"选择框"勾选 playwright 的工具
        browser_tools = registry.get_tools(["playwright"])

        # 勾选多个服务的工具（自动合并）
        analysis_tools = registry.get_tools(["search", "filesystem"])

        # 不传参数 = 全选
        all_tools = registry.get_tools()
"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AsyncExitStack
import shlex
from tempfile import TemporaryFile

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tools.mcp_tool import list_available_servers, load_server_config

LEGACY_TOOL_DENYLIST_BY_SERVER: dict[str, set[str]] = {
    "reverse-network-mcp-server": {"read_network_log"},
}


def _normalize_runtime_tool_input(tool_name: str, value):
    if tool_name != "browser_type" or not isinstance(value, dict):
        return value
    normalized = dict(value)
    if isinstance(normalized.get("args"), dict):
        normalized["args"] = dict(normalized["args"])
    return normalized


def apply_runtime_tool_defaults(tools: list) -> list:
    wrapped: list = []
    for tool in tools:
        tool_name = str(getattr(tool, "name", "") or "").strip()
        if tool_name != "browser_type":
            wrapped.append(tool)
            continue
        if getattr(tool, "_auto_reverse_runtime_defaults_applied", False):
            wrapped.append(tool)
            continue

        original_ainvoke = getattr(tool, "ainvoke", None)
        if callable(original_ainvoke):
            async def ainvoke_with_defaults(input, config=None, _orig=original_ainvoke, _name=tool_name, **kwargs):
                normalized_input = _normalize_runtime_tool_input(_name, input)
                return await _orig(normalized_input, config=config, **kwargs)
            object.__setattr__(tool, "ainvoke", ainvoke_with_defaults)

        original_invoke = getattr(tool, "invoke", None)
        if callable(original_invoke):
            def invoke_with_defaults(input, config=None, _orig=original_invoke, _name=tool_name, **kwargs):
                normalized_input = _normalize_runtime_tool_input(_name, input)
                return _orig(normalized_input, config=config, **kwargs)
            object.__setattr__(tool, "invoke", invoke_with_defaults)

        object.__setattr__(tool, "_auto_reverse_runtime_defaults_applied", True)
        wrapped.append(tool)
    return wrapped


def _read_errlog_tail(errlog, *, line_limit: int = 20, char_limit: int = 2000) -> str:
    try:
        errlog.flush()
        errlog.seek(0)
        raw_text = str(errlog.read() or "").strip()
    except Exception:
        return ""

    if not raw_text:
        return ""

    lines = [line.rstrip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return ""

    summary = "\n".join(lines[-line_limit:]).strip()
    if len(summary) > char_limit:
        summary = summary[-char_limit:].lstrip()
    return summary


def _format_load_error(params, exc: Exception, *, stderr_tail: str = "") -> str:
    exc_text = str(exc).strip() or exc.__class__.__name__
    command_parts = [str(params.command), *[str(item) for item in (params.args or [])]]
    command_text = shlex.join(command_parts)
    cwd_text = str(params.cwd).strip() if getattr(params, "cwd", None) else "（继承当前进程）"
    detail = f"{exc_text}；command={command_text}；cwd={cwd_text}"
    if not stderr_tail:
        return detail
    return f"{detail}；stderr tail:\n{stderr_tail}"


class ToolRegistry:
    """
    MCP 工具注册表。

    作为异步上下文管理器使用，进入时并行启动指定 MCP 服务
    的子进程并加载工具；退出时统一关闭所有子进程。
    Agent 只需调用 get_tools() 按服务名取用工具列表，完全不感知底层细节。
    """

    def __init__(
        self,
        server_names: Iterable[str] | None = None,
        *,
        headless: bool = False,
        isolated: bool = False,
    ) -> None:
        # { server_name: [LangChain Tool, ...] }
        self._store: dict[str, list] = {}
        self._load_errors: dict[str, str] = {}
        self._opened_stacks: list[AsyncExitStack] = []
        self._preserved_stacks: list[AsyncExitStack] = []
        self._requested_servers = list(server_names) if server_names is not None else None
        self._headless = headless
        self._isolated = isolated

    def _resolve_server_names(self) -> list[str]:
        available_servers = list_available_servers()
        if self._requested_servers is None:
            return available_servers

        deduped: list[str] = []
        seen: set[str] = set()
        for name in self._requested_servers:
            if name in seen:
                continue
            deduped.append(name)
            seen.add(name)

        unknown = [name for name in deduped if name not in available_servers]
        if unknown:
            available = ", ".join(available_servers) or "（无）"
            unknown_text = ", ".join(repr(name) for name in unknown)
            raise KeyError(f"服务 {unknown_text} 未在配置文件中注册，可用服务：{available}")

        return deduped

    @staticmethod
    def _filter_legacy_tools(server_name: str, tools: list) -> list:
        denylist = LEGACY_TOOL_DENYLIST_BY_SERVER.get(server_name)
        if not denylist:
            return tools

        filtered = []
        removed: list[str] = []
        for tool in tools:
            tool_name = str(getattr(tool, "name", "") or "").strip()
            if tool_name in denylist:
                removed.append(tool_name)
                continue
            filtered.append(tool)

        if removed:
            removed_names = ", ".join(removed)
            print(f"[ToolRegistry] 已过滤 {server_name} 的 legacy 工具: {removed_names}")
        return filtered

    async def __aenter__(self) -> "ToolRegistry":
        server_names = self._resolve_server_names()
        if not server_names:
            return self

        async def _load_one(name: str) -> tuple[str, list, AsyncExitStack]:
            params = load_server_config(name, headless=self._headless, isolated=self._isolated)
            stack = AsyncExitStack()
            await stack.__aenter__()
            errlog = TemporaryFile(mode="w+t", encoding="utf-8")
            stack.callback(errlog.close)
            try:
                read, write = await stack.enter_async_context(stdio_client(params, errlog=errlog))
                session: ClientSession = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                tools = await load_mcp_tools(session)
                return name, tools, stack
            except Exception as exc:
                stderr_tail = _read_errlog_tail(errlog)
                await stack.aclose()
                raise RuntimeError(_format_load_error(params, exc, stderr_tail=stderr_tail)) from exc

        for name in server_names:
            try:
                loaded_name, tools, stack = await _load_one(name)
            except Exception as exc:
                # 单个服务启动失败不影响其他服务
                self._load_errors[name] = str(exc)
                print(f"[ToolRegistry] 警告：服务 {name} 启动失败 — {exc}")
                continue
            filtered_tools = apply_runtime_tool_defaults(self._filter_legacy_tools(loaded_name, tools))
            self._store[loaded_name] = filtered_tools
            self._load_errors.pop(loaded_name, None)
            self._opened_stacks.append(stack)
            print(f"[ToolRegistry] 已加载: {loaded_name}（{len(filtered_tools)} 个工具）")

        return self

    def detach_preserved_runtime(self) -> None:
        self._preserved_stacks.extend(self._opened_stacks)
        self._opened_stacks = []

    async def close_preserved_runtime(self) -> None:
        for stack in reversed(self._preserved_stacks):
            try:
                await stack.aclose()
            except Exception as exc:
                print(f"[ToolRegistry] 警告：保留运行时清理失败 — {exc}")
        self._preserved_stacks.clear()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        for stack in reversed(self._opened_stacks):
            try:
                await stack.aclose()
            except Exception as exc:
                # MCP 清理失败不应覆盖已完成的业务结果，记录后继续回收其他服务。
                print(f"[ToolRegistry] 警告：服务清理失败 — {exc}")
        self._opened_stacks.clear()
        self._store.clear()
        self._load_errors.clear()

    def get_tools(self, servers: list[str] | None = None) -> list:
        """
        按服务名选取并合并工具列表，相当于多选框勾选。

        Args:
            servers: 服务名称列表，如 ["playwright", "search"]。
                     传入 None 或空列表时返回全部已加载工具。

        Returns:
            合并后的 LangChain Tool 列表，可直接传给 create_react_agent。

        Raises:
            KeyError: 指定的服务名未在注册表中（未加载成功）
        """
        if not servers:
            merged = []
            for tools in self._store.values():
                merged.extend(tools)
            return merged

        merged = []
        for name in servers:
            if name not in self._store:
                available = ", ".join(self._store.keys()) or "（无）"
                load_error = self._load_errors.get(name)
                if load_error:
                    raise KeyError(
                        f"服务 {name!r} 启动失败，未进入注册表：{load_error}；当前已加载服务：{available}"
                    )
                raise KeyError(
                    f"服务 {name!r} 未在注册表中，可用服务：{available}"
                )
            merged.extend(self._store[name])
        return merged

    def available_servers(self) -> list[str]:
        """返回所有已成功加载的服务名称列表。"""
        return list(self._store.keys())

    def tool_count(self, server: str | None = None) -> int:
        """返回指定服务（或全部）已加载的工具数量。"""
        if server:
            return len(self._store.get(server, []))
        return sum(len(t) for t in self._store.values())
