from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import Any, cast

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_openai.chat_models.base import (
    WellKnownTools,
    _convert_delta_to_message_chunk,
    _convert_to_openai_response_format,
    _convert_dict_to_message,
    _convert_message_to_dict,
)
from pydantic import Field, PrivateAttr

from ._utils import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_TIMEOUT,
    normalize_api_key,
    normalize_base_url,
)
from .async_client import AsyncNewAPIClient
from .client import NewAPIClient
from .types import ChatCompletionChunk, ChatCompletionChoice, ChatMessage


def _build_response_metadata(
    *,
    model_name: str | None,
    response_id: str | None,
    finish_reason: str | None = None,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if usage:
        metadata["token_usage"] = usage
    if model_name:
        metadata["model_name"] = model_name
    if response_id:
        metadata["id"] = response_id
    if finish_reason:
        metadata["finish_reason"] = finish_reason
    return metadata


def _message_from_sdk_message(message: ChatMessage, *, response_id: str | None = None) -> AIMessage:
    payload = dict(message.raw)
    if response_id and "id" not in payload:
        payload["id"] = response_id
    converted = _convert_dict_to_message(payload)
    if not isinstance(converted, AIMessage):
        converted = AIMessage(content=str(getattr(converted, "content", "") or ""))
    if message.reasoning_content is not None:
        converted.additional_kwargs["reasoning_content"] = message.reasoning_content
    if message.refusal is not None:
        converted.additional_kwargs["refusal"] = message.refusal
    return converted


def _generation_from_choice(
    choice: ChatCompletionChoice,
    *,
    model_name: str | None,
    response_id: str | None,
    usage: dict[str, Any] | None,
) -> ChatGeneration:
    message = _message_from_sdk_message(choice.message or ChatMessage(role="assistant"), response_id=response_id)
    return ChatGeneration(
        message=message,
        generation_info=_build_response_metadata(
            model_name=model_name,
            response_id=response_id,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
        or None,
    )


def _generation_chunk_from_sdk_chunk(chunk: ChatCompletionChunk) -> ChatGenerationChunk:
    choice = chunk.choices[0] if chunk.choices else {}
    delta = dict(choice.get("delta") or {})
    if chunk.id and "id" not in delta:
        delta["id"] = chunk.id
    message_chunk = cast(AIMessageChunk, _convert_delta_to_message_chunk(delta, AIMessageChunk))
    if "reasoning_content" in delta:
        message_chunk.additional_kwargs["reasoning_content"] = delta.get("reasoning_content")
    generation_info = _build_response_metadata(
        model_name=chunk.model,
        response_id=chunk.id,
        finish_reason=str(choice.get("finish_reason") or "") or None,
    )
    return ChatGenerationChunk(message=message_chunk, generation_info=generation_info or None)


class NewAPIChatModel(BaseChatModel):
    model_name: str
    openai_api_base: str
    api_key: str = Field(..., repr=False)
    temperature: float | None = 0
    streaming: bool = False
    request_timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS
    default_headers: dict[str, str] = Field(default_factory=dict)
    model_kwargs: dict[str, Any] = Field(default_factory=dict)
    http_client: httpx.Client | None = Field(default=None, exclude=True)
    http_async_client: httpx.AsyncClient | None = Field(default=None, exclude=True)
    _root_client: NewAPIClient | None = PrivateAttr(default=None)
    _root_async_client: AsyncNewAPIClient | None = PrivateAttr(default=None)

    @property
    def model(self) -> str:
        return self.model_name

    @property
    def _llm_type(self) -> str:
        return "newapi-chat"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "openai_api_base": self.openai_api_base,
            "temperature": self.temperature,
            "streaming": self.streaming,
        }

    def _build_request_kwargs(self, *, stop: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        request_kwargs = dict(self.model_kwargs)
        request_kwargs.update({key: value for key, value in kwargs.items() if value is not None})
        extra_body = request_kwargs.pop("extra_body", None)
        if isinstance(extra_body, Mapping):
            request_kwargs.update({str(key): value for key, value in extra_body.items() if value is not None})
        request_kwargs.pop("stream", None)
        if stop is not None and "stop" not in request_kwargs:
            request_kwargs["stop"] = stop
        if self.temperature is not None and "temperature" not in request_kwargs:
            request_kwargs["temperature"] = self.temperature
        return request_kwargs

    def _messages_to_payload(self, messages: list[BaseMessage]) -> list[dict[str, Any]]:
        return [_convert_message_to_dict(message) for message in messages]

    def _new_client(self) -> NewAPIClient:
        if self._root_client is None:
            self._root_client = NewAPIClient(
                base_url=self.openai_api_base,
                api_key=self.api_key,
                timeout=self.request_timeout,
                max_retries=self.max_retries,
                retry_backoff_seconds=self.retry_backoff_seconds,
                headers=self.default_headers,
                client=self.http_client,
            )
        return self._root_client

    def _new_async_client(self) -> AsyncNewAPIClient:
        if self._root_async_client is None:
            self._root_async_client = AsyncNewAPIClient(
                base_url=self.openai_api_base,
                api_key=self.api_key,
                timeout=self.request_timeout,
                max_retries=self.max_retries,
                retry_backoff_seconds=self.retry_backoff_seconds,
                headers=self.default_headers,
                client=self.http_async_client,
            )
        return self._root_async_client

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        request_messages = self._messages_to_payload(messages)
        request_kwargs = self._build_request_kwargs(stop=stop, **kwargs)
        client = self._new_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=request_messages,
            **request_kwargs,
        )
        generations = [
            _generation_from_choice(
                choice,
                model_name=response.model,
                response_id=response.id,
                usage=response.usage,
            )
            for choice in response.choices
        ]
        return ChatResult(
            generations=generations,
            llm_output=_build_response_metadata(
                model_name=response.model,
                response_id=response.id,
                usage=response.usage,
            )
            or None,
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        request_messages = self._messages_to_payload(messages)
        request_kwargs = self._build_request_kwargs(stop=stop, **kwargs)
        client = self._new_async_client()
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=request_messages,
            **request_kwargs,
        )
        generations = [
            _generation_from_choice(
                choice,
                model_name=response.model,
                response_id=response.id,
                usage=response.usage,
            )
            for choice in response.choices
        ]
        return ChatResult(
            generations=generations,
            llm_output=_build_response_metadata(
                model_name=response.model,
                response_id=response.id,
                usage=response.usage,
            )
            or None,
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        request_messages = self._messages_to_payload(messages)
        request_kwargs = self._build_request_kwargs(stop=stop, **kwargs)
        client = self._new_client()
        for chunk in client.chat.completions.stream(
            model=self.model_name,
            messages=request_messages,
            **request_kwargs,
        ):
            yield _generation_chunk_from_sdk_chunk(chunk)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        request_messages = self._messages_to_payload(messages)
        request_kwargs = self._build_request_kwargs(stop=stop, **kwargs)
        client = self._new_async_client()
        async for chunk in client.chat.completions.stream(
            model=self.model_name,
            messages=request_messages,
            **request_kwargs,
        ):
            yield _generation_chunk_from_sdk_chunk(chunk)

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | BaseTool | Any],
        *,
        tool_choice: dict[str, Any] | str | bool | None = None,
        strict: bool | None = None,
        parallel_tool_calls: bool | None = None,
        response_format: dict[str, Any] | type | None = None,
        **kwargs: Any,
    ) -> Runnable[Any, AIMessage]:
        if parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = parallel_tool_calls
        formatted_tools = [convert_to_openai_tool(tool, strict=strict) for tool in tools]
        tool_names: list[str] = []
        for tool in formatted_tools:
            if "function" in tool:
                tool_names.append(str(tool["function"].get("name") or ""))
            elif "name" in tool:
                tool_names.append(str(tool.get("name") or ""))
        if tool_choice:
            if isinstance(tool_choice, str):
                if tool_choice in tool_names:
                    tool_choice = {"type": "function", "function": {"name": tool_choice}}
                elif tool_choice in WellKnownTools:
                    tool_choice = {"type": tool_choice}
                elif tool_choice == "any":
                    tool_choice = "required"
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif not isinstance(tool_choice, dict):
                raise ValueError(
                    f"Unrecognized tool_choice type. Expected str, bool or dict. Received: {tool_choice}"
                )
            kwargs["tool_choice"] = tool_choice
        if response_format:
            if (
                isinstance(response_format, dict)
                and response_format.get("type") == "json_schema"
                and isinstance(response_format.get("json_schema"), dict)
                and "schema" in response_format["json_schema"]
            ):
                strict = response_format["json_schema"].get("strict", strict)
                response_format = cast(dict[str, Any], response_format["json_schema"]["schema"])
            kwargs["response_format"] = _convert_to_openai_response_format(response_format, strict=strict)
        return cast("Runnable[Any, AIMessage]", super().bind(tools=formatted_tools, **kwargs))


