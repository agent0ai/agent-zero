from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from typing import Any

WORKFLOW_KEY = "workflow_runs"
MAX_WORKFLOW_OUTPUT_CHARS = 12000
SENSITIVE_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth_header",
    "private_key",
    "access_key",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_store() -> dict[str, Any]:
    return {"runs": [], "saved_runs": [], "active_run_id": None}


def _is_sensitive_key(key: str) -> bool:
    key_lower = key.strip().lower()
    return any(marker in key_lower for marker in SENSITIVE_KEY_MARKERS)


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, val in value.items():
            if _is_sensitive_key(str(key)):
                redacted[str(key)] = "***REDACTED***"
            else:
                redacted[str(key)] = _redact_value(val)
        return redacted
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def _compact_deployment_output(payload: dict[str, Any]) -> dict[str, Any]:
    deployment = payload.get("deployment")
    compact: dict[str, Any] = {}
    if isinstance(deployment, dict):
        compact["deployment"] = {
            "environment": deployment.get("environment"),
            "status": deployment.get("status"),
            "platform": deployment.get("platform"),
            "telemetry": deployment.get("telemetry"),
        }
    return compact


def _prepare_output(output: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    safe_output = _redact_value(copy.deepcopy(output))
    serialized = json.dumps(safe_output, ensure_ascii=False, default=str)
    if len(serialized) <= MAX_WORKFLOW_OUTPUT_CHARS:
        return safe_output, False

    compact = _compact_deployment_output(safe_output)
    compact["_truncated"] = {
        "reason": "size_limit",
        "max_chars": MAX_WORKFLOW_OUTPUT_CHARS,
        "original_chars": len(serialized),
    }
    return compact, True


def ensure_store(context) -> dict[str, Any]:
    store = context.data.get(WORKFLOW_KEY)
    if not store or not isinstance(store, dict):
        store = _default_store()
        context.data[WORKFLOW_KEY] = store
    store.setdefault("runs", [])
    store.setdefault("saved_runs", [])
    store.setdefault("active_run_id", None)
    return store


def _find_run(store: dict[str, Any], run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    for run in store.get("runs", []):
        if run.get("run_id") == run_id:
            return run
    return None


def start_run(context, name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    store = ensure_store(context)
    run_id = str(uuid.uuid4())
    run = {
        "run_id": run_id,
        "name": name,
        "created_at": _now_iso(),
        "status": "in_progress",
        "steps": [],
        "metadata": metadata or {},
    }
    store["runs"].append(run)
    store["active_run_id"] = run_id
    return run


def ensure_active_run(context, name: str | None = None) -> dict[str, Any] | None:
    store = ensure_store(context)
    active = _find_run(store, store.get("active_run_id"))
    if active:
        return active
    if not name:
        return None
    return start_run(context, name, metadata={"context_id": getattr(context, "id", "")})


def record_tool_start(
    context,
    tool_name: str,
    trace_id: str,
    agent_name: str,
    agent_number: int,
    tool_args: dict[str, Any] | None,
    auto_store: bool = True,
) -> str | None:
    if not auto_store:
        return None
    run = ensure_active_run(context, name="Thread Workflow")
    if not run:
        return None
    step_id = str(uuid.uuid4())
    step = {
        "step_id": step_id,
        "trace_id": trace_id,
        "name": tool_name,
        "tool_name": tool_name,
        "agent_name": agent_name,
        "agent_number": agent_number,
        "status": "running",
        "started_at": _now_iso(),
        "ended_at": None,
        "duration_ms": None,
        "error": None,
        "tool_args": tool_args or {},
    }
    run["steps"].append(step)
    return step_id


def record_tool_end(
    context,
    step_id: str | None,
    status: str,
    duration_ms: float | None,
    error: str | None = None,
    output: dict[str, Any] | None = None,
) -> None:
    if not step_id:
        return
    store = ensure_store(context)
    active = _find_run(store, store.get("active_run_id"))
    if not active:
        return
    for step in active.get("steps", []):
        if step.get("step_id") == step_id:
            step["status"] = status
            step["ended_at"] = _now_iso()
            if duration_ms is not None:
                step["duration_ms"] = round(duration_ms, 2)
            if error:
                step["error"] = error
            if output:
                safe_output, truncated = _prepare_output(output)
                step["output"] = safe_output
                if truncated:
                    step["output_truncated"] = True
                deployment = safe_output.get("deployment", {})
                if isinstance(deployment, dict):
                    telemetry = deployment.get("telemetry")
                    if isinstance(telemetry, dict):
                        step["deployment_telemetry"] = telemetry
                    if deployment.get("status") is not None:
                        step["deployment_status"] = deployment.get("status")
                    if deployment.get("environment") is not None:
                        step["deployment_environment"] = deployment.get("environment")
            break


def save_active_run(context, label: str | None = None) -> dict[str, Any] | None:
    store = ensure_store(context)
    active = _find_run(store, store.get("active_run_id"))
    if not active:
        return None
    saved = copy.deepcopy(active)
    saved["saved_at"] = _now_iso()
    if label:
        saved["label"] = label
    saved["status"] = "saved"
    store["saved_runs"].append(saved)
    return saved


def clear_store(context) -> dict[str, Any]:
    store = _default_store()
    context.data[WORKFLOW_KEY] = store
    return store
