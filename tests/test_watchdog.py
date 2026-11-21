from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from helpers import watchdog


class RecordingObserver:
    def __init__(self):
        self.subscriptions = {}
        self.calls = []
        self.alive = False
        self.on_schedule = lambda: None

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive

    def schedule(self, handler, root, recursive):
        assert recursive
        self.on_schedule()
        handle = object()
        self.subscriptions[handle] = (handler, root)
        self.calls.append(("add", root))
        return handle

    def unschedule(self, handle):
        _, root = self.subscriptions.pop(handle)
        self.calls.append(("remove", root))

    def unschedule_all(self):
        self.subscriptions.clear()
        self.calls.append(("clear",))

    def stop(self):
        self.alive = False

    def join(self):
        pass


@pytest.fixture
def registry(monkeypatch):
    observer = RecordingObserver()
    monkeypatch.setattr(watchdog, "_WatchdogObserver", lambda: observer)
    registry = watchdog._WatchRegistry()
    yield registry, observer
    registry.clear()


def add(registry, id, *roots, handler=lambda items: None):
    registry.add(id, [str(root) for root in roots], ["*.py"], None, ["modify"], 0, handler)


def test_adding_and_removing_roots_retains_existing_subscriptions(registry, tmp_path):
    watches, observer = registry
    first, second = tmp_path / "first", tmp_path / "second"
    add(watches, "first", first)
    original = next(iter(observer.subscriptions))
    add(watches, "second", second)
    assert observer.calls == [("add", str(first)), ("add", str(second))]
    assert original in observer.subscriptions
    assert watches.remove("second")
    assert original in observer.subscriptions
    assert observer.calls[-1] == ("remove", str(second))
    watches.clear()
    assert not observer.subscriptions
    assert not observer.is_alive()
    assert not watches._scheduled_roots


def test_overlapping_roots_share_coverage_and_reconcile_parent_removal(registry, tmp_path):
    watches, observer = registry
    parent, child = tmp_path / "parent", tmp_path / "parent/child"
    add(watches, "child", child)
    add(watches, "parent", parent)
    assert [root for _, root in observer.subscriptions.values()] == [str(parent)]
    count = len(observer.calls)
    add(watches, "nested", child / "nested")
    assert len(observer.calls) == count
    watches.remove("parent")
    assert [root for _, root in observer.subscriptions.values()] == [str(child)]
    assert observer.calls[-2:] == [("remove", str(parent)), ("add", str(child))]


def test_replacing_callback_keeps_subscription_and_filters_events(registry, tmp_path):
    watches, observer = registry
    old, new = [], []
    add(watches, "test", tmp_path, handler=old.extend)
    add(watches, "test", tmp_path, handler=new.extend)
    assert observer.calls == [("add", str(tmp_path))]
    handler, _ = next(iter(observer.subscriptions.values()))
    for name, event_type in [("a.py", "modified"), ("a.txt", "modified"), ("b.py", "created")]:
        handler.dispatch(SimpleNamespace(src_path=str(tmp_path / name), event_type=event_type))
    assert not old
    assert new == [[str(tmp_path / "a.py"), "modify"]]


def test_failed_schedule_retries_without_rescanning_successful_roots(registry, tmp_path):
    watches, observer = registry
    first, second = tmp_path / "first", tmp_path / "second"
    add(watches, "first", first)
    original = next(iter(observer.subscriptions))
    def fail():
        raise OSError("watch unavailable")
    observer.on_schedule = fail
    with pytest.raises(OSError, match="watch unavailable"):
        add(watches, "second", second)
    assert original in observer.subscriptions
    observer.on_schedule = lambda: None
    add(watches, "second", second)
    assert observer.calls == [("add", str(first)), ("add", str(second))]


def test_refresh_drains_concurrent_registration_without_holding_registry_lock(registry, tmp_path):
    watches, observer = registry
    first, second = tmp_path / "first", tmp_path / "second"
    completed = threading.Event()
    def register_second():
        add(watches, "second", second)
        completed.set()
    worker = threading.Thread(target=register_second, daemon=True)
    def during_schedule():
        observer.on_schedule = lambda: None
        worker.start()
        assert completed.wait(2), "observer call held the registry lock"
    observer.on_schedule = during_schedule
    add(watches, "first", first)
    worker.join(timeout=2)
    assert {root for _, root in observer.subscriptions.values()} == {str(first), str(second)}


def test_live_events_continue_after_changing_roots():
    # Other test modules stub watchdog during collection; use the installed observer here.
    subprocess.run([sys.executable, "-c", """
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from helpers import watchdog

with TemporaryDirectory() as root:
    first, second = Path(root) / 'first', Path(root) / 'second'
    received = Event()
    try:
        watchdog.add_watchdog('first', [str(first)], patterns=['*.py'],
                              events=['modify'], handler=lambda items: received.set())
        watchdog.add_watchdog('second', [str(second)], handler=lambda items: None)
        watchdog.remove_watchdog('second')
        (first / 'event.py').write_text('updated', encoding='utf-8')
        assert received.wait(3), 'retained watch did not deliver a real filesystem event'
    finally:
        watchdog.clear_watchdogs()
"""], cwd=Path(watchdog.__file__).resolve().parents[1], check=True, timeout=10)
