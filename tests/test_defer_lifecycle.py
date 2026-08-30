import asyncio
import threading
import time
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


def test_run_task_end_extension_marks_state_dirty_after_completion(monkeypatch):
    from extensions.python._functions.agent.AgentContext.run_task.end import (
        _10_mark_state_dirty as task_done_extension,
    )

    task = make_task()
    callback_called = threading.Event()
    observations: list[tuple[str | None, bool]] = []

    def mark_dirty(*, reason=None):
        observations.append((reason, bool(task.is_alive())))
        callback_called.set()

    monkeypatch.setattr(
        task_done_extension,
        "mark_dirty_all",
        mark_dirty,
    )

    async def run():
        return "done"

    try:
        with pytest.raises(RuntimeError, match="Task hasn't been started"):
            task.add_done_callback(lambda _future: None)
        task.start_task(run)
        task_done_extension.MarkStateDirty(agent=None).execute(
            data={"result": task}
        )
        assert task.result_sync(timeout=2) == "done"
        assert callback_called.wait(2)
        assert observations == [("agent.AgentContext.run_task_done", False)]
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
        assert owner_ref() is not None
        task.event_loop_thread.loop.call_soon_threadsafe(release[0].set)
        assert finished.wait(2)
        asyncio.run_coroutine_threadsafe(
            asyncio.sleep(0), task.event_loop_thread.loop
        ).result(2)
        assert owner_ref() is None
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


