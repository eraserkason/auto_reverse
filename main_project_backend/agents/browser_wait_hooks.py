from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar


T = TypeVar("T")
HookPredicate = Callable[[T], bool]


@dataclass
class WaitHookResult(Generic[T]):
    matched: bool
    matched_hook: str | None
    attempts: int
    elapsed_seconds: float
    last_value: T | None = None


async def wait_for_hooks(
    value_getter: Callable[[], Awaitable[T]],
    hooks: list[tuple[str, HookPredicate[T]]],
    *,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 1.5,
) -> WaitHookResult[T]:
    if not hooks:
        raise ValueError("wait_for_hooks 至少需要一个 hook 条件")

    loop = asyncio.get_running_loop()
    started_at = loop.time()
    attempts = 0
    last_value: T | None = None
    timeout = max(0.0, float(timeout_seconds))
    poll_interval = max(0.0, float(poll_interval_seconds))

    while True:
        attempts += 1
        last_value = await value_getter()

        for hook_name, predicate in hooks:
            try:
                if predicate(last_value):
                    return WaitHookResult(
                        matched=True,
                        matched_hook=hook_name,
                        attempts=attempts,
                        elapsed_seconds=loop.time() - started_at,
                        last_value=last_value,
                    )
            except Exception:
                continue

        elapsed = loop.time() - started_at
        if elapsed >= timeout:
            return WaitHookResult(
                matched=False,
                matched_hook=None,
                attempts=attempts,
                elapsed_seconds=elapsed,
                last_value=last_value,
            )

        remaining = max(0.0, timeout - elapsed)
        await asyncio.sleep(min(poll_interval, remaining) if poll_interval > 0 else 0)
