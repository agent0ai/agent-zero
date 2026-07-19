"""Context event streaming bridge for the a0-connector plugin."""
from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Callable

from helpers.print_style import PrintStyle


EVENT_USER_MESSAGE = "user_message"
EVENT_ASSISTANT_DELTA = "assistant_delta"
EVENT_ASSISTANT_MESSAGE = "assistant_message"
EVENT_TOOL_START = "tool_start"
EVENT_TOOL_OUTPUT = "tool_output"
EVENT_TOOL_END = "tool_end"
EVENT_CODE_START = "code_start"
EVENT_CODE_OUTPUT = "code_output"
EVENT_WARNING = "warning"
EVENT_ERROR = "error"
EVENT_INFO = "info"
EVENT_STATUS = "status"
EVENT_UTIL_MESSAGE = "util_message"
EVENT_MESSAGE_COMPLETE = "message_complete"
EVENT_CONTEXT_UPDATED = "context_updated"

_LOG_TYPE_MAP: dict[str, str] = {
    "agent": EVENT_STATUS,
    "ai_response": EVENT_ASSISTANT_MESSAGE,
    "browser": EVENT_TOOL_OUTPUT,
    "code": EVENT_CODE_START,
    "code_exe": EVENT_CODE_OUTPUT,
    "code_output": EVENT_CODE_OUTPUT,
    "error": EVENT_ERROR,
    "hint": EVENT_STATUS,
    "info": EVENT_INFO,
    "input": EVENT_USER_MESSAGE,
    "mcp": EVENT_TOOL_START,
    "progress": EVENT_STATUS,
    "response": EVENT_ASSISTANT_MESSAGE,
    "subagent": EVENT_STATUS,
    "tool": EVENT_TOOL_START,
    "tool_output": EVENT_TOOL_OUTPUT,
    "user": EVENT_USER_MESSAGE,
    "util": EVENT_UTIL_MESSAGE,
    "warning": EVENT_WARNING,
}


def log_entry_to_connector_event(
    log_entry: dict[str, Any],
    context_id: str,
) -> dict[str, Any]:
    entry_type = str(log_entry.get("type", "")).strip()
    event_type = _LOG_TYPE_MAP.get(entry_type, EVENT_STATUS)
    item_no = int(log_entry.get("no", 0) or 0)

    data: dict[str, Any] = {}
    content = log_entry.get("content")
    heading = log_entry.get("heading")
    kvps = log_entry.get("kvps")

    if isinstance(content, str) and content:
        data["text"] = content
    if isinstance(heading, str) and heading:
        data["heading"] = heading
    if isinstance(kvps, dict) and kvps:
        data["meta"] = kvps

    return {
        "context_id": context_id,
        "sequence": item_no + 1,
        "event": event_type,
        "timestamp": log_entry.get("timestamp", ""),
        "data": data,
    }


def get_context_log_entries(
    context_id: str,
    after: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Return connector events plus the next log cursor for the context."""
    try:
        from agent import AgentContext

        context = AgentContext.get(context_id)
        if context is None:
            return [], 0

        log_output = context.log.output(start=max(int(after or 0), 0))
        events = [
            log_entry_to_connector_event(entry, context_id)
            for entry in log_output.items
            if isinstance(entry, dict)
        ]
        return events, int(log_output.end)
    except Exception as exc:
        PrintStyle.error(
            f"[a0-connector] event_bridge error for context {context_id}: {exc}"
        )
        return [], max(int(after or 0), 0)


async def stream_context_events(
    context_id: str,
    from_sequence: int = 0,
    poll_interval: float = 0.5,
    timeout: float = 300.0,
    emit_fn: Callable[[dict[str, Any]], Any] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    cursor = max(int(from_sequence or 0), 0)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        events, next_cursor = get_context_log_entries(context_id, after=cursor)
        for event in events:
            if emit_fn is not None:
                try:
                    result = emit_fn(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:
                    PrintStyle.error(f"[a0-connector] emit_fn error: {exc}")
            yield event

        cursor = max(cursor, next_cursor)
        await asyncio.sleep(poll_interval)
