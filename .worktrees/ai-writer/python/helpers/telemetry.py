from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from python.helpers.secrets import get_secrets_manager

TELEMETRY_KEY = "telemetry"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _mask_value(secrets_mgr, value: Any) -> Any:
    if isinstance(value, str):
        return secrets_mgr.mask_values(value)
    if isinstance(value, list):
        return [_mask_value(secrets_mgr, item) for item in value]
    if isinstance(value, dict):
        return {key: _mask_value(secrets_mgr, val) for key, val in value.items()}
    return value


def _safe_args(context, args: dict[str, Any]) -> dict[str, Any]:
    secrets_mgr = get_secrets_manager(context)
    return {key: _mask_value(secrets_mgr, value) for key, value in (args or {}).items()}


def ensure_store(context) -> dict[str, Any]:
    store = context.data.get(TELEMETRY_KEY)
    if not store or not isinstance(store, dict):
        store = {"events": [], "stats": {}}
        context.data[TELEMETRY_KEY] = store
    store.setdefault("events", [])
    store.setdefault("stats", {})
    return store


def record_event(context, event: dict[str, Any], max_events: int) -> dict[str, Any]:
    store = ensure_store(context)
    events = store["events"]
    events.append(event)
    if max_events and len(events) > max_events:
        store["events"] = events[-max_events:]
    return event


def update_stats(context, tool_name: str, duration_ms: float | None, status: str) -> None:
    store = ensure_store(context)
    stats = store["stats"]
    tool_stats = stats.get(tool_name) or {"count": 0, "error_count": 0, "total_ms": 0.0}
    tool_stats["count"] += 1
    if status != "success":
        tool_stats["error_count"] += 1
    if duration_ms is not None:
        tool_stats["total_ms"] += duration_ms
        tool_stats["avg_ms"] = tool_stats["total_ms"] / max(tool_stats["count"], 1)
    stats[tool_name] = tool_stats


def build_event(
    context,
    trace_id: str,
    agent_name: str,
    agent_number: int,
    tool_name: str,
    stage: str,
    tool_args: dict[str, Any] | None = None,
    duration_ms: float | None = None,
    status: str = "success",
    error: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "trace_id": trace_id,
        "timestamp": _now_iso(),
        "agent_name": agent_name,
        "agent_number": agent_number,
        "tool_name": tool_name,
        "stage": stage,
        "status": status,
    }
    if tool_args is not None:
        event["tool_args"] = _safe_args(context, tool_args)
    if duration_ms is not None:
        event["duration_ms"] = round(duration_ms, 2)
    if error:
        event["error"] = error
    return event


def now_ms() -> float:
    return time.time() * 1000.0
