from __future__ import annotations


def mark_dirty_all(*, reason: str | None = None) -> None:
    from python.helpers.state_monitor import get_state_monitor

    get_state_monitor().mark_dirty_all(reason=reason)


def mark_dirty_for_context(context_id: str, *, reason: str | None = None) -> None:
    from python.helpers.state_monitor import get_state_monitor

    get_state_monitor().mark_dirty_for_context(context_id, reason=reason)
