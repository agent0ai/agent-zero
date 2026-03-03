from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from python.helpers import persist_chat
from python.helpers.state_monitor_integration import mark_dirty_all


LEGALFLOW_REVIEW_GATE_KEY = "legalflow_review_gate"

ReviewGateStatus = Literal["not_required", "required", "passed", "failed", "stale"]


class ReviewGate(TypedDict, total=False):
    version: int
    status: ReviewGateStatus
    required_for_revision: int
    reviewed_revision: int
    updated_at: str
    report: dict[str, Any]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_gate(context) -> ReviewGate | None:  # AgentContext
    raw: Any = None
    try:
        raw = context.get_data(LEGALFLOW_REVIEW_GATE_KEY)
    except Exception:
        raw = None
    if isinstance(raw, dict):
        return raw  # type: ignore[return-value]
    try:
        raw = context.get_output_data(LEGALFLOW_REVIEW_GATE_KEY)
    except Exception:
        raw = None
    return raw if isinstance(raw, dict) else None


def _set_gate(context, gate: ReviewGate) -> None:  # AgentContext
    context.set_data(LEGALFLOW_REVIEW_GATE_KEY, gate)
    context.set_output_data(LEGALFLOW_REVIEW_GATE_KEY, gate)
    try:
        persist_chat.save_tmp_chat(context)
    except Exception:
        pass
    try:
        mark_dirty_all(reason="review_gate.update")
    except Exception:
        pass


def require_review(context, *, revision: int, reason: str | None = None) -> ReviewGate:
    gate: ReviewGate = {
        "version": 1,
        "status": "required",
        "required_for_revision": revision,
        "reviewed_revision": 0,
        "updated_at": _now_iso(),
    }
    if reason:
        gate["report"] = {"reason": reason}
    _set_gate(context, gate)
    return gate


def record_review_result(
    context,
    *,
    revision: int,
    passed: bool,
    report: dict[str, Any],
) -> ReviewGate:
    gate: ReviewGate = {
        "version": 1,
        "status": "passed" if passed else "failed",
        "required_for_revision": revision,
        "reviewed_revision": revision,
        "updated_at": _now_iso(),
        "report": report,
    }
    _set_gate(context, gate)
    return gate

