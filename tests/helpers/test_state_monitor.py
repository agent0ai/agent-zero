import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.asyncio
async def test_state_monitor_debounce_coalesces_without_postponing_and_cleanup_cancels_pending():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    namespace = "/state_sync"
    monitor = StateMonitor(debounce_seconds=10.0)
    monitor.register_sid(namespace, "sid-1")
    monitor.bind_manager(type("FakeManager", (), {"_dispatcher_loop": None})())
    monitor.update_projection(
        namespace,
        "sid-1",
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )

    monitor.mark_dirty(namespace, "sid-1")
    first = monitor._debounce_handles[(namespace, "sid-1")]

    monitor.mark_dirty(namespace, "sid-1")
    second = monitor._debounce_handles[(namespace, "sid-1")]

    # Throttled coalescing: subsequent dirties keep the scheduled push instead of postponing it.
    assert first is second
    assert not second.cancelled()

    monitor.unregister_sid(namespace, "sid-1")
    assert second.cancelled()
    assert (namespace, "sid-1") not in monitor._debounce_handles


@pytest.mark.asyncio
async def test_state_monitor_namespace_identity_prevents_cross_namespace_state_push(monkeypatch) -> None:
    import asyncio
    from unittest.mock import AsyncMock

    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    loop = asyncio.get_running_loop()
    push_ready = asyncio.Event()
    captured: list[tuple[str, str]] = []

    async def _emit_to(namespace: str, sid: str, event_type: str, _payload: object, **_kwargs):
        if event_type == "state_push":
            captured.append((namespace, sid))
            push_ready.set()

    class FakeManager:
        def __init__(self):
            self._dispatcher_loop = loop
            self.emit_to = AsyncMock(side_effect=_emit_to)

    monitor = StateMonitor(debounce_seconds=0.0)
    manager = FakeManager()
    monitor.bind_manager(manager, handler_id="tester")

    sid = "shared-sid"
    ns_a = "/a"
    ns_b = "/b"
    monitor.register_sid(ns_a, sid)
    monitor.register_sid(ns_b, sid)
    monitor.update_projection(
        ns_a,
        sid,
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.update_projection(
        ns_b,
        sid,
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )

    async def _fake_snapshot(**_kwargs):
        return {
            "log_version": 0,
            "notifications_version": 0,
            "logs": [],
            "contexts": [],
            "tasks": [],
            "notifications": [],
        }

    # Patch build_snapshot used by StateMonitor so this test stays lightweight.
    monkeypatch.setattr("python.helpers.state_monitor.build_snapshot_from_request", _fake_snapshot)

    monitor.mark_dirty(ns_a, sid, reason="test")
    await asyncio.wait_for(push_ready.wait(), timeout=1.0)

    assert captured
    assert all(ns == ns_a for ns, _ in captured)


# --- get_state_monitor ---


def test_get_state_monitor_returns_singleton():
    from python.helpers.state_monitor import get_state_monitor, _reset_state_monitor_for_testing

    _reset_state_monitor_for_testing()
    m1 = get_state_monitor()
    m2 = get_state_monitor()
    assert m1 is m2


# --- register_sid / unregister_sid ---


def test_register_sid_creates_projection():
    from python.helpers.state_monitor import StateMonitor

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    assert ("/ns", "sid-1") in monitor._projections
    monitor.unregister_sid("/ns", "sid-1")
    assert ("/ns", "sid-1") not in monitor._projections


def test_unregister_sid_cancels_pending_handles():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    monitor = StateMonitor(debounce_seconds=10.0)
    monitor.register_sid("/ns", "sid-1")
    monitor.bind_manager(type("M", (), {"_dispatcher_loop": None})())
    monitor.update_projection(
        "/ns", "sid-1",
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.mark_dirty("/ns", "sid-1")
    handle = monitor._debounce_handles.get(("/ns", "sid-1"))
    monitor.unregister_sid("/ns", "sid-1")
    assert handle is None or handle.cancelled()


# --- mark_dirty_all ---


def test_mark_dirty_all_marks_all_registered_sids():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    monitor.register_sid("/ns", "sid-2")
    monitor.bind_manager(type("M", (), {"_dispatcher_loop": None})())
    monitor.update_projection(
        "/ns", "sid-1",
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.update_projection(
        "/ns", "sid-2",
        request=StateRequestV1(context=None, log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.mark_dirty_all(reason="test")
    assert monitor._projections[("/ns", "sid-1")].dirty_version >= 1
    assert monitor._projections[("/ns", "sid-2")].dirty_version >= 1


# --- mark_dirty_for_context ---


def test_mark_dirty_for_context_skips_empty_context_id():
    from python.helpers.state_monitor import StateMonitor

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    monitor.mark_dirty_for_context("", reason="test")
    monitor.mark_dirty_for_context("   ", reason="test")
    # Should not raise; empty/whitespace context_id is skipped
    assert ("/ns", "sid-1") in monitor._projections


def test_mark_dirty_for_context_marks_only_matching_context():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-a")
    monitor.register_sid("/ns", "sid-b")
    monitor.bind_manager(type("M", (), {"_dispatcher_loop": None})())
    monitor.update_projection(
        "/ns", "sid-a",
        request=StateRequestV1(context="ctx-1", log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.update_projection(
        "/ns", "sid-b",
        request=StateRequestV1(context="ctx-2", log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=1,
    )
    monitor.mark_dirty_for_context("ctx-1", reason="test")
    assert monitor._projections[("/ns", "sid-a")].dirty_version >= 1
    assert monitor._projections[("/ns", "sid-b")].dirty_version == 0


# --- update_projection ---


def test_update_projection_sets_request_and_seq_base():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    request = StateRequestV1(
        context="ctx-1",
        log_from=5,
        notifications_from=3,
        timezone="Europe/London",
    )
    monitor.update_projection("/ns", "sid-1", request=request, seq_base=10)
    proj = monitor._projections[("/ns", "sid-1")]
    assert proj.request == request
    assert proj.seq_base == 10
    assert proj.seq == 10


# --- _debug_state ---


def test_debug_state_returns_identities_and_handles():
    from python.helpers.state_monitor import StateMonitor

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    state = monitor._debug_state()
    assert "identities" in state
    assert "handles" in state
    assert ("/ns", "sid-1") in state["identities"]


# --- mark_dirty does not schedule when seq_base is 0 ---


def test_mark_dirty_does_not_schedule_before_seq_base_set():
    from python.helpers.state_monitor import StateMonitor

    monitor = StateMonitor()
    monitor.register_sid("/ns", "sid-1")
    monitor.bind_manager(type("M", (), {"_dispatcher_loop": None})())
    # Do NOT call update_projection - seq_base stays 0
    monitor.mark_dirty("/ns", "sid-1", reason="test")
    # Should not have scheduled a push (seq_base <= 0 gates scheduling)
    assert ("/ns", "sid-1") not in monitor._debounce_handles
