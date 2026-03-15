"""Tests for python/helpers/defer.py."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- EventLoopThread ---


class TestEventLoopThread:
    def test_event_loop_thread_singleton_per_name(self):
        from python.helpers.defer import EventLoopThread, THREAD_BACKGROUND

        try:
            with patch("python.helpers.defer.EventLoopThread._start"):
                with patch("python.helpers.defer.EventLoopThread._lock"):
                    t1 = EventLoopThread(THREAD_BACKGROUND)
                    t2 = EventLoopThread(THREAD_BACKGROUND)
                    assert t1 is t2
        finally:
            EventLoopThread._instances.clear()

    def test_event_loop_thread_different_names_different_instances(self):
        from python.helpers.defer import EventLoopThread

        try:
            with patch("python.helpers.defer.EventLoopThread._start"):
                with patch("python.helpers.defer.EventLoopThread._lock"):
                    t1 = EventLoopThread("thread_a")
                    t2 = EventLoopThread("thread_b")
                    assert t1 is not t2
        finally:
            EventLoopThread._instances.pop("thread_a", None)
            EventLoopThread._instances.pop("thread_b", None)


# --- DeferredTask ---


class TestDeferredTask:
    def test_start_task_runs_coroutine(self):
        from python.helpers.defer import DeferredTask

        async def sample_task():
            return 42

        mock_future = asyncio.Future()
        mock_future.set_result(42)
        mock_elt = MagicMock()
        mock_elt.run_coroutine = MagicMock(return_value=mock_future)
        mock_elt.loop = MagicMock()

        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            task = DeferredTask()
            task.start_task(sample_task)
            assert task.is_ready()
            assert task.result_sync(timeout=0.1) == 42

    def test_start_task_raises_before_start_for_result_sync(self):
        from python.helpers.defer import DeferredTask

        with patch("python.helpers.defer.EventLoopThread"):
            task = DeferredTask()
            with pytest.raises(RuntimeError, match="hasn't been started"):
                task.result_sync()

    def test_is_ready_false_before_start(self):
        from python.helpers.defer import DeferredTask

        with patch("python.helpers.defer.EventLoopThread"):
            task = DeferredTask()
            assert task.is_ready() is False

    def test_is_alive_true_while_running(self):
        from python.helpers.defer import DeferredTask

        async def slow_task():
            await asyncio.sleep(10)

        mock_future = asyncio.Future()
        mock_elt = MagicMock()
        mock_elt.run_coroutine = MagicMock(return_value=mock_future)
        mock_elt.loop = MagicMock()

        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            task = DeferredTask()
            task.start_task(slow_task)
            assert task.is_alive() is True

    def test_kill_cancels_future(self):
        from python.helpers.defer import DeferredTask

        async def never_ends():
            while True:
                await asyncio.sleep(1)

        mock_future = asyncio.Future()
        mock_elt = MagicMock()
        mock_elt.run_coroutine = MagicMock(return_value=mock_future)
        mock_elt.loop = MagicMock()

        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            task = DeferredTask()
            task.start_task(never_ends)
            task.kill()
            assert mock_future.cancelled()

    def test_add_child_task(self):
        from python.helpers.defer import DeferredTask, ChildTask

        with patch("python.helpers.defer.EventLoopThread"):
            parent = DeferredTask()
            child = DeferredTask()
            parent.add_child_task(child, terminate_thread=False)
            assert len(parent.children) == 1
            assert isinstance(parent.children[0], ChildTask)
            assert parent.children[0].task is child
            assert parent.children[0].terminate_thread is False

    def test_kill_children_clears_children_list(self):
        from python.helpers.defer import DeferredTask, ChildTask

        mock_elt = MagicMock()
        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            parent = DeferredTask()
            child = DeferredTask()
            child._future = None
            child.kill = MagicMock()
            parent.children = [ChildTask(task=child, terminate_thread=False)]
            parent.kill_children()
            assert len(parent.children) == 0
            child.kill.assert_called_once_with(terminate_thread=False)


# --- ChildTask ---


class TestChildTask:
    def test_child_task_dataclass(self):
        from python.helpers.defer import ChildTask, DeferredTask

        with patch("python.helpers.defer.EventLoopThread"):
            task = DeferredTask()
            ct = ChildTask(task=task, terminate_thread=True)
            assert ct.task is task
            assert ct.terminate_thread is True


# --- execute_inside ---


@pytest.mark.asyncio
class TestExecuteInside:
    async def test_execute_inside_runs_func_when_loop_is_current(self):
        from python.helpers.defer import DeferredTask

        # Use the current event loop so run_coroutine_threadsafe actually runs the coro
        mock_elt = MagicMock()
        mock_elt.loop = asyncio.get_running_loop()
        mock_elt.run_coroutine = MagicMock()

        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            task = DeferredTask()
            future = task.execute_inside(lambda: 42)
            result = await asyncio.wait_for(future, timeout=1.0)
            assert result == 42

    def test_execute_inside_raises_when_loop_not_initialized(self):
        from python.helpers.defer import DeferredTask

        mock_elt = MagicMock()
        mock_elt.loop = None
        with patch("python.helpers.defer.EventLoopThread", return_value=mock_elt):
            task = DeferredTask()
            with pytest.raises(RuntimeError, match="not initialized"):
                task.execute_inside(lambda: 1)
