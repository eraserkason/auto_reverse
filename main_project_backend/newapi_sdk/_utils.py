from __future__ import annotations

from typing import Any, Mapping

from .exceptions import NewAPIConfigError


DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 0.6
RETRYABLE_TRANSPORT_TYPE_NAMES = {
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "NetworkError",
    "PoolTimeout",
    "ProtocolError",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "TimeoutException",
    "WriteError",
    "WriteTimeout",
}
RETRYABLE_TRANSPORT_KEYWORDS = (
    "broken pipe",
    "connecterror",
    "connection reset",
    "connection refused",
    "network is unreachable",
    "pooltimeout",
    "protocol error",
    "readerror",
    "readtimeout",
    "remoteprotocolerror",
    "server disconnected",
    "temporarily unavailable",
    "timed out",
    "writeerror",
)


def iter_exception_chain(exc: BaseException, *, max_depth: int = 6) -> list[BaseException]:
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


def normalize_base_url(base_url: str | None) -> str:
    resolved = str(base_url or "").strip().rstrip("/")
    if not resolved:
        raise NewAPIConfigError("NewAPI 缺少 base_url")
    return resolved


def normalize_api_key(api_key: str | None) -> str:
    resolved = str(api_key or "").strip()
    if not resolved:
        raise NewAPIConfigError("NewAPI 缺少 api_key")
    return resolved


def join_url(base_url: str, path: str) -> str:
    return f"{normalize_base_url(base_url)}/{str(path or '').lstrip('/')}"


def build_headers(
    *,
    api_key: str,
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {normalize_api_key(api_key)}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    headers.update({str(key): str(value) for key, value in (extra_headers or {}).items()})
    return headers


def compact_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in payload.items() if value is not None}


def extract_error_message(payload: Any) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            for key in ("message", "type", "code"):
                value = error.get(key)
                if value:
                    return str(value)
        if isinstance(error, str) and error.strip():
            return error.strip()
        for key in ("message", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return str(payload or "").strip() or "未知错误"


def is_retryable_transport_error(exc: BaseException) -> bool:
    for current in iter_exception_chain(exc):
        if current.__class__.__name__ in RETRYABLE_TRANSPORT_TYPE_NAMES:
            return True
        message = str(current).lower()
        if any(keyword in message for keyword in RETRYABLE_TRANSPORT_KEYWORDS):
            return True
    return False


def compute_retry_delay_seconds(attempt: int, *, backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS) -> float:
    return max(0.0, float(backoff_seconds)) * max(1, int(attempt) + 1)
