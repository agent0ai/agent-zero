"""A timed-out MCP worker must not be left spinning.

Before this fix the timeout path abandoned the worker. A worker whose event
loop keeps cycling then spins at 100% CPU holding the GIL for the lifetime of
the process; observed in the wild at 11h55m of CPU on a single leaked thread.
"""
import asyncio
import threading
import time

from helpers.defer import DeferredTask
from helpers.mcp_handler import _stop_worker_loop


async def _spinner():
    # Keeps the loop RUNNING (and burning CPU) rather than blocking it --
    # this is the state a wedged MCP worker is actually left in.
    while True:
        await asyncio.sleep(0)


def test_stop_worker_loop_ends_spin_without_blocking_caller():
    task = DeferredTask(thread_name=f"test-mcp-spin-{threading.get_ident()}")
    task.start_task(_spinner)
    try:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            loop = task.event_loop_thread.loop
            if loop is not None and loop.is_running():
                break
            time.sleep(0.05)
        thread = task.event_loop_thread.thread
        assert thread is not None and thread.is_alive()

        started = time.monotonic()
        task.kill(terminate_thread=False)
        _stop_worker_loop(task)
        elapsed = time.monotonic() - started

        # Must not wait on the wedged loop: no drain, no join.
        assert elapsed < 1.0, f"caller blocked for {elapsed:.2f}s"

        thread.join(timeout=10)
        assert not thread.is_alive(), "worker thread survived; it would spin forever"
    finally:
        loop = getattr(task.event_loop_thread, "loop", None)
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)


def test_stop_worker_loop_is_safe_when_loop_already_gone():
    task = DeferredTask(thread_name=f"test-mcp-gone-{threading.get_ident()}")
    task.kill(terminate_thread=True)
    _stop_worker_loop(task)  # must not raise
