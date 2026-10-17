import asyncio
import gc
import threading
import traceback
import uuid

import pytest

from helpers.defer import DeferredTask


def make_worker():
    return DeferredTask(f"defer-cancellation-{uuid.uuid4()}")


def test_execute_inside_propagates_worker_cancellation():
    worker = make_worker()

    async def cancelled_operation():
        raise asyncio.CancelledError

    async def run():
        result = worker.execute_inside(cancelled_operation)
        done, _ = await asyncio.wait([result], timeout=2)
        assert result in done, "A cancelled worker left its caller pending"
        with pytest.raises(asyncio.CancelledError):
            await result

    try:
        asyncio.run(run())
    finally:
        worker.kill(terminate_thread=True)


def test_execute_inside_cancellation_stops_the_worker_operation():
    worker = make_worker()
    started = threading.Event()
    cancelled = threading.Event()

    async def operation():
        started.set()
        try:
            await asyncio.Future()
        finally:
            cancelled.set()

    async def run():
        result = worker.execute_inside(operation)
        assert await asyncio.to_thread(started.wait, 2)
        result.cancel()
        with pytest.raises(asyncio.CancelledError):
            await result
        assert await asyncio.to_thread(cancelled.wait, 2), (
            "Cancelling the caller left the worker operation running"
        )

    try:
        asyncio.run(run())
    finally:
        worker.kill(terminate_thread=True)


def test_execute_inside_cancellation_keeps_shared_loop_and_sibling_alive():
    worker = make_worker()
    cancelled = threading.Event()
    sibling_started = threading.Event()
    sibling_release = threading.Event()

    async def operation():
        try:
            await asyncio.Future()
        finally:
            cancelled.set()

    async def sibling():
        sibling_started.set()
        await asyncio.to_thread(sibling_release.wait, 2)
        return "sibling result"

    async def run():
        result = worker.execute_inside(operation)
        sibling_result = worker.execute_inside(sibling)
        assert await asyncio.to_thread(sibling_started.wait, 2)
        result.cancel()
        assert await asyncio.to_thread(cancelled.wait, 2)
        assert worker.event_loop_thread.loop.is_running()
        sibling_release.set()
        assert await asyncio.wait_for(sibling_result, 2) == "sibling result"
        assert await worker.execute_inside(lambda: "still works") == "still works"

    try:
        asyncio.run(run())
    finally:
        sibling_release.set()
        worker.kill(terminate_thread=True)


@pytest.mark.parametrize("mode", ["synchronous", "coroutine", "nested_awaitable"])
def test_execute_inside_preserves_results(mode):
    worker = make_worker()

    async def async_result():
        return "result"

    async def nested_result():
        return async_result()

    operation = {
        "synchronous": lambda: "result",
        "coroutine": async_result,
        "nested_awaitable": nested_result,
    }[mode]

    async def run():
        assert await worker.execute_inside(operation) == "result"

    try:
        asyncio.run(run())
    finally:
        worker.kill(terminate_thread=True)


@pytest.mark.parametrize("mode", ["synchronous", "coroutine", "nested_awaitable"])
def test_execute_inside_preserves_exception(mode):
    worker = make_worker()
    error = ValueError("test error")

    def raise_error():
        raise error

    async def async_error():
        raise_error()

    async def nested_error():
        return async_error()

    operation = {
        "synchronous": raise_error,
        "coroutine": async_error,
        "nested_awaitable": nested_error,
    }[mode]

    async def run():
        with pytest.raises(ValueError, match="test error") as caught:
            await worker.execute_inside(operation)
        assert caught.value is error
        assert "raise_error" in [
            frame.name for frame in traceback.extract_tb(caught.value.__traceback__)
        ]

    try:
        asyncio.run(run())
    finally:
        worker.kill(terminate_thread=True)


@pytest.mark.parametrize("late_error", [False, True])
def test_execute_inside_ignores_late_completion_after_caller_cancellation(late_error):
    worker = make_worker()
    started = threading.Event()
    finished = threading.Event()
    loop_errors = []

    async def operation():
        started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            if late_error:
                raise ValueError("error during cancellation cleanup")
            return "completed during cancellation cleanup"
        finally:
            finished.set()

    async def run():
        await worker.execute_inside(
            lambda: asyncio.get_running_loop().set_exception_handler(
                lambda loop, context: loop_errors.append(context)
            )
        )
        result = worker.execute_inside(operation)
        assert await asyncio.to_thread(started.wait, 2)
        result.cancel()
        with pytest.raises(asyncio.CancelledError):
            await result
        assert await asyncio.to_thread(finished.wait, 2)
        # Flush completion callbacks, then collect any unreferenced Task whose
        # exception would otherwise be reported by the loop on destruction.
        await worker.execute_inside(lambda: None)
        await worker.execute_inside(gc.collect)
        assert loop_errors == []
        assert await worker.execute_inside(lambda: "still works") == "still works"

    try:
        asyncio.run(run())
    finally:
        worker.kill(terminate_thread=True)


def test_execute_inside_rejects_an_uninitialized_loop():
    worker = make_worker()
    worker.kill(terminate_thread=True)

    with pytest.raises(RuntimeError, match="Event loop is not initialized"):
        worker.execute_inside(lambda: "must not run")
