from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest


def _supports_parallel_tool_calls(bind_tools: Callable[..., Any]) -> bool:
    try:
        signature = inspect.signature(bind_tools)
    except (TypeError, ValueError):
        return False

    if 'parallel_tool_calls' in signature.parameters:
        return True

    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )


def bind_browser_tools_serially(model: Any, tools: Sequence[Any]) -> Any:
    tool_list = list(tools)
    if not tool_list:
        return model

    bind_tools = getattr(model, 'bind_tools', None)
    if not callable(bind_tools):
        return model

    if _supports_parallel_tool_calls(bind_tools):
        return bind_tools(tool_list, parallel_tool_calls=False)
    return bind_tools(tool_list)


class DisableParallelToolCallsMiddleware(AgentMiddleware):
    def _override_request(self, request: ModelRequest[Any]) -> ModelRequest[Any]:
        bind_tools = getattr(request.model, 'bind_tools', None)
        if not callable(bind_tools) or not _supports_parallel_tool_calls(bind_tools):
            return request

        model_settings = dict(request.model_settings or {})
        model_settings['parallel_tool_calls'] = False
        return request.override(model_settings=model_settings)

    def wrap_model_call(self, request, handler):
        return handler(self._override_request(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._override_request(request))
