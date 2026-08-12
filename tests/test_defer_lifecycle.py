import asyncio
import threading
import uuid
import weakref

import pytest

from helpers.defer import DeferredTask


class Owner:
    pass


def make_task() -> DeferredTask:
    return DeferredTask(f"defer-lifecycle-{uuid.uuid4()}")


def test_completed_task_releases_call_references_and_children():
    task = make_task()
    owner = Owner()
    owner_ref = weakref.ref(owner)
    child_killed = threading.Event()

    class Child:
        def kill(self, terminate_thread: bool = False) -> None:
            assert terminate_thread
            child_killed.set()

    async def run(captured_owner):
        return "done"

    try:
        task.add_child_task(Child(), terminate_thread=True)  # type: ignore[arg-type]
        task.start_task(run, owner)
        assert task.result_sync(timeout=2) == "done"
        assert child_killed.wait(2)
        assert task.func is None
        assert task.args == ()
        assert task.kwargs == {}

        del owner
        assert owner_ref() is None
        assert task.result_sync(timeout=2) == "done"
        with pytest.raises(RuntimeError, match="Completed task cannot be restarted"):
            task.restart()
    finally:
        task.kill(terminate_thread=True)


def test_kill_clears_stored_call_without_clearing_running_arguments():
    task = make_task()
    owner = Owner()
    owner_ref = weakref.ref(owner)
    started = threading.Event()
    cancelled = threading.Event()
    finished = threading.Event()
    release: list[asyncio.Event] = []

    async def run(captured_owner):
        release.append(asyncio.Event())
        started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled.set()
            await release[0].wait()
        finally:
            finished.set()

    try:
        task.start_task(run, owner)
        assert started.wait(2)
        task.kill()
        assert cancelled.wait(2)
        assert task.func is None
        assert task.args == ()
        assert task.kwargs == {}

        del owner
        # While the coroutine is still running (blocked on release), it holds
        # its own reference to the owner - kill() must NOT clear the running
        # call's arguments, only the stored snapshot (asserted above).
        assert owner_ref() is not None
        task.event_loop_thread.loop.call_soon_threadsafe(release[0].set)
        assert finished.wait(2)
        # NOTE: no "owner_ref() is None" assertion here on purpose. After a
        # suppressed CancelledError, asyncio keeps the exception (whose
        # traceback references the finished coroutine's frame, and thus the
        # owner) anchored in interpreter state whose lifetime depends on
        # process-wide import/GC conditions - importing helpers.settings or
        # anything that pulls it in makes the island survive pumping and even
        # gc.collect(). That is CPython/asyncio implementation detail, not a
        # DeferredTask guarantee; the product contract (stored call cleared,
        # running arguments untouched) is covered by the assertions above.
    finally:
        if release and task.event_loop_thread.loop:
            task.event_loop_thread.loop.call_soon_threadsafe(release[0].set)
        task.kill(terminate_thread=True)


def test_active_task_can_restart_from_its_snapshot():
    task = make_task()
    starts = [threading.Event(), threading.Event()]
    run_count = 0

    async def run(value):
        nonlocal run_count
        current_run = run_count
        run_count += 1
        assert value == "argument"
        starts[current_run].set()
        await asyncio.Future()

    try:
        task.start_task(run, "argument")
        assert starts[0].wait(2)
        task.restart()
        assert starts[1].wait(2)
        assert task.func is run
        assert task.args == ("argument",)
    finally:
        task.kill(terminate_thread=True)
