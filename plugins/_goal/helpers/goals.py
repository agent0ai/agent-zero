from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from helpers import files


PLUGIN_NAME = "_goal"
GOALS_DIR = "goals"
ACTIVE_STATUSES = {"active", "paused"}
FINAL_STATUSES = {"complete", "blocked"}
VALID_STATUSES = ACTIVE_STATUSES | FINAL_STATUSES


def get_goal(context_id: str) -> dict[str, Any] | None:
    context_id = _require_context_id(context_id)
    path = _goal_path(context_id)
    if not Path(path).is_file():
        return None

    try:
        raw = json.loads(files.read_file(path))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None

    goal = _normalize_goal(raw, context_id=context_id)
    if not goal.get("objective"):
        return None
    return goal


def list_goals() -> list[dict[str, Any]]:
    directory = _goals_dir()
    if not Path(directory).is_dir():
        return []

    goals: list[dict[str, Any]] = []
    for goal_file in sorted(Path(directory).glob("*.json")):
        try:
            raw = json.loads(files.read_file(str(goal_file)))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        context_id = str(raw.get("context_id") or "").strip()
        if not context_id:
            continue
        goal = _normalize_goal(raw, context_id=context_id)
        if goal.get("objective"):
            goals.append(goal)
    return goals


def create_goal(
    context_id: str,
    objective: str,
    *,
    created_by: str = "user",
    token_budget: int | None = None,
) -> dict[str, Any]:
    context_id = _require_context_id(context_id)
    objective = _clean_objective(objective)
    if not objective:
        raise ValueError("Goal objective is required")

    now = _now()
    existing = get_goal(context_id)
    goal = {
        "context_id": context_id,
        "objective": objective,
        "status": "active",
        "created_by": _clean_created_by(created_by),
        "token_budget": _clean_token_budget(token_budget),
        "created_at": existing.get("created_at") if existing else now,
        "active_since": now,
        "elapsed_seconds": 0,
        "updated_at": now,
        "note": "",
    }
    _write_goal(goal)
    return goal


def update_goal(
    context_id: str,
    *,
    objective: str | None = None,
    status: str | None = None,
    note: str | None = None,
    token_budget: int | None = None,
) -> dict[str, Any]:
    context_id = _require_context_id(context_id)
    goal = get_goal(context_id)
    if not goal:
        raise FileNotFoundError("Goal not found")

    if objective is not None:
        cleaned_objective = _clean_objective(objective)
        if not cleaned_objective:
            raise ValueError("Goal objective is required")
        goal["objective"] = cleaned_objective

    if status is not None:
        _apply_status(goal, _normalize_status(status))

    if note is not None:
        goal["note"] = str(note or "").strip()

    if token_budget is not None:
        goal["token_budget"] = _clean_token_budget(token_budget)

    goal["updated_at"] = _now()
    _write_goal(goal)
    return goal


def delete_goal(context_id: str) -> None:
    context_id = _require_context_id(context_id)
    files.delete_file(_goal_path(context_id))


def public_goal(goal: dict[str, Any] | None) -> dict[str, Any] | None:
    if not goal:
        return None
    return {
        "context_id": str(goal.get("context_id") or ""),
        "objective": str(goal.get("objective") or ""),
        "status": str(goal.get("status") or "active"),
        "created_by": str(goal.get("created_by") or "user"),
        "token_budget": goal.get("token_budget"),
        "created_at": str(goal.get("created_at") or ""),
        "active_since": str(goal.get("active_since") or ""),
        "elapsed_seconds": _clean_elapsed_seconds(goal.get("elapsed_seconds")),
        "updated_at": str(goal.get("updated_at") or ""),
        "note": str(goal.get("note") or ""),
    }


