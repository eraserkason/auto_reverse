from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(slots=True)
class ServerSentEvent:
    event: str | None
    data: str
    event_id: str | None = None
    retry: int | None = None


def iter_sse_events(lines: Iterable[str]) -> Iterator[ServerSentEvent]:
    data_lines: list[str] = []
    event_name: str | None = None
    event_id: str | None = None
    retry: int | None = None

    def flush() -> ServerSentEvent | None:
        nonlocal data_lines, event_name, event_id, retry
        if not data_lines and event_name is None and event_id is None and retry is None:
            return None
        event = ServerSentEvent(
            event=event_name,
            data="\n".join(data_lines),
            event_id=event_id,
            retry=retry,
        )
        data_lines = []
        event_name = None
        event_id = None
        retry = None
        return event

    for raw_line in lines:
        line = str(raw_line).rstrip("\n")
        if line.endswith("\r"):
            line = line[:-1]

        if line == "":
            event = flush()
            if event is not None:
                yield event
            continue

        if line.startswith(":"):
            continue

        field, separator, value = line.partition(":")
        if separator and value.startswith(" "):
            value = value[1:]

        if field == "data":
            data_lines.append(value)
        elif field == "event":
            event_name = value or None
        elif field == "id":
            event_id = value or None
        elif field == "retry":
            try:
                retry = int(value)
            except ValueError:
                retry = None

    event = flush()
    if event is not None:
        yield event
