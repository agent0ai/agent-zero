"""Thin host adapter; provider dependencies and processes live in the sandbox."""
from __future__ import annotations

import json
from pathlib import Path
import re
import threading
import time

from helpers import plugins, runtime
from helpers.sandbox import get_manager, SandboxMount, SandboxError

PLUGIN = '_tunnel'
SANDBOX = 'service-tunnel'
PROVIDERS = {'cloudflared', 'microsoft', 'serveo', 'tailscale'}
_lock = threading.Lock()
_cached_status: tuple[float, dict] = (0, {})


def enabled() -> bool:
    return plugins.get_toggle_state(PLUGIN) == 'enabled'


def config() -> dict:
    return plugins.get_plugin_config(PLUGIN) or {}


def invalidate() -> None:
    global _cached_status
    _cached_status = (0, {})


def status(*, fresh: bool = False) -> dict:
    global _cached_status
    if not fresh and time.monotonic() - _cached_status[0] < 1:
        return dict(_cached_status[1])
    result = {'success': False, 'is_running': False, 'tunnel_url': None, 'notifications': []}
    if not enabled():
        return result
    result['provider'] = str(config().get('provider') or 'cloudflared')
    manager = get_manager()
    if not (manager.config.instances_dir / SANDBOX / 'metadata.json').is_file():
        return result
    info = manager.inspect(SANDBOX)
    result['sandbox_status'] = info.status
    if info.status == 'running':
        try:
            provider = manager.read_file(SANDBOX, 'var/lib/a0-tunnel/provider', limit=32).strip()
            result['provider'] = provider
            if provider == 'cloudflared':
                log = manager.read_file(SANDBOX, 'var/lib/a0-tunnel/tunnel.log')
                urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com\b', log)
                if urls and 'Registered tunnel connection' in log:
                    result.update(success=True, is_running=True, tunnel_url=urls[-1])
            else:
                payload = json.loads(manager.read_file(SANDBOX, 'var/lib/a0-tunnel/status.json'))
                if isinstance(payload, dict):
                    for key in ('is_running', 'tunnel_url', 'notifications', 'message'):
                        if key in payload:
                            result[key] = payload[key]
                    result['success'] = bool(result['is_running'] and result['tunnel_url'])
        except (OSError, ValueError):
            pass  # Installer/provider has not produced status yet.
    _cached_status = (time.monotonic(), result)
    return dict(result)


def start(provider: str = '') -> dict:
    if not enabled():
        raise SandboxError('Enable the Remote Control plugin first')
    settings = config()
    provider = provider or str(settings.get('provider') or 'cloudflared')
    if provider not in PROVIDERS:
        raise SandboxError('Unsupported tunnel provider')
    port = int(settings.get('port') or runtime.get_web_ui_port())
    if not 1 <= port <= 65535:
        raise SandboxError('Tunnel target port must be between 1 and 65535')
    with _lock:
        manager = get_manager()
        existing = status(fresh=True)
        if existing['is_running'] and existing.get('provider') == provider:
            return existing
        command = ['/bin/sh', '/plugin/sandbox/boot.sh', provider, str(port)]
        if (manager.config.instances_dir / SANDBOX / 'metadata.json').exists():
            manager.stop(SANDBOX)
            manager.set_command(SANDBOX, command)
            manager.start(SANDBOX)
        else:
            manager.create(
                SANDBOX, sandbox_type='permanent', standalone=True, service=True,
                network='host', share_usr=False, ownership={'plugin_id': PLUGIN}, image=str(settings.get('image') or ''),
                mounts=[SandboxMount(Path(__file__).resolve().parents[1], '/plugin', True)],
                command=command,
            )
        invalidate()
        try:
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                result = status(fresh=True)
                if result['is_running']:
                    return result
                if result.get('sandbox_status') != 'running':
                    raise SandboxError('Tunnel setup exited. Check the plugin sandbox install.log and tunnel.log.')
                if result.get('message'):
                    raise SandboxError(str(result['message']))
                time.sleep(0.5)
            raise SandboxError('Timed out waiting for the tunnel provider')
        except BaseException:
            manager.stop(SANDBOX)
            invalidate()
            raise


def stop() -> dict:
    with _lock:
        manager = get_manager()
        if (manager.config.instances_dir / SANDBOX / 'metadata.json').exists():
            manager.stop(SANDBOX)
        invalidate()
    return {'success': True, 'is_running': False, 'tunnel_url': None}


def request(data: dict) -> dict:
    action = data.get('action', 'get')
    if action == 'create':
        return start(str(data.get('provider') or ''))
    if action == 'stop':
        return stop()
    if action == 'health':
        return {'success': True}
    if action in {'get', 'notifications'}:
        return status()
    if action == 'verify':
        current = status()
        return {'success': True, 'is_valid': bool(current['is_running'] and data.get('url') == current['tunnel_url'])}
    raise ValueError('Unknown tunnel action')
