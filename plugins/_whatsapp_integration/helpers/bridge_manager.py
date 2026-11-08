"""Thin lifecycle client; Baileys and npm installs belong to the guest."""
from __future__ import annotations

import asyncio
from pathlib import Path
import secrets

from helpers.sandbox import SandboxMount
from helpers.sandbox_worker import SandboxWorker
from plugins._whatsapp_integration.helpers.number_utils import normalize_allowed_numbers

worker = SandboxWorker('_whatsapp_integration', idle_seconds=None)
_bridge_config: dict = {}
_bridge_token = secrets.token_urlsafe(32)
_bridge_lock = None
_bridge_lock_loop = None


def _get_bridge_lock():
    global _bridge_lock, _bridge_lock_loop
    loop = asyncio.get_running_loop()
    if _bridge_lock is None or _bridge_lock_loop is not loop:
        _bridge_lock, _bridge_lock_loop = asyncio.Lock(), loop
    return _bridge_lock


def auth_headers():
    return {'Authorization': 'Bearer ' + _bridge_token}


def get_bridge_url(port: int) -> str:
    return f'http://127.0.0.1:{int(port)}'


def get_running_config() -> dict:
    return dict(_bridge_config)


def is_process_alive() -> bool:
    if not worker.ready:
        return False
    try:
        return bool(worker.call({'action': 'status'}, timeout=5))
    except Exception:
        return False


async def is_bridge_running(port: int) -> bool:
    if not await asyncio.to_thread(is_process_alive):
        return False
    from plugins._whatsapp_integration.helpers.wa_client import get_health
    try:
        return (await get_health(get_bridge_url(port))).get('status') == 'connected'
    except Exception:
        return False


async def start_bridge(port: int, session_dir: str, cache_dir: str, mode: str = 'self-chat',
                       allowed_numbers: object = None, allow_group: bool = False) -> bool:
    if not 1 <= int(port) <= 65535:
        raise ValueError('Invalid bridge port')
    config = {'port': int(port), 'mode': mode,
              'allowed_numbers': sorted(normalize_allowed_numbers(allowed_numbers)),
              'allow_group': bool(allow_group)}
    mounts = []
    for directory in (session_dir, cache_dir):
        path = Path(directory).resolve()
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        mounts.append(SandboxMount(path, str(path), False))
    async with _get_bridge_lock():
        if _bridge_config == config and worker.mounts == mounts and await asyncio.to_thread(is_process_alive):
            return True
        guest_config = {'port': config['port'], 'mode': mode, 'session': str(mounts[0].source),
                        'cache-dir': str(mounts[1].source),
                        'allowed-numbers': ','.join(config['allowed_numbers']),
                        'allow-group': str(bool(allow_group)).lower()}
        _bridge_config.clear()
        started = await worker.acall({'action': 'start', 'config': guest_config, 'token': _bridge_token},
                                     mounts=mounts, timeout=960)
        if started:
            _bridge_config.update(config)
        return bool(started)


async def ensure_bridge_http_up(port: int, session_dir: str, cache_dir: str,
                                mode: str = 'self-chat', allowed_numbers: object = None,
                                allow_group: bool = False) -> bool:
    return await start_bridge(port, session_dir, cache_dir, mode, allowed_numbers, allow_group)


async def stop_bridge() -> None:
    async with _get_bridge_lock():
        await asyncio.to_thread(worker.stop)
        _bridge_config.clear()