def wait_until(predicate, timeout: float = 5.0) -> bool:
    """Polls ``predicate`` until it holds, so teardown need not be raced.

    Teardown finishes on the loop's own thread in one case, so there is no
    future to wait on -- but polling still fails within the timeout rather than
    passing on a sleep that happened to be long enough.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_killing_one_task_does_not_cancel_siblings_on_the_shared_thread():
    """``EventLoopThread`` instances are shared by name, so one task's
    ``kill(terminate_thread=True)`` used to stop a loop that its siblings were
    still running on, cancelling their work.

    ``TaskScheduler`` passes a single fixed thread name for every scheduled
    task (`helpers/task_scheduler.py`), so deleting one running task took down
    every other running task in the process. The cancellation surfaces only on
    the abandoned task's own future, so nothing reported it.
    """
    name = f"defer-shared-{uuid.uuid4()}"
    victim, survivor = DeferredTask(name), DeferredTask(name)
    assert victim.event_loop_thread is survivor.event_loop_thread

    victim_started = threading.Event()
    survivor_started = threading.Event()
    progress: list[int] = []

    async def blocks_forever():
        victim_started.set()
        await asyncio.Future()

    async def keeps_working():
        survivor_started.set()
        for step in range(10):
            await asyncio.sleep(0.05)
            progress.append(step)
        return "finished"

    try:
        victim.start_task(blocks_forever)
        survivor.start_task(keeps_working)
        assert victim_started.wait(5) and survivor_started.wait(5)

        victim.kill(terminate_thread=True)

        # The survivor's own result, not a progress count: a cancelled task
        # would raise here, while asserting only that the counter advanced
        # could pass on work done before the kill landed.
        assert survivor.result_sync(timeout=5) == "finished"
    finally:
        survivor.kill(terminate_thread=True)
        victim.kill(terminate_thread=True)


def test_last_task_to_be_killed_still_tears_the_thread_down():
    """Deferring teardown to the last user must not mean never tearing down.

    Otherwise the fix for the shared-thread cancellation would trade it for a
    thread leak, which matters most for the per-request thread names
    (``BrowserRuntime-<context>``) that are created and discarded constantly.
    """
    name = f"defer-teardown-{uuid.uuid4()}"
    first, second = DeferredTask(name), DeferredTask(name)
    event_loop_thread = first.event_loop_thread
    loop, thread = event_loop_thread.loop, event_loop_thread.thread
    assert loop is not None and thread is not None

    async def idle():
        await asyncio.Future()

    first.start_task(idle)
    second.start_task(idle)

    first.kill(terminate_thread=True)
    assert not loop.is_closed(), "the loop went down while a sibling still held it"

    second.kill(terminate_thread=True)
    assert wait_until(lambda: loop.is_closed()), "the loop outlived its last user"
    assert wait_until(lambda: not thread.is_alive()), "the thread outlived its loop"


def test_a_new_task_after_teardown_gets_a_working_thread():
    """Reusing a thread name after it was torn down must not hand back a dead
    loop: instances are cached by name, and a terminated one stays cached until
    it is replaced.

    This one passes on the unfixed code too. It is here as a guard on the fix
    rather than on the bug: teardown now leaves a closed loop attached in the
    in-loop case, so ``_start`` has to treat a closed loop as absent. The
    reuse-after-teardown path is what would break if it did not.
    """
    name = f"defer-reuse-{uuid.uuid4()}"
    first = DeferredTask(name)

    async def done():
        return "first"

    first.start_task(done)
    assert first.result_sync(timeout=5) == "first"
    first.kill(terminate_thread=True)

    second = DeferredTask(name)

    async def again():
        return "second"

    try:
        second.start_task(again)
        assert second.result_sync(timeout=5) == "second"
    finally:
        second.kill(terminate_thread=True)


def test_killing_from_the_loops_own_thread_does_not_deadlock():
    """A task's done-callback runs *on* the loop thread, and it kills children.

    A child that shares the parent's thread therefore reached
    ``kill(terminate_thread=True)`` from inside the loop, where the old code
    waited on ``run_coroutine_threadsafe(...).result()`` with no timeout -- a
    coroutine that only that thread can advance. The thread wedged permanently,
    taking every task on it with it.
    """
    name = f"defer-own-thread-{uuid.uuid4()}"
    child = DeferredTask(name)
    parent = DeferredTask(name)
    parent.add_child_task(child, terminate_thread=True)
    loop = parent.event_loop_thread.loop
    assert loop is not None

    child_started = threading.Event()

    async def child_body():
        child_started.set()
        await asyncio.Future()

    async def parent_body():
        return "parent done"

    try:
        child.start_task(child_body)
        assert child_started.wait(5)
        parent.start_task(parent_body)
        assert parent.result_sync(timeout=5) == "parent done"

        # Probed by scheduling onto the loop rather than by elapsed time: the
        # parent's result arrives before the done-callback runs, so a wedge
        # would otherwise go unnoticed here.
        assert wait_until(lambda: child._future is not None and child._future.done())
        probe = asyncio.run_coroutine_threadsafe(asyncio.sleep(0), loop)
        probe.result(timeout=5)
    finally:
        parent.kill(terminate_thread=True)


def test_teardown_requested_from_inside_the_loop_still_completes():
    """The in-loop teardown path cannot join its own thread or close a loop that
    is still running, so it chains the drain and the stop onto the loop. It must
    still finish, and it must leave the instance reusable rather than holding a
    closed loop.

    ``kill()`` is invoked on the loop directly here. The refcount checked above
    is what keeps a shared thread from reaching this branch, so within the
    current tree there is no indirect route to it -- but ``__del__`` calls
    ``kill()`` from wherever the last reference happens to be dropped, so the
    branch has to hold on its own.
    """
    name = f"defer-in-loop-{uuid.uuid4()}"
    task = DeferredTask(name)
    event_loop_thread = task.event_loop_thread
    loop, thread = event_loop_thread.loop, event_loop_thread.thread
    assert loop is not None and thread is not None

    started = threading.Event()

    async def idle():
        started.set()
        await asyncio.Future()

    task.start_task(idle)
    assert started.wait(5)

    loop.call_soon_threadsafe(lambda: task.kill(terminate_thread=True))

    assert wait_until(lambda: loop.is_closed()), "the loop never closed"
    assert wait_until(lambda: not thread.is_alive()), "the thread never stopped"

    # The in-loop path cannot null out ``loop``/``thread``, so a later task on
    # the same name would otherwise be handed the closed loop.
    successor = DeferredTask(name)

    async def done():
        return "reusable"

    try:
        successor.start_task(done)
        assert successor.result_sync(timeout=5) == "reusable"
    finally:
        successor.kill(terminate_thread=True)


def test_a_restarted_task_keeps_its_claim_on_the_thread():
    """``restart()`` goes through ``kill()``, which drops the task's claim.

    Without re-registering, a sibling's later ``kill(terminate_thread=True)``
    would see a count that no longer includes the restarted task and stop the
    loop underneath it.
    """
    name = f"defer-restart-{uuid.uuid4()}"
    restarted = DeferredTask(name)
    sibling = DeferredTask(name)
    starts = [threading.Event(), threading.Event()]
    run_count = 0
    progress: list[int] = []

    async def run(value):
        nonlocal run_count
        current = run_count
        run_count += 1
        starts[current].set()
        if current == 0:
            await asyncio.Future()
        for step in range(10):
            await asyncio.sleep(0.05)
            progress.append(step)
        return f"restarted:{value}"

    async def idle():
        await asyncio.Future()

    try:
        sibling.start_task(idle)
        restarted.start_task(run, "argument")
        assert starts[0].wait(5)
        restarted.restart()
        assert starts[1].wait(5)

        sibling.kill(terminate_thread=True)

        assert restarted.result_sync(timeout=5) == "restarted:argument"
    finally:
        restarted.kill(terminate_thread=True)
        sibling.kill(terminate_thread=True)


def test_killing_the_same_task_twice_does_not_release_the_thread_twice():
    """``kill()`` is called from ``__del__`` as well as explicitly, and
    ``close_runtime_sync`` kills in a ``finally`` after a task that may already
    have been killed. A double release would drop a sibling's claim."""
    name = f"defer-double-kill-{uuid.uuid4()}"
    killed_twice = DeferredTask(name)
    sibling = DeferredTask(name)
    progress: list[int] = []

    async def idle():
        await asyncio.Future()

    async def keeps_working():
        for step in range(10):
            await asyncio.sleep(0.05)
            progress.append(step)
        return "finished"

    try:
        killed_twice.start_task(idle)
        sibling.start_task(keeps_working)

        killed_twice.kill(terminate_thread=True)
        killed_twice.kill(terminate_thread=True)

        assert sibling.result_sync(timeout=5) == "finished"
    finally:
        sibling.kill(terminate_thread=True)
