"""
WhatsApp bridge subprocess manager.

No agent/tool dependencies.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import shutil
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any, Sequence

from helpers.print_style import PrintStyle


_bridge_lock: asyncio.Lock | None = None
_bridge_lock_loop: asyncio.AbstractEventLoop | None = None
_bridge_config: dict = {}  # config the running bridge was started with

MAX_STARTUP_LOG_LINES = 80
STARTUP_WAIT_ATTEMPTS = 20
STARTUP_WAIT_SECONDS = 0.5
DEPENDENCY_FAILURE_MARKERS = (
    "ERR_MODULE_NOT_FOUND",
    "MODULE_NOT_FOUND",
    "Cannot find module",
    "Cannot find package",
)


# ------------------------------------------------------------------
# Process wrapper with destructor
# ------------------------------------------------------------------

class _BridgeProcess:
    """Thin wrapper around Popen — kills the process on garbage collection."""

    def __init__(self, process: subprocess.Popen, port: int):
        self._process = process
        self._port = port
        self._recent_output: deque[str] = deque(maxlen=MAX_STARTUP_LOG_LINES)

    def poll(self) -> int | None:
        return self._process.poll()

    def terminate(self) -> None:
        self._process.terminate()

    def wait(self, timeout: float | None = None) -> int:
        return self._process.wait(timeout=timeout)

    def kill(self) -> None:
        self._process.kill()

    def remember_output(self, text: str) -> None:
        self._recent_output.append(text)

    def recent_output(self) -> str:
        return "\n".join(self._recent_output)

    @property
    def stdout(self):
        return self._process.stdout

    def __del__(self) -> None:
        try:
            if self._process.poll() is None:
                PrintStyle.error("WhatsApp: bridge still running on GC, killing")
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                _kill_port_process(self._port)
        except Exception as e:
            PrintStyle.error(f"WhatsApp: bridge destructor error: {e}")


_bridge_process: _BridgeProcess | None = None

REPO_ROOT = Path(__file__).resolve().parents[3]
BRIDGE_DIR = str(Path(__file__).parent.parent / "whatsapp-bridge")
BRIDGE_SCRIPT = os.path.join(BRIDGE_DIR, "bridge.js")
BRIDGE_PACKAGE_JSON = os.path.join(BRIDGE_DIR, "package.json")
BRIDGE_PACKAGE_LOCK = os.path.join(BRIDGE_DIR, "package-lock.json")
BRIDGE_RUNTIME_DIR = os.path.join(REPO_ROOT, "usr", "whatsapp", "bridge-runtime")
BRIDGE_INSTALL_STATE = os.path.join(BRIDGE_RUNTIME_DIR, "deps-state.json")
BRIDGE_NPM_CACHE = os.path.join(BRIDGE_RUNTIME_DIR, "npm-cache")
NODE_MODULES_DIR = os.path.join(BRIDGE_DIR, "node_modules")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

async def start_bridge(
    port: int,
    session_dir: str,
    cache_dir: str,
    mode: str = "self-chat",
) -> bool:
    async with _get_bridge_lock():
        return await _ensure_bridge_started(
            port=port,
            session_dir=session_dir,
            cache_dir=cache_dir,
            mode=mode,
            require_connection=True,
            start_label="WhatsApp: starting bridge",
        )


async def stop_bridge() -> None:
    async with _get_bridge_lock():
        _stop_bridge_process()


async def is_bridge_running(port: int) -> bool:
    if not _bridge_process or _bridge_process.poll() is not None:
        return False
    return await _check_health(port)


def get_bridge_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


async def ensure_bridge_http_up(
    port: int,
    session_dir: str,
    cache_dir: str,
    mode: str = "self-chat",
) -> bool:
    """Start bridge if needed and wait for HTTP server only (not WA connection)."""
    async with _get_bridge_lock():
        return await _ensure_bridge_started(
            port=port,
            session_dir=session_dir,
            cache_dir=cache_dir,
            mode=mode,
            require_connection=False,
            start_label="WhatsApp: starting bridge for pairing",
        )


def is_process_alive() -> bool:
    return _bridge_process is not None and _bridge_process.poll() is None


def get_running_config() -> dict:
    return dict(_bridge_config)


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _get_bridge_lock() -> asyncio.Lock:
    global _bridge_lock, _bridge_lock_loop
    loop = asyncio.get_running_loop()
    if _bridge_lock is None or _bridge_lock_loop is not loop:
        _bridge_lock = asyncio.Lock()
        _bridge_lock_loop = loop
    return _bridge_lock


async def _ensure_bridge_started(
    *,
    port: int,
    session_dir: str,
    cache_dir: str,
    mode: str,
    require_connection: bool,
    start_label: str,
) -> bool:
    global _bridge_process

    if _bridge_process and _bridge_process.poll() is None:
        if require_connection:
            return True
        if await _check_http_up(port):
            return True

        PrintStyle.warning("WhatsApp: bridge is running but HTTP is not responding, restarting")
        _stop_bridge_process()

    await _ensure_bridge_dependencies()

    attempt = 0
    while attempt < 2:
        attempt += 1
        success, output = await _start_bridge_once(
            port=port,
            session_dir=session_dir,
            cache_dir=cache_dir,
            mode=mode,
            require_connection=require_connection,
            start_label=start_label,
        )
        if success:
            return True

        if attempt == 1 and _looks_like_dependency_failure(output):
            PrintStyle.warning(
                "WhatsApp: bridge startup looks like a dependency issue, "
                "reinstalling dependencies and retrying"
            )
            await _ensure_bridge_dependencies(force_reinstall=True)
            continue

        return False

    return False


async def _start_bridge_once(
    *,
    port: int,
    session_dir: str,
    cache_dir: str,
    mode: str,
    require_connection: bool,
    start_label: str,
) -> tuple[bool, str]:
    global _bridge_process

    cmd = [
        "node", BRIDGE_SCRIPT,
        "--port", str(port),
        "--session", session_dir,
        "--cache-dir", cache_dir,
        "--mode", mode,
    ]

    _kill_port_process(port)
    PrintStyle.info(start_label)
    _bridge_process = _BridgeProcess(subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=BRIDGE_DIR,
    ), port)
    _start_log_reader(_bridge_process)
    _bridge_config.clear()
    _bridge_config.update({"port": port, "mode": mode})

    healthy, output = await _wait_for_bridge_startup(
        port=port,
        require_connection=require_connection,
    )
    if healthy:
        return True, output

    if output:
        PrintStyle.error(f"WhatsApp: bridge startup failed\n{output}")
    return False, output


async def _wait_for_bridge_startup(*, port: int, require_connection: bool) -> tuple[bool, str]:
    for _ in range(STARTUP_WAIT_ATTEMPTS):
        await asyncio.sleep(STARTUP_WAIT_SECONDS)

        process = _bridge_process
        if process is None:
            return False, ""

        if process.poll() is not None:
            output = _summarize_output(process.recent_output())
            PrintStyle.error("WhatsApp: bridge process exited unexpectedly")
            _clear_bridge_process()
            return False, output

        if require_connection:
            if await _check_health(port):
                return True, process.recent_output()
        else:
            if await _check_http_up(port):
                return True, process.recent_output()

    if require_connection:
        PrintStyle.warning("WhatsApp: bridge started but not yet connected")
        process = _bridge_process
        return True, process.recent_output() if process else ""

    process = _bridge_process
    return False, _summarize_output(process.recent_output()) if process else ""


def _looks_like_dependency_failure(output: str) -> bool:
    return any(marker in output for marker in DEPENDENCY_FAILURE_MARKERS)


async def _check_health(port: int) -> bool:
    try:
        from plugins._whatsapp_integration.helpers.wa_client import get_health
        health = await get_health(get_bridge_url(port))
        return health.get("status") == "connected"
    except Exception:
        return False


async def _check_http_up(port: int) -> bool:
    try:
        from plugins._whatsapp_integration.helpers.wa_client import get_health
        await get_health(get_bridge_url(port))
        return True
    except Exception:
        return False


async def _ensure_bridge_dependencies(force_reinstall: bool = False) -> None:
    expected_state = await _build_dependency_state()

    if not force_reinstall:
        install_state = _load_dependency_state()
        if os.path.isdir(NODE_MODULES_DIR) and await _validate_bridge_dependencies():
            if install_state is None:
                _write_dependency_state(expected_state)
                return
            if install_state == expected_state:
                return

    await _reinstall_bridge_dependencies()

    if not await _validate_bridge_dependencies():
        raise RuntimeError("WhatsApp: bridge dependencies failed validation after reinstall")

    _write_dependency_state(await _build_dependency_state())


async def _build_dependency_state() -> dict[str, Any]:
    return {
        "package_json_hash": _sha256_file(BRIDGE_PACKAGE_JSON),
        "package_lock_hash": _sha256_file(BRIDGE_PACKAGE_LOCK) if os.path.isfile(BRIDGE_PACKAGE_LOCK) else "",
        "platform": platform.system(),
        "arch": platform.machine(),
        "node_version": (await _run_subprocess(["node", "--version"], cwd=BRIDGE_DIR)).strip(),
        "npm_version": (await _run_subprocess(["npm", "--version"], cwd=BRIDGE_DIR)).strip(),
    }


async def _validate_bridge_dependencies() -> bool:
    dependency_names = _bridge_dependency_names()
    if not dependency_names or not os.path.isdir(NODE_MODULES_DIR):
        return False

    imports = ", ".join(json.dumps(name) for name in dependency_names)
    script = (
        f"for (const name of [{imports}]) {{ await import(name); }}\n"
        "process.stdout.write('ok');\n"
    )

    try:
        output = await _run_subprocess(
            ["node", "--input-type=module", "--eval", script],
            cwd=BRIDGE_DIR,
        )
    except RuntimeError as e:
        PrintStyle.warning(f"WhatsApp: dependency validation failed: {e}")
        return False
    return output.strip() == "ok"


async def _reinstall_bridge_dependencies() -> None:
    _ensure_runtime_dir()

    if os.path.isdir(NODE_MODULES_DIR):
        PrintStyle.warning("WhatsApp: bridge dependencies missing, outdated, or corrupt; reinstalling")
        shutil.rmtree(NODE_MODULES_DIR, ignore_errors=True)
    else:
        PrintStyle.info("WhatsApp: installing bridge dependencies")

    if os.path.isfile(BRIDGE_INSTALL_STATE):
        try:
            os.remove(BRIDGE_INSTALL_STATE)
        except OSError:
            pass

    commands: list[list[str]] = []
    if os.path.isfile(BRIDGE_PACKAGE_LOCK):
        commands.append(["npm", "ci", "--omit=dev", "--no-audit", "--no-fund"])
    commands.append(["npm", "install", "--omit=dev", "--no-audit", "--no-fund"])
    env = {"npm_config_cache": BRIDGE_NPM_CACHE}

    last_error: RuntimeError | None = None
    for command in commands:
        try:
            await _run_subprocess(command, cwd=BRIDGE_DIR, env=env)
            return
        except RuntimeError as e:
            last_error = e
            PrintStyle.warning(f"WhatsApp: {' '.join(command)} failed: {e}")

    raise RuntimeError(str(last_error) if last_error else "npm install failed")


def _bridge_dependency_names() -> list[str]:
    with open(BRIDGE_PACKAGE_JSON, "r", encoding="utf-8") as f:
        package_json = json.load(f)
    dependencies = package_json.get("dependencies") or {}
    return sorted(dependencies.keys())


def _load_dependency_state() -> dict[str, Any] | None:
    if not os.path.isfile(BRIDGE_INSTALL_STATE):
        return None
    try:
        with open(BRIDGE_INSTALL_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_dependency_state(state: dict[str, Any]) -> None:
    _ensure_runtime_dir()
    with open(BRIDGE_INSTALL_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_runtime_dir() -> None:
    os.makedirs(BRIDGE_RUNTIME_DIR, exist_ok=True)


async def _run_subprocess(
    command: Sequence[str],
    *,
    cwd: str,
    env: dict[str, str] | None = None,
) -> str:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    proc = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        env=process_env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        raise RuntimeError(output or f"{' '.join(command)} exited with code {proc.returncode}")
    return output


def _stop_bridge_process() -> None:
    global _bridge_process
    if not _bridge_process:
        return
    try:
        _bridge_process.terminate()
        try:
            _bridge_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _bridge_process.kill()
    except Exception:
        pass
    _clear_bridge_process()
    PrintStyle.info("WhatsApp: bridge stopped")


def _clear_bridge_process() -> None:
    global _bridge_process
    _bridge_process = None
    _bridge_config.clear()


def _kill_port_process(port: int) -> None:
    """Kill any orphaned process listening on the given TCP port."""
    try:
        system = platform.system()
        if system == "Windows":
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[3] == "LISTENING":
                    if parts[1].endswith(f":{port}"):
                        try:
                            subprocess.run(
                                ["taskkill", "/PID", parts[4], "/F"],
                                capture_output=True, timeout=5,
                            )
                        except subprocess.SubprocessError:
                            pass
        elif system == "Darwin":
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True, text=True, timeout=5,
            )
            for pid_str in result.stdout.strip().splitlines():
                try:
                    os.kill(int(pid_str.strip()), 9)
                except (ValueError, OSError):
                    pass
        else:
            result = subprocess.run(
                ["fuser", f"{port}/tcp"],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                subprocess.run(
                    ["fuser", "-k", f"{port}/tcp"],
                    capture_output=True, timeout=5,
                )
    except Exception:
        pass


def _start_log_reader(process: _BridgeProcess) -> None:
    def _reader() -> None:
        assert process.stdout
        for line in iter(process.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                process.remember_output(text)
                PrintStyle.standard(f"WhatsApp bridge: {text}")
        process.stdout.close()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()


def _summarize_output(output: str, max_lines: int = 12) -> str:
    if not output:
        return ""
    lines = [line for line in output.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:])
