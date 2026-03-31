import asyncio
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._whatsapp_integration.helpers import bridge_manager


@pytest.fixture(autouse=True)
def reset_bridge_manager_state():
    bridge_manager._bridge_lock = None
    bridge_manager._bridge_lock_loop = None
    bridge_manager._bridge_process = None
    bridge_manager._bridge_config.clear()
    yield
    bridge_manager._bridge_lock = None
    bridge_manager._bridge_lock_loop = None
    bridge_manager._bridge_process = None
    bridge_manager._bridge_config.clear()


def test_get_bridge_lock_recreates_lock_when_loop_marker_changes():
    async def _run():
        original_lock = asyncio.Lock()
        bridge_manager._bridge_lock = original_lock
        bridge_manager._bridge_lock_loop = object()

        refreshed_lock = bridge_manager._get_bridge_lock()

        assert refreshed_lock is bridge_manager._bridge_lock
        assert refreshed_lock is not original_lock

    asyncio.run(_run())


def test_ensure_bridge_dependencies_reinstalls_invalid_dependency_tree(monkeypatch):
    state_writes: list[dict] = []
    validate_results = [False, True]
    reinstall_calls: list[bool] = []

    monkeypatch.setattr(bridge_manager, "NODE_MODULES_DIR", "/tmp/whatsapp-node-modules")
    monkeypatch.setattr(bridge_manager.os.path, "isdir", lambda path: path == "/tmp/whatsapp-node-modules")

    async def fake_build_dependency_state():
        return {"package_json_hash": "a", "package_lock_hash": "b"}

    async def fake_validate_bridge_dependencies():
        return validate_results.pop(0)

    async def fake_reinstall_bridge_dependencies():
        reinstall_calls.append(True)

    monkeypatch.setattr(bridge_manager, "_build_dependency_state", fake_build_dependency_state)
    monkeypatch.setattr(bridge_manager, "_load_dependency_state", lambda: {"package_json_hash": "a", "package_lock_hash": "b"})
    monkeypatch.setattr(bridge_manager, "_validate_bridge_dependencies", fake_validate_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_reinstall_bridge_dependencies", fake_reinstall_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_write_dependency_state", lambda state: state_writes.append(state))

    asyncio.run(bridge_manager._ensure_bridge_dependencies())

    assert reinstall_calls == [True]
    assert state_writes == [{"package_json_hash": "a", "package_lock_hash": "b"}]


def test_ensure_bridge_dependencies_bootstraps_missing_state_without_reinstall(monkeypatch):
    state_writes: list[dict] = []
    reinstall_calls: list[bool] = []

    monkeypatch.setattr(bridge_manager, "NODE_MODULES_DIR", "/tmp/whatsapp-node-modules")
    monkeypatch.setattr(bridge_manager.os.path, "isdir", lambda path: path == "/tmp/whatsapp-node-modules")

    async def fake_build_dependency_state():
        return {"package_json_hash": "a", "package_lock_hash": "b"}

    async def fake_validate_bridge_dependencies():
        return True

    async def fake_reinstall_bridge_dependencies():
        reinstall_calls.append(True)

    monkeypatch.setattr(bridge_manager, "_build_dependency_state", fake_build_dependency_state)
    monkeypatch.setattr(bridge_manager, "_load_dependency_state", lambda: None)
    monkeypatch.setattr(bridge_manager, "_validate_bridge_dependencies", fake_validate_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_reinstall_bridge_dependencies", fake_reinstall_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_write_dependency_state", lambda state: state_writes.append(state))

    asyncio.run(bridge_manager._ensure_bridge_dependencies())

    assert reinstall_calls == []
    assert state_writes == [{"package_json_hash": "a", "package_lock_hash": "b"}]


def test_reinstall_bridge_dependencies_uses_local_npm_cache(monkeypatch):
    run_calls: list[tuple[list[str], dict[str, str] | None]] = []
    real_isdir = bridge_manager.os.path.isdir

    monkeypatch.setattr(bridge_manager.PrintStyle, "warning", staticmethod(lambda message: None))
    monkeypatch.setattr(bridge_manager.PrintStyle, "info", staticmethod(lambda message: None))
    monkeypatch.setattr(bridge_manager, "NODE_MODULES_DIR", "/tmp/whatsapp-node-modules")
    monkeypatch.setattr(bridge_manager, "BRIDGE_PACKAGE_LOCK", "/tmp/package-lock.json")
    monkeypatch.setattr(bridge_manager, "BRIDGE_INSTALL_STATE", "/tmp/deps-state.json")
    monkeypatch.setattr(bridge_manager, "BRIDGE_NPM_CACHE", "/tmp/npm-cache")
    monkeypatch.setattr(
        bridge_manager.os.path,
        "isdir",
        lambda path: path == "/tmp/whatsapp-node-modules" or real_isdir(path),
    )
    monkeypatch.setattr(
        bridge_manager.os.path,
        "isfile",
        lambda path: path == "/tmp/package-lock.json",
    )
    monkeypatch.setattr(bridge_manager.shutil, "rmtree", lambda path, ignore_errors=True: None)

    async def fake_run_subprocess(command, *, cwd, env=None):
        run_calls.append((list(command), env))
        return ""

    monkeypatch.setattr(bridge_manager, "_run_subprocess", fake_run_subprocess)

    asyncio.run(bridge_manager._reinstall_bridge_dependencies())

    assert run_calls == [
        (
            ["npm", "ci", "--omit=dev", "--no-audit", "--no-fund"],
            {"npm_config_cache": "/tmp/npm-cache"},
        ),
    ]


def test_start_bridge_reinstalls_and_retries_after_dependency_failure(monkeypatch):
    ensure_calls: list[bool] = []
    start_attempts = [
        (False, "Error: Cannot find package '@whiskeysockets/baileys'"),
        (True, ""),
    ]

    async def fake_ensure_bridge_dependencies(force_reinstall: bool = False):
        ensure_calls.append(force_reinstall)

    async def fake_start_bridge_once(**kwargs):
        return start_attempts.pop(0)

    monkeypatch.setattr(bridge_manager, "_ensure_bridge_dependencies", fake_ensure_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_start_bridge_once", fake_start_bridge_once)

    started = asyncio.run(bridge_manager.start_bridge(
        port=3100,
        session_dir="/tmp/wa-session",
        cache_dir="/tmp/wa-cache",
    ))

    assert started is True
    assert ensure_calls == [False, True]


def test_start_bridge_does_not_reinstall_on_non_dependency_failure(monkeypatch):
    ensure_calls: list[bool] = []

    async def fake_ensure_bridge_dependencies(force_reinstall: bool = False):
        ensure_calls.append(force_reinstall)

    async def fake_start_bridge_once(**kwargs):
        return False, "Bridge closed unexpectedly without module resolution errors"

    monkeypatch.setattr(bridge_manager, "_ensure_bridge_dependencies", fake_ensure_bridge_dependencies)
    monkeypatch.setattr(bridge_manager, "_start_bridge_once", fake_start_bridge_once)

    started = asyncio.run(bridge_manager.start_bridge(
        port=3100,
        session_dir="/tmp/wa-session",
        cache_dir="/tmp/wa-cache",
    ))

    assert started is False
    assert ensure_calls == [False]
