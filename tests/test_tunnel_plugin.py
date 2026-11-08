from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from plugins._tunnel.helpers import runtime
from plugins._tunnel.api.tunnel import Tunnel


def test_plugin_api_retains_auth_and_csrf():
    assert Tunnel.requires_auth()
    assert Tunnel.requires_csrf()


def test_unused_tunnel_does_not_create_a_sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime, 'enabled', lambda: True)
    monkeypatch.setattr(runtime, 'config', lambda: {})
    manager = SimpleNamespace(config=SimpleNamespace(instances_dir=tmp_path))
    monkeypatch.setattr(runtime, 'get_manager', lambda: manager)
    assert runtime.status(fresh=True)['is_running'] is False
    assert list(tmp_path.iterdir()) == []


def test_first_start_uses_runtime_port_default_image_and_native_service(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime, 'enabled', lambda: True)
    monkeypatch.setattr(runtime, 'config', lambda: {})
    monkeypatch.setattr(runtime.runtime, 'get_web_ui_port', lambda: 8765)
    calls = []
    states = iter([{'is_running': False}, {'is_running': True, 'provider': 'cloudflared', 'tunnel_url': 'https://example.test'}])
    monkeypatch.setattr(runtime, 'status', lambda **kwargs: next(states))
    manager = SimpleNamespace(config=SimpleNamespace(instances_dir=tmp_path), create=lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(runtime, 'get_manager', lambda: manager)
    assert runtime.start()['is_running']
    args, options = calls[0]
    assert args == ('service-tunnel',)
    assert options['image'] == ''
    assert options['network'] == 'host'
    assert options['standalone'] and options['service']
    assert options['share_usr'] is False
    assert options['command'] == ['/bin/sh', '/plugin/sandbox/boot.sh', 'cloudflared', '8765']
    assert options['mounts'][0].read_only


def test_disabled_plugin_never_starts_or_reports_old_url(monkeypatch):
    monkeypatch.setattr(runtime, 'enabled', lambda: False)
    assert runtime.status(fresh=True)['tunnel_url'] is None
    with pytest.raises(runtime.SandboxError, match='Enable'):
        runtime.start()


def test_supervisor_migration_is_scoped_and_idempotent(monkeypatch, tmp_path):
    migration = importlib.import_module('extensions.python.startup_migration._25_retire_tunnel_service')
    config = tmp_path / 'supervisord.conf'
    config.write_text('[program:run_ui]\ncommand=keep\n\n[program:run_tunnel_api]\ncommand=/exe/run_tunnel_api.sh\nautorestart=true\n\n[eventlistener:keep]\ncommand=keep\n')
    calls = []
    monkeypatch.setattr(migration.shutil, 'which', lambda _: '/usr/bin/supervisorctl')
    monkeypatch.setattr(migration.subprocess, 'run', lambda argv, **kwargs: calls.append(argv))
    assert migration.retire(config)
    assert 'program:run_tunnel_api' not in config.read_text()
    assert '[program:run_ui]\ncommand=keep' in config.read_text()
    assert '[eventlistener:keep]\ncommand=keep' in config.read_text()
    assert not migration.retire(config)
    assert calls == [['/usr/bin/supervisorctl','reread'], ['/usr/bin/supervisorctl','update']]


def test_native_startup_does_not_touch_system_supervisor(monkeypatch):
    migration = importlib.import_module('extensions.python.startup_migration._25_retire_tunnel_service')
    monkeypatch.setattr(migration.runtime, 'is_dockerized', lambda: False)
    monkeypatch.setattr(migration, 'retire', lambda: pytest.fail('must not modify native host Supervisor'))
    migration.RetireTunnelController(None).execute()
