import threading
from types import SimpleNamespace

from helpers.watchdog import _WatchRegistry


def test_registration_does_not_deadlock_in_flight_dispatch(tmp_path, monkeypatch):
    registry = _WatchRegistry()
    first, second, nested = [tmp_path / name for name in ('first', 'second', 'nested')]
    for path in (first, second, nested):
        path.mkdir()
    callback = None
    completed = threading.Event()
    received = []

    class Observer:
        def start(self): pass
        def stop(self): pass
        def join(self): pass
        def schedule(self, *args, **kwargs): pass
        def unschedule_all(self):
            nonlocal callback
            if callback:
                run, callback = callback, None
                thread = threading.Thread(target=run, daemon=True)
                thread.start()
                assert completed.wait(2), 'observer is waiting for a dispatch blocked on the registry lock'
                thread.join(1)

    monkeypatch.setattr(registry, '_create_observer', Observer)

    def add(name, root, handler):
        registry.add(name, [str(root)], None, None, 'all', 0, handler)

    def handler(items):
        received.extend(items)
        # A callback can register another root while a refresh is in progress.
        add('nested', nested, lambda _: None)

    add('first', first, handler)
    def dispatch():
        try:
            registry.dispatch(str(first), SimpleNamespace(event_type='modified', src_path=str(first / 'file'), is_synthetic=False))
        finally:
            completed.set()
    callback = dispatch
    add('second', second, lambda _: None)
    assert received == [[str(first / 'file'), 'modify']]
    assert registry._scheduled_roots == {str(first), str(second), str(nested)}
    registry.clear()


def test_guest_package_files_do_not_reload_live_plugins(monkeypatch):
    from helpers import plugins
    from unittest.mock import Mock
    watches = {}
    monkeypatch.setattr(plugins.watchdog, 'add_watchdog', lambda **args: watches.update({args['id']: args}))
    changed = Mock()
    monkeypatch.setattr(plugins, 'after_plugin_change', changed)
    plugins.register_watchdogs()
    on_change = watches['plugins_roots']['handler']
    on_change([['/a0/usr/plugins/_sandboxing/runtime/instances/service/rootfs/opt/runtime/lib/markdown/extensions/foo.py', 'create'],
               ['/a0/usr/plugins/_sandboxing/runtime/instances/service/rootfs/opt/runtime/lib/pkg/hooks.py', 'create']])
    changed.assert_not_called()
    on_change([['/a0/plugins/_desktop/extensions/python/startup_migration/routes.py', 'modify']])
    changed.assert_called_once_with(['_desktop'], python_change=True, frontend_reload=True)
