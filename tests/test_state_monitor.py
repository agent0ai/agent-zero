import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_state_monitor_defaults_to_ten_pushes_per_second() -> None:
    from helpers.state_monitor import StateMonitor

    assert StateMonitor().debounce_seconds == 0.1


@pytest.mark.asyncio
async def test_state_monitor_debounce_coalesces_without_postponing_and_cleanup_cancels_pending():
    from helpers.state_monitor import StateMonitor
    from helpers.state_snapshot import StateRequestV1

    namespace = "/ws"
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

    from helpers.state_monitor import StateMonitor
    from helpers.state_snapshot import StateRequestV1

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
    monkeypatch.setattr("helpers.state_monitor.build_snapshot_from_request", _fake_snapshot)

    monitor.mark_dirty(ns_a, sid, reason="test")
    await asyncio.wait_for(push_ready.wait(), timeout=1.0)

    assert captured
    assert all(ns == ns_a for ns, _ in captured)


@pytest.mark.asyncio
async def test_collection_delta_tracks_full_and_stream_dirty_waves(monkeypatch) -> None:
    import asyncio

    import helpers.state_monitor as state_monitor_module
    from helpers.state_monitor import StateMonitor
    from helpers.state_snapshot import StateRequestV1

    namespace = "/ws"
    sid = "sid-delta"
    identity = (namespace, sid)
    include_calls: list[bool] = []
    emitted: list[dict] = []

    async def fake_snapshot(*, request, include_collections=True):
        include_calls.append(include_collections)
        return {
            "deselect_chat": False,
            "context": request.context or "",
            "contexts": [] if include_collections else None,
            "tasks": [] if include_collections else None,
            "logs": [],
            "log_guid": "guid",
            "log_version": request.log_from,
            "log_progress": "",
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "notifications",
            "notifications_version": request.notifications_from,
        }

    class FakeManager:
        def __init__(self, loop):
            self._dispatcher_loop = loop

        async def emit_to(self, _namespace, _sid, _event_type, payload, **_kwargs):
            emitted.append(payload["snapshot"])

    monitor = StateMonitor(debounce_seconds=60.0)
    monitor.bind_manager(FakeManager(asyncio.get_running_loop()))
    monitor.register_sid(namespace, sid)
    monitor.update_projection(
        namespace,
        sid,
        request=StateRequestV1(
            context="ctx",
            log_from=0,
            notifications_from=0,
            timezone="UTC",
            collections_delta=True,
        ),
        seq_base=1,
    )
    monkeypatch.setattr(
        state_monitor_module,
        "build_snapshot_from_request",
        fake_snapshot,
    )

    async def flush() -> None:
        handle = monitor._debounce_handles.pop(identity)
        handle.cancel()
        await monitor._flush_push(identity)

    monitor.mark_dirty(namespace, sid, include_collections=False)
    await flush()

    monitor.mark_dirty(namespace, sid, include_collections=False)
    monitor.mark_dirty(namespace, sid, include_collections=True)
    await flush()

    monitor.update_projection(
        namespace,
        sid,
        request=StateRequestV1(
            context="ctx",
            log_from=0,
            notifications_from=0,
            timezone="UTC",
        ),
        seq_base=1,
    )
    monitor.mark_dirty(namespace, sid, include_collections=False)
    await flush()

    assert include_calls == [False, True, True]
    assert emitted[0]["contexts"] is None
    assert emitted[0]["tasks"] is None
    assert emitted[1]["contexts"] == []
    assert emitted[2]["contexts"] == []
