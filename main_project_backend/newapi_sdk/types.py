from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ModelObject:
    id: str
    object: str | None = None
    created: int | None = None
    owned_by: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ModelObject":
        return cls(
            id=str(payload.get("id") or ""),
            object=str(payload.get("object") or "") or None,
            created=payload.get("created") if isinstance(payload.get("created"), int) else None,
            owned_by=str(payload.get("owned_by") or "") or None,
            raw=dict(payload),
        )


@dataclass(slots=True)
class ModelsListResponse:
    data: list[ModelObject]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ModelsListResponse":
        items = payload.get("data", []) if isinstance(payload, dict) else []
        return cls(
            data=[ModelObject.from_payload(item) for item in items if isinstance(item, dict)],
            raw=dict(payload),
        )


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: Any = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    reasoning_content: Any = None
    refusal: Any = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ChatMessage":
        tool_calls = payload.get("tool_calls") if isinstance(payload.get("tool_calls"), list) else []
        return cls(
            role=str(payload.get("role") or ""),
            content=payload.get("content"),
            name=str(payload.get("name") or "") or None,
            tool_call_id=str(payload.get("tool_call_id") or "") or None,
            tool_calls=[item for item in tool_calls if isinstance(item, dict)],
            reasoning_content=payload.get("reasoning_content"),
            refusal=payload.get("refusal"),
            raw=dict(payload),
        )


@dataclass(slots=True)
class ChatCompletionChoice:
    index: int
    finish_reason: str | None
    message: ChatMessage | None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ChatCompletionChoice":
        raw_message = payload.get("message")
        return cls(
            index=int(payload.get("index") or 0),
            finish_reason=str(payload.get("finish_reason") or "") or None,
            message=ChatMessage.from_payload(raw_message) if isinstance(raw_message, dict) else None,
            raw=dict(payload),
        )


@dataclass(slots=True)
class ChatCompletionResponse:
    id: str | None
    model: str | None
    object: str | None
    created: int | None
    choices: list[ChatCompletionChoice]
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ChatCompletionResponse":
        choices = payload.get("choices", []) if isinstance(payload, dict) else []
        return cls(
            id=str(payload.get("id") or "") or None,
            model=str(payload.get("model") or "") or None,
            object=str(payload.get("object") or "") or None,
            created=payload.get("created") if isinstance(payload.get("created"), int) else None,
            choices=[ChatCompletionChoice.from_payload(item) for item in choices if isinstance(item, dict)],
            usage=dict(payload.get("usage") or {}) if isinstance(payload.get("usage"), dict) else {},
            raw=dict(payload),
        )


@dataclass(slots=True)
class ChatCompletionChunk:
    id: str | None
    model: str | None
    object: str | None
    created: int | None
    choices: list[dict[str, Any]]
    raw: dict[str, Any] = field(default_factory=dict)
    event: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, event: str | None = None) -> "ChatCompletionChunk":
        choices = payload.get("choices", []) if isinstance(payload, dict) else []
        return cls(
            id=str(payload.get("id") or "") or None,
            model=str(payload.get("model") or "") or None,
            object=str(payload.get("object") or "") or None,
            created=payload.get("created") if isinstance(payload.get("created"), int) else None,
            choices=[item for item in choices if isinstance(item, dict)],
            raw=dict(payload),
            event=event,
        )


@dataclass(slots=True)
class ResponseObject:
    id: str | None
    model: str | None
    object: str | None
    status: str | None
    output: list[Any]
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ResponseObject":
        output = payload.get("output", []) if isinstance(payload, dict) and isinstance(payload.get("output"), list) else []
        return cls(
            id=str(payload.get("id") or "") or None,
            model=str(payload.get("model") or "") or None,
            object=str(payload.get("object") or "") or None,
            status=str(payload.get("status") or "") or None,
            output=list(output),
            usage=dict(payload.get("usage") or {}) if isinstance(payload.get("usage"), dict) else {},
            raw=dict(payload),
        )


@dataclass(slots=True)
class ResponseStreamEvent:
    event: str | None
    data: dict[str, Any]
    raw_data: str

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        event: str | None = None,
        raw_data: str = "",
    ) -> "ResponseStreamEvent":
        return cls(event=event, data=dict(payload), raw_data=raw_data)


@dataclass(slots=True)
class EmbeddingData:
    index: int
    embedding: list[float]
    object: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EmbeddingData":
        embedding = payload.get("embedding", [])
        return cls(
            index=int(payload.get("index") or 0),
            embedding=[float(item) for item in embedding] if isinstance(embedding, list) else [],
            object=str(payload.get("object") or "") or None,
            raw=dict(payload),
        )


@dataclass(slots=True)
class EmbeddingResponse:
    model: str | None
    object: str | None
    data: list[EmbeddingData]
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EmbeddingResponse":
        items = payload.get("data", []) if isinstance(payload, dict) else []
        return cls(
            model=str(payload.get("model") or "") or None,
            object=str(payload.get("object") or "") or None,
            data=[EmbeddingData.from_payload(item) for item in items if isinstance(item, dict)],
            usage=dict(payload.get("usage") or {}) if isinstance(payload.get("usage"), dict) else {},
            raw=dict(payload),
        )