def summarize_goal(goal: dict[str, Any] | None) -> str:
    if not goal:
        return "No goal is set for this chat."

    status = str(goal.get("status") or "active")
    objective = str(goal.get("objective") or "").strip()
    elapsed = _format_elapsed(_elapsed_seconds(goal))
    updated = str(goal.get("updated_at") or "").strip()
    lines = [f"Status: {status}", f"Goal: {objective}", f"Active time: {elapsed}"]
    if updated:
        lines.append(f"Updated: {updated}")
    note = str(goal.get("note") or "").strip()
    if note:
        lines.append(f"Note: {note}")
    return "\n".join(lines)


def _write_goal(goal: dict[str, Any]) -> None:
    files.write_file(
        _goal_path(str(goal["context_id"])),
        json.dumps(public_goal(goal), indent=2, ensure_ascii=False) + "\n",
    )


def _normalize_goal(raw: dict[str, Any], *, context_id: str) -> dict[str, Any]:
    status = str(raw.get("status") or "active").strip().lower()
    if status not in VALID_STATUSES:
        status = "active"

    created_at = str(raw.get("created_at") or "")
    updated_at = str(raw.get("updated_at") or "")
    active_since = str(raw.get("active_since") or "")
    elapsed_seconds = _clean_elapsed_seconds(raw.get("elapsed_seconds"))
    if "elapsed_seconds" not in raw and status != "active":
        elapsed_seconds = _seconds_between(created_at, updated_at)
    if status == "active" and not active_since:
        active_since = created_at or updated_at

    return {
        "context_id": context_id,
        "objective": _clean_objective(str(raw.get("objective") or "")),
        "status": status,
        "created_by": _clean_created_by(str(raw.get("created_by") or "user")),
        "token_budget": _clean_token_budget(raw.get("token_budget")),
        "created_at": created_at,
        "active_since": active_since,
        "elapsed_seconds": elapsed_seconds,
        "updated_at": updated_at,
        "note": str(raw.get("note") or "").strip(),
    }


def _goals_dir() -> str:
    return files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR, PLUGIN_NAME, GOALS_DIR)


def _goal_path(context_id: str) -> str:
    return files.get_abs_path(_goals_dir(), f"{_safe_context_id(context_id)}.json")


def _require_context_id(context_id: str) -> str:
    context_id = str(context_id or "").strip()
    if not context_id:
        raise ValueError("A chat context is required")
    return context_id


def _safe_context_id(context_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", context_id).strip("._")
    if not safe:
        raise ValueError("A chat context is required")
    return safe[:180]


def _clean_objective(objective: str) -> str:
    return re.sub(r"\s+", " ", str(objective or "")).strip()


def _normalize_status(status: str) -> str:
    cleaned = str(status or "").strip().lower()
    if cleaned not in VALID_STATUSES:
        raise ValueError("Goal status must be active, paused, complete, or blocked")
    return cleaned


def _clean_created_by(created_by: str) -> str:
    cleaned = str(created_by or "").strip().lower()
    return cleaned if cleaned in {"user", "model"} else "user"


def _clean_token_budget(token_budget: Any) -> int | None:
    if token_budget in (None, ""):
        return None
    try:
        value = int(token_budget)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _apply_status(goal: dict[str, Any], status: str) -> None:
    current = str(goal.get("status") or "active")
    if current == "active" and status != "active":
        goal["elapsed_seconds"] = _elapsed_seconds(goal)
        goal["active_since"] = ""
    elif current != "active" and status == "active":
        goal["active_since"] = _now()
    goal["status"] = status


def _elapsed_seconds(goal: dict[str, Any]) -> int:
    seconds = _clean_elapsed_seconds(goal.get("elapsed_seconds"))
    if str(goal.get("status") or "active") == "active":
        seconds += _seconds_between(str(goal.get("active_since") or ""), _now())
    return seconds


def _clean_elapsed_seconds(value: Any) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, seconds)


def _seconds_between(start: str, end: str) -> int:
    start_dt = _parse_time(start)
    end_dt = _parse_time(end)
    if not start_dt or not end_dt:
        return 0
    return max(0, int((end_dt - start_dt).total_seconds()))


def _parse_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_elapsed(seconds: int) -> str:
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
