from __future__ import annotations

import json
import time
from typing import Any, Iterator, Mapping

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


class ModelsResource:
    def __init__(self, client: "NewAPIClient") -> None:
        self._client = client

    def list(self) -> ModelsListResponse:
        return ModelsListResponse.from_payload(self._client._request_json("GET", "/models"))


class ChatCompletionsResource:
    def __init__(self, client: "NewAPIClient") -> None:
        self._client = client

    def create(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> ChatCompletionResponse:
        payload = compact_payload({"model": model, "messages": messages, **kwargs})
        return ChatCompletionResponse.from_payload(self._client._request_json("POST", "/chat/completions", json_body=payload))

    def stream(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[ChatCompletionChunk]:
        payload = compact_payload({"model": model, "messages": messages, "stream": True, **kwargs})
        for event in self._client._stream_json("POST", "/chat/completions", json_body=payload):
            yield ChatCompletionChunk.from_payload(event.data, event=event.event)


class ChatResource:
    def __init__(self, client: "NewAPIClient") -> None:
        self.completions = ChatCompletionsResource(client)


class ResponsesResource:
    def __init__(self, client: "NewAPIClient") -> None:
        self._client = client

    def create(self, *, model: str, input: Any, **kwargs: Any) -> ResponseObject:
        payload = compact_payload({"model": model, "input": input, **kwargs})
        return ResponseObject.from_payload(self._client._request_json("POST", "/responses", json_body=payload))

    def stream(self, *, model: str, input: Any, **kwargs: Any) -> Iterator[ResponseStreamEvent]:
        payload = compact_payload({"model": model, "input": input, "stream": True, **kwargs})
        yield from self._client._stream_json("POST", "/responses", json_body=payload)


class EmbeddingsResource:
    def __init__(self, client: "NewAPIClient") -> None:
        self._client = client

    def create(self, *, model: str, input: Any, **kwargs: Any) -> EmbeddingResponse:
        payload = compact_payload({"model": model, "input": input, **kwargs})
        return EmbeddingResponse.from_payload(self._client._request_json("POST", "/embeddings", json_body=payload))


class NewAPIClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        headers: Mapping[str, str] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self._extra_headers = {str(key): str(value) for key, value in (headers or {}).items()}
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)
        self.models = ModelsResource(self)
        self.chat = ChatResource(self)
        self.responses = ResponsesResource(self)
        self.embeddings = EmbeddingsResource(self)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "NewAPIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_exc: httpx.HTTPError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=join_url(self.base_url, path),
                    headers=build_headers(api_key=self.api_key, extra_headers=self._extra_headers),
                    json=json_body,
                )
                return self._decode_json_response(response)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self.max_retries or not is_retryable_transport_error(exc):
                    raise NewAPIRequestError(str(exc)) from exc
                delay_seconds = compute_retry_delay_seconds(attempt, backoff_seconds=self.retry_backoff_seconds)
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
        if last_exc is not None:
            raise NewAPIRequestError(f"请求失败（已重试 {self.max_retries} 次）") from last_exc
        raise NewAPIRequestError("请求失败")

    def _stream_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Iterator[ResponseStreamEvent]:
        last_exc: httpx.HTTPError | None = None
        for attempt in range(self.max_retries + 1):
            yielded_event = False
            try:
                with self._client.stream(
                    method=method,
                    url=join_url(self.base_url, path),
                    headers=build_headers(api_key=self.api_key, extra_headers=self._extra_headers),
                    json=json_body,
                ) as response:
                    self._raise_for_status(response)
                    for event in iter_sse_events(response.iter_lines()):
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
                    time.sleep(delay_seconds)
        if last_exc is not None:
            raise NewAPIRequestError(f"请求失败（已重试 {self.max_retries} 次）") from last_exc

    def _decode_json_response(self, response: httpx.Response) -> dict[str, Any]:
        self._raise_for_status(response)
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise NewAPIResponseError("响应无法解析为 JSON") from exc
        if not isinstance(payload, dict):
            raise NewAPIResponseError("响应 JSON 结构不合法")
        return payload

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        body_text = ""
        payload: Any | None = None
        try:
            body_text = response.text
        except Exception:  # noqa: BLE001
            body_text = ""
        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
            payload = body_text
        raise NewAPIHTTPError(
            status_code=response.status_code,
            message=extract_error_message(payload),
            response_body=payload,
        )
