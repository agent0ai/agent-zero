"""
Tests for per-context event loop isolation.

Verifies that:
1. EventLoopThread creates separate threads for different names
2. AgentContext.run_task() uses a per-context thread name
3. Context removal terminates the thread (terminate_thread=True)
4. Context replacement terminates the old thread
"""
import asyncio
import importlib.util
import threading
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# defer.py is self-contained — register in sys.modules before exec so @dataclass works
import sys as _sys
_spec = importlib.util.spec_from_file_location(
    "defer",
    PROJECT_ROOT / "python" / "helpers" / "defer.py",
)
_mod = importlib.util.module_from_spec(_spec)
_sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
EventLoopThread = _mod.EventLoopThread
DeferredTask = _mod.DeferredTask


# ─── EventLoopThread isolation ────────────────────────────────────────────────

class TestEventLoopThreadIsolation:
    """Each unique thread_name must produce a separate thread and event loop."""

    def _cleanup_threads(self, names):
        for name in names:
            with EventLoopThread._lock:
                inst = EventLoopThread._instances.pop(name, None)
            if inst:
                try:
                    inst.terminate()
                except Exception:
                    pass

    def test_different_names_create_different_threads(self):
        names = ["test-iso-A", "test-iso-B"]
        try:
            a = EventLoopThread("test-iso-A")
            b = EventLoopThread("test-iso-B")
            assert a is not b
            assert a.thread is not b.thread
            assert a.loop is not b.loop
        finally:
            self._cleanup_threads(names)

    def test_same_name_returns_singleton(self):
        name = "test-iso-singleton"
        try:
            a = EventLoopThread(name)
            b = EventLoopThread(name)
            assert a is b
        finally:
            self._cleanup_threads([name])

    def test_terminate_removes_from_registry(self):
        name = "test-iso-terminate"
        t = EventLoopThread(name)
        assert name in EventLoopThread._instances
        t.terminate()
        assert name not in EventLoopThread._instances

    def test_coroutine_runs_on_correct_thread(self):
        names = ["test-iso-thread-X", "test-iso-thread-Y"]
        try:
            x = EventLoopThread("test-iso-thread-X")
            y = EventLoopThread("test-iso-thread-Y")

            results = {}

            async def capture_thread(label):
                results[label] = threading.current_thread().name

            fx = x.run_coroutine(capture_thread("x"))
            fy = y.run_coroutine(capture_thread("y"))
            fx.result(timeout=5)
            fy.result(timeout=5)

            assert results["x"] == "test-iso-thread-X"
            assert results["y"] == "test-iso-thread-Y"
            assert results["x"] != results["y"]
        finally:
            self._cleanup_threads(names)


# ─── DeferredTask thread lifecycle ────────────────────────────────────────────

class TestDeferredTaskTermination:

    def test_kill_with_terminate_stops_thread(self):
        name = "test-defer-term"
        task = DeferredTask(thread_name=name)

        async def noop():
            return 42

        task.start_task(noop)
        task._future.result(timeout=5)

        assert name in EventLoopThread._instances
        task.kill(terminate_thread=True)
        assert name not in EventLoopThread._instances

    def test_kill_without_terminate_keeps_thread(self):
        name = "test-defer-keep"
        try:
            task = DeferredTask(thread_name=name)

            async def noop():
                return 1

            task.start_task(noop)
            task._future.result(timeout=5)

            task.kill(terminate_thread=False)
            assert name in EventLoopThread._instances
        finally:
            with EventLoopThread._lock:
                inst = EventLoopThread._instances.pop(name, None)
            if inst:
                inst.terminate()


# ─── Stuck task isolation ─────────────────────────────────────────────────────

class TestStuckTaskIsolation:
    """A blocked coroutine on one thread must not prevent another thread
    from executing its coroutines."""

    def test_blocked_task_does_not_block_other_thread(self):
        names = ["test-stuck-A", "test-stuck-B"]
        try:
            stuck_event = asyncio.Event()

            async def blocking():
                await asyncio.sleep(60)

            async def quick():
                return "done"

            task_a = DeferredTask(thread_name="test-stuck-A")
            task_a.start_task(blocking)

            task_b = DeferredTask(thread_name="test-stuck-B")
            task_b.start_task(quick)

            result = task_b._future.result(timeout=5)
            assert result == "done"
            assert not task_a._future.done()
        finally:
            for name in names:
                with EventLoopThread._lock:
                    inst = EventLoopThread._instances.pop(name, None)
                if inst:
                    inst.terminate()


# ─── AgentContext.run_task thread_name ─────────────────────────────────────────

class TestAgentContextThreadName:
    """Verify that run_task uses f'AgentCtx-{self.id}' as thread_name,
    ensuring per-context isolation. We extract and inspect the source
    to avoid importing the full Agent Zero dependency tree."""

    def test_run_task_uses_per_context_thread_name(self):
        import ast

        source = (PROJECT_ROOT / "agent.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != "AgentContext":
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef) or item.name != "run_task":
                    continue
                src_segment = ast.get_source_segment(source, item)
                assert src_segment is not None, "Could not extract run_task source"
                assert "AgentCtx-" in src_segment, (
                    "run_task must use per-context thread_name like f'AgentCtx-{self.id}'"
                )
                assert "self.__class__.__name__" not in src_segment, (
                    "run_task must NOT use self.__class__.__name__ (shared singleton)"
                )
                return

        pytest.fail("AgentContext.run_task not found in agent.py")

    def test_remove_terminates_thread(self):
        """Verify AgentContext.remove() passes terminate_thread=True."""
        import ast

        source = (PROJECT_ROOT / "agent.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != "AgentContext":
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef) or item.name != "remove":
                    continue
                src_segment = ast.get_source_segment(source, item)
                assert src_segment is not None
                assert "terminate_thread=True" in src_segment, (
                    "remove() must call task.kill(terminate_thread=True)"
                )
                return

        pytest.fail("AgentContext.remove not found in agent.py")

    def test_init_replacement_terminates_thread(self):
        """Verify AgentContext.__init__ passes terminate_thread=True
        when killing a replaced context's task."""
        import ast

        source = (PROJECT_ROOT / "agent.py").read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != "AgentContext":
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef) or item.name != "__init__":
                    continue
                src_segment = ast.get_source_segment(source, item)
                assert src_segment is not None
                assert "terminate_thread=True" in src_segment, (
                    "__init__ must call existing.task.kill(terminate_thread=True)"
                )
                return

        pytest.fail("AgentContext.__init__ not found in agent.py")
