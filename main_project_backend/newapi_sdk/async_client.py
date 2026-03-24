from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Mapping

import httpx

from ._sse import iter_sse_events
from ._utils import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_TIMEOUT,
    build_headers,
    compact_payload,
    compute_retry_delay_seconds,
    extract_error_message,
    is_retryable_transport_error,
    join_url,
    normalize_base_url,
)
from .exceptions import NewAPIHTTPError, NewAPIRequestError, NewAPIResponseError
from .types import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    EmbeddingResponse,
    ModelsListResponse,
    ResponseObject,
    ResponseStreamEvent,
)


class AsyncModelsResource:
    def __init__(self, client: "AsyncNewAPIClient") -> None:
        self._client = client

    async def list(self) -> ModelsListResponse:
        return ModelsListResponse.from_payload(await self._client._request_json("GET", "/models"))


class AsyncChatCompletionsResource:
    def __init__(self, client: "AsyncNewAPIClient") -> None:
        self._client = client

    async def create(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> ChatCompletionResponse:
        payload = compact_payload({"model": model, "messages": messages, **kwargs})
        return ChatCompletionResponse.from_payload(await self._client._request_json("POST", "/chat/completions", json_body=payload))

    async def stream(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> AsyncIterator[ChatCompletionChunk]:
        payload = compact_payload({"model": model, "messages": messages, "stream": True, **kwargs})
        async for event in self._client._stream_json("POST", "/chat/completions", json_body=payload):
            yield ChatCompletionChunk.from_payload(event.data, event=event.event)


class AsyncChatResource:
    def __init__(self, client: "AsyncNewAPIClient") -> None:
        self.completions = AsyncChatCompletionsResource(client)


class AsyncResponsesResource:
    def __init__(self, client: "AsyncNewAPIClient") -> None:
        self._client = client

    async def create(self, *, model: str, input: Any, **kwargs: Any) -> ResponseObject:
        payload = compact_payload({"model": model, "input": input, **kwargs})
        return ResponseObject.from_payload(await self._client._request_json("POST", "/responses", json_body=payload))

    async def stream(self, *, model: str, input: Any, **kwargs: Any) -> AsyncIterator[ResponseStreamEvent]:
        payload = compact_payload({"model": model, "input": input, "stream": True, **kwargs})
        async for event in self._client._stream_json("POST", "/responses", json_body=payload):
            yield event


class AsyncEmbeddingsResource:
    def __init__(self, client: "AsyncNewAPIClient") -> None:
        self._client = client

    async def create(self, *, model: str, input: Any, **kwargs: Any) -> EmbeddingResponse:
        payload = compact_payload({"model": model, "input": input, **kwargs})
        return EmbeddingResponse.from_payload(await self._client._request_json("POST", "/embeddings", json_body=payload))


class AsyncNewAPIClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        headers: Mapping[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self._extra_headers = {str(key): str(value) for key, value in (headers or {}).items()}
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self.models = AsyncModelsResource(self)
        self.chat = AsyncChatResource(self)
        self.responses = AsyncResponsesResource(self)
        self.embeddings = AsyncEmbeddingsResource(self)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncNewAPIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self.aclose()
        return False

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_exc: httpx.HTTPError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=join_url(self.base_url, path),
                    headers=build_headers(api_key=self.api_key, extra_headers=self._extra_headers),
                    json=json_body,
                )
                return await self._decode_json_response(response)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self.max_retries or not is_retryable_transport_error(exc):
                    raise NewAPIRequestError(str(exc)) from exc
                delay_seconds = compute_retry_delay_seconds(attempt, backoff_seconds=self.retry_backoff_seconds)
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
        if last_exc is not None:
            raise NewAPIRequestError(f"请求失败（已重试 {self.max_retries} 次）") from last_exc
        raise NewAPIRequestError("请求失败")

    async def _stream_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> AsyncIterator[ResponseStreamEvent]:
        last_exc: httpx.HTTPError | None = None
        for attempt in range(self.max_retries + 1):
            yielded_event = False
            try:
                async with self._client.stream(
                    method=method,
                    url=join_url(self.base_url, path),
                    headers=build_headers(api_key=self.api_key, extra_headers=self._extra_headers),
                    json=json_body,
                ) as response:
                    await self._raise_for_status(response)
                    buffered_lines: list[str] = []
                    async for line in response.aiter_lines():
                        buffered_lines.append(line)
                        if line != "":
                            continue
                        for event in iter_sse_events(buffered_lines):
                            if not event.data:
                                continue
                            if event.data.strip() == "[DONE]":
                                return
                            try:
                                payload = json.loads(event.data)
                            except json.JSONDecodeError as exc:
                                raise NewAPIResponseError("流式响应无法解析为 JSON") from exc
                            if not isinstance(payload, dict):
                                raise NewAPIResponseError("流式响应 JSON 结构不合法")
                            yielded_event = True
                            yield ResponseStreamEvent.from_payload(
                                payload,
                                event=event.event,
                                raw_data=event.data,
                            )
                        buffered_lines = []
                    if buffered_lines:
                        for event in iter_sse_events(buffered_lines):
                            if not event.data:
                                continue
                            if event.data.strip() == "[DONE]":
                                return
                            try:
                                payload = json.loads(event.data)
                            except json.JSONDecodeError as exc:
                                raise NewAPIResponseError("流式响应无法解析为 JSON") from exc
                            if not isinstance(payload, dict):
                                raise NewAPIResponseError("流式响应 JSON 结构不合法")
                            yielded_event = True
                            yield ResponseStreamEvent.from_payload(
                                payload,
                                event=event.event,
                                raw_data=event.data,
                            )
                    return
            except httpx.HTTPError as exc:
                last_exc = exc
                if yielded_event or attempt >= self.max_retries or not is_retryable_transport_error(exc):
                    raise NewAPIRequestError(str(exc)) from exc
                delay_seconds = compute_retry_delay_seconds(attempt, backoff_seconds=self.retry_backoff_seconds)
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
        if last_exc is not None:
            raise NewAPIRequestError(f"请求失败（已重试 {self.max_retries} 次）") from last_exc

    async def _decode_json_response(self, response: httpx.Response) -> dict[str, Any]:
        await self._raise_for_status(response)
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise NewAPIResponseError("响应无法解析为 JSON") from exc
        if not isinstance(payload, dict):
            raise NewAPIResponseError("响应 JSON 结构不合法")
        return payload

    async def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body_bytes = await response.aread()
            body_text = body_bytes.decode(response.encoding or "utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body_text = ""
        try:
            payload: Any | None = json.loads(body_text) if body_text else response.json()
        except Exception:  # noqa: BLE001
            payload = body_text
        raise NewAPIHTTPError(
            status_code=response.status_code,
            message=extract_error_message(payload),
            response_body=payload,
        )
