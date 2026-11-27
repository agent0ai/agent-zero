from pathlib import Path
from types import SimpleNamespace
import json
import multiprocessing

import pytest

from plugins._searxng import search as cli


class Manager:
    def __init__(self, root):
        self.config = SimpleNamespace(instances_dir=root)
        self.events = []
        self.installed = ''
        self.fail_install = False

    def create(self, name, **kwargs):
        assert kwargs['service'] is True and kwargs['share_usr'] is False
        assert kwargs['sandbox_type'] == 'permanent'
        assert [mount.destination for mount in kwargs['mounts']] == ['/plugin', '/worker']
        self.events.append('create')
        path = self.config.instances_dir / name
        path.mkdir()
        (path / 'metadata.json').write_text('{}')

    def stop(self, name):
        self.events.append('stop')

    def start(self, name):
        self.events.append('start')

    def set_command(self, name, command):
        assert command == []

    def set_mounts(self, name, mounts):
        pass

    def read_file(self, name, path):
        return self.installed

    def exec(self, name, argv, timeout):
        if argv[0] == 'sh':
            assert timeout == 1800
            assert cli.status(self)['state'] == 'installing'
            assert cli.status(self)['busy'] is True
            self.events.append('install')
            if self.fail_install:
                return SimpleNamespace(exit_code=1, stdout='', stderr='install failed')
            self.installed = argv[-1]
            return SimpleNamespace(exit_code=0, stdout='', stderr='')
        assert timeout == 60
        assert cli.status(self)['state'] == 'searching'
        self.events.append('search')
        return SimpleNamespace(exit_code=0, stdout=json.dumps({'query': argv[-1], 'results': []}), stderr='')


def test_cold_install_and_warm_reuse(tmp_path, capsys):
    manager = Manager(tmp_path)
    assert cli.search('test', manager) == {'query': 'test', 'results': []}
    assert manager.events == ['create', 'install', 'search', 'stop']
    assert cli.status(manager)['state'] == 'idle'
    assert cli.status(manager)['busy'] is False
    manager.events.clear()
    cli.search('another query', manager)
    assert manager.events == ['stop', 'start', 'search', 'stop']
    assert 'First use may take' in capsys.readouterr().err


def test_failed_install_stops_and_retries(tmp_path):
    manager = Manager(tmp_path)
    manager.fail_install = True
    with pytest.raises(cli.SandboxError, match='install failed'):
        cli.search('test', manager)
    assert manager.events[-1] == 'stop'
    assert not manager.installed
    assert cli.status(manager)['state'] == 'error'
    manager.fail_install = False
    cli.search('retry', manager)
    assert manager.events.count('install') == 2
    assert cli.status(manager)['state'] == 'idle'


@pytest.mark.parametrize('query', ['', ' ', None, 42, 'x' * 8193])
def test_invalid_query_never_touches_sandbox(query):
    with pytest.raises(ValueError, match='Search query'):
        cli.search(query, None)


def _hold_setup(root, ready, release):
    manager = SimpleNamespace(config=SimpleNamespace(instances_dir=Path(root)))
    with cli.locked(manager) as path:
        cli._write_status(path, 'installing', 'Installing test dependencies')
        ready.set()
        release.wait(20)


def _wait_for_setup(root, waiting, entered):
    manager = SimpleNamespace(config=SimpleNamespace(instances_dir=Path(root)))
    waiting.set()
    with cli.locked(manager):
        entered.set()


def test_process_lock_reports_installing_and_serializes_callers(tmp_path):
    context = multiprocessing.get_context('spawn')
    ready, release, waiting, entered = (context.Event() for _ in range(4))
    owner = context.Process(target=_hold_setup, args=(str(tmp_path), ready, release))
    waiter = context.Process(target=_wait_for_setup, args=(str(tmp_path), waiting, entered))
    manager = Manager(tmp_path)
    owner.start()
    try:
        assert ready.wait(20)
        assert cli.status(manager)['state'] == 'installing'
        assert cli.status(manager)['busy'] is True
        waiter.start()
        assert waiting.wait(20)
        assert not entered.wait(.3)
        release.set()
        assert entered.wait(20)
    finally:
        release.set()
        owner.join(20)
        if owner.is_alive():
            owner.kill()
            owner.join()
        if waiter.pid:
            waiter.join(20)
            if waiter.is_alive():
                waiter.kill()
                waiter.join()
    assert owner.exitcode == waiter.exitcode == 0
    assert cli.status(manager)['state'] == 'interrupted'
    assert cli.status(manager)['busy'] is False


def test_killed_installer_releases_lock_and_reports_interrupted(tmp_path):
    context = multiprocessing.get_context('spawn')
    ready, release = context.Event(), context.Event()
    owner = context.Process(target=_hold_setup, args=(str(tmp_path), ready, release))
    owner.start()
    try:
        assert ready.wait(20)
        owner.kill()
        owner.join(20)
        manager = Manager(tmp_path)
        assert cli.status(manager)['state'] == 'interrupted'
        cli.search('retry after kill', manager)
        assert manager.events.count('install') == 1
    finally:
        if owner.is_alive():
            owner.kill()
        owner.join()


def test_cli_status_never_starts_a_sandbox(monkeypatch, tmp_path, capsys):
    manager = Manager(tmp_path)
    monkeypatch.setattr(cli, 'get_manager', lambda: manager)
    assert cli.main(['--status']) == 0
    assert json.loads(capsys.readouterr().out) == {'state': 'idle', 'busy': False}
    assert manager.events == []


def test_hooks_are_lazy_and_share_the_cli_lock(monkeypatch, tmp_path):
    from plugins._searxng import hooks
    manager = Manager(tmp_path)
    monkeypatch.setattr(cli, 'get_manager', lambda: manager)
    assert hooks.install()['installed_on_demand'] is True
    assert manager.events == []
    cli.search('test', manager)
    hooks.disable()
    assert manager.events[-1] == 'stop'
    manager.delete = lambda name, **kwargs: manager.events.append(('delete', name, kwargs))
    hooks.uninstall()
    assert manager.events[-1] == ('delete', cli.NAME, {'missing_ok': True})