def create_langchain_chat_model(
    *,
    model: str,
    api_key: str,
    base_url: str,
    temperature: float = 0,
    streaming: bool = False,
    **kwargs: Any,
) -> NewAPIChatModel:
    request_timeout = kwargs.pop("request_timeout", kwargs.pop("timeout", DEFAULT_TIMEOUT))
    max_retries = kwargs.pop("max_retries", DEFAULT_MAX_RETRIES)
    retry_backoff_seconds = kwargs.pop("retry_backoff_seconds", DEFAULT_RETRY_BACKOFF_SECONDS)
    default_headers = dict(kwargs.pop("default_headers", {}) or {})
    model_kwargs = dict(kwargs.pop("model_kwargs", {}) or {})
    http_client = kwargs.pop("http_client", None)
    http_async_client = kwargs.pop("http_async_client", None)
    model_kwargs.update(kwargs)
    return NewAPIChatModel(
        model_name=model,
        api_key=normalize_api_key(api_key),
        openai_api_base=normalize_base_url(base_url),
        temperature=temperature,
        streaming=streaming,
        request_timeout=float(request_timeout),
        max_retries=max(0, int(max_retries)),
        retry_backoff_seconds=max(0.0, float(retry_backoff_seconds)),
        default_headers=default_headers,
        model_kwargs=model_kwargs,
        http_client=http_client,
        http_async_client=http_async_client,
    )
