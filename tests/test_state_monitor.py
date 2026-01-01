import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.asyncio
async def test_state_monitor_debounce_coalesces_without_postponing_and_cleanup_cancels_pending():
    from python.helpers.state_monitor import StateMonitor

    monitor = StateMonitor(debounce_seconds=10.0)
    monitor.register_sid("sid-1")
    monitor.bind_manager(type("FakeManager", (), {"_dispatcher_loop": None})())
    monitor.update_projection(
        "sid-1",
        context=None,
        log_from=0,
        notifications_from=0,
        timezone="UTC",
        seq_base=1,
    )

    monitor.mark_dirty("sid-1")
    first = monitor._debounce_handles["sid-1"]

    monitor.mark_dirty("sid-1")
    second = monitor._debounce_handles["sid-1"]

    # Throttled coalescing: subsequent dirties keep the scheduled push instead of postponing it.
    assert first is second
    assert not second.cancelled()

    monitor.unregister_sid("sid-1")
    assert second.cancelled()
    assert "sid-1" not in monitor._debounce_handles
