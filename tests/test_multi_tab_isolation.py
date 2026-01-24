import asyncio
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.asyncio
async def test_state_monitor_per_sid_isolation_independent_snapshots_seq_and_cursors(monkeypatch):
    import python.helpers.state_monitor as state_monitor_module
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    snapshot_calls: list[dict[str, object]] = []
    emitted: list[dict[str, object]] = []

    namespace = "/state_sync"

    async def fake_build_snapshot_from_request(*, request):
        context = request.context
        log_from = request.log_from
        notifications_from = request.notifications_from
        timezone = request.timezone
        snapshot_calls.append(
            {
                "context": context,
                "log_from": log_from,
                "notifications_from": notifications_from,
                "timezone": timezone,
            }
        )
        # Return poll-shaped keys that StateMonitor expects to advance cursors from.
        return {
            "deselect_chat": False,
            "context": context or "",
            "contexts": [],
            "tasks": [],
            "logs": [],
            "log_guid": "log-guid",
            "log_version": int(log_from) + 1,
            "log_progress": "",
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "notifications-guid",
            "notifications_version": int(notifications_from) + 1,
        }

    class FakeManager:
        def __init__(self, loop):
            self._dispatcher_loop = loop

        async def emit_to(self, namespace, sid, event_type, payload, *, handler_id=None):
            emitted.append(
                {
                    "namespace": namespace,
                    "sid": sid,
                    "event_type": event_type,
                    "payload": payload,
                    "handler_id": handler_id,
                }
            )

    monkeypatch.setattr(
        state_monitor_module,
        "build_snapshot_from_request",
        fake_build_snapshot_from_request,
    )

    monitor = StateMonitor(debounce_seconds=60.0)
    loop = asyncio.get_running_loop()
    monitor.bind_manager(FakeManager(loop), handler_id="test.handler")

    monitor.register_sid(namespace, "sid-a")
    monitor.register_sid(namespace, "sid-b")

    monitor.update_projection(
        namespace,
        "sid-a",
        request=StateRequestV1(context="ctx-a", log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=10,
    )
    monitor.update_projection(
        namespace,
        "sid-b",
        request=StateRequestV1(
            context="ctx-b",
            log_from=40,
            notifications_from=7,
            timezone="Europe/Berlin",
        ),
        seq_base=100,
    )

    # Flush pushes directly to avoid relying on debounce scheduling.
    await monitor._flush_push((namespace, "sid-a"))
    await monitor._flush_push((namespace, "sid-b"))

    assert snapshot_calls == [
        {"context": "ctx-a", "log_from": 0, "notifications_from": 0, "timezone": "UTC"},
        {"context": "ctx-b", "log_from": 40, "notifications_from": 7, "timezone": "Europe/Berlin"},
    ]

    assert len(emitted) == 2
    assert {entry["sid"] for entry in emitted} == {"sid-a", "sid-b"}
    assert all(entry["event_type"] == "state_push" for entry in emitted)
    assert all(entry["handler_id"] == "test.handler" for entry in emitted)
    assert all(entry["namespace"] == namespace for entry in emitted)

    payload_a = next(entry["payload"] for entry in emitted if entry["sid"] == "sid-a")
    payload_b = next(entry["payload"] for entry in emitted if entry["sid"] == "sid-b")

    assert payload_a["seq"] == 11  # seq_base=10 -> first push increments to 11
    assert payload_b["seq"] == 101  # seq_base=100 -> first push increments to 101

    assert payload_a["snapshot"]["context"] == "ctx-a"
    assert payload_b["snapshot"]["context"] == "ctx-b"

    # Verify per-sid cursor advancement is independent.
    assert monitor._projections[(namespace, "sid-a")].request.log_from == 1
    assert monitor._projections[(namespace, "sid-a")].request.notifications_from == 1
    assert monitor._projections[(namespace, "sid-b")].request.log_from == 41
    assert monitor._projections[(namespace, "sid-b")].request.notifications_from == 8


@pytest.mark.asyncio
async def test_state_monitor_mark_dirty_for_context_scopes_to_active_context():
    from python.helpers.state_monitor import StateMonitor
    from python.helpers.state_snapshot import StateRequestV1

    monitor = StateMonitor(debounce_seconds=60.0)
    namespace = "/state_sync"
    monitor.register_sid(namespace, "sid-a")
    monitor.register_sid(namespace, "sid-b")

    monitor.update_projection(
        namespace,
        "sid-a",
        request=StateRequestV1(context="ctx-a", log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=10,
    )
    monitor.update_projection(
        namespace,
        "sid-b",
        request=StateRequestV1(context="ctx-b", log_from=0, notifications_from=0, timezone="UTC"),
        seq_base=10,
    )

    monitor.mark_dirty_for_context("ctx-a")
    assert (namespace, "sid-a") in monitor._debounce_handles
    assert (namespace, "sid-b") not in monitor._debounce_handles

    monitor.unregister_sid(namespace, "sid-a")
    monitor.unregister_sid(namespace, "sid-b")
