"""
WhatsApp bridge subprocess manager.

No agent/tool dependencies.
"""

import asyncio
import os
import platform
import subprocess
import threading
from pathlib import Path

from helpers.print_style import PrintStyle


_bridge_lock = asyncio.Lock()
_bridge_config: dict = {}  # config the running bridge was started with


# ------------------------------------------------------------------
# Process wrapper with destructor
# ------------------------------------------------------------------

class _BridgeProcess:
    """Thin wrapper around Popen — kills the process on garbage collection."""

    def __init__(self, process: subprocess.Popen, port: int):
        self._process = process
        self._port = port

    def poll(self) -> int | None:
        return self._process.poll()

    def terminate(self) -> None:
        self._process.terminate()

    def wait(self, timeout: float | None = None) -> int:
        return self._process.wait(timeout=timeout)

    def kill(self) -> None:
        self._process.kill()

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

BRIDGE_DIR = str(Path(__file__).parent.parent / "whatsapp-bridge")
BRIDGE_SCRIPT = os.path.join(BRIDGE_DIR, "bridge.js")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

async def start_bridge(
    port: int,
    session_dir: str,
    cache_dir: str,
    allowed_numbers: list[str] | None = None,
    mode: str = "dedicated",
) -> bool:
    global _bridge_process
    async with _bridge_lock:
        # If process is alive, keep it (even if WA not yet connected — may be pairing)
        if _bridge_process and _bridge_process.poll() is None:
            return True

        await _ensure_npm_install()

        cmd = [
            "node", BRIDGE_SCRIPT,
            "--port", str(port),
            "--session", session_dir,
            "--cache-dir", cache_dir,
            "--mode", mode,
        ]
        if allowed_numbers:
            cmd += ["--allowed-numbers", ",".join(allowed_numbers)]

        _kill_port_process(port)
        PrintStyle.info("WhatsApp: starting bridge")
        _bridge_process = _BridgeProcess(subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BRIDGE_DIR,
        ), port)
        _start_log_reader(_bridge_process)
        _bridge_config.clear()
        _bridge_config.update({"port": port, "mode": mode, "allowed_numbers": sorted(allowed_numbers or [])})

        # Wait for bridge to become healthy
        for _ in range(20):
            await asyncio.sleep(0.5)
            if _bridge_process.poll() is not None:
                PrintStyle.error("WhatsApp: bridge process exited unexpectedly")
                return False
            if await _check_health(port):
                return True

        PrintStyle.warning("WhatsApp: bridge started but not yet connected")
        return True


async def stop_bridge() -> None:
    global _bridge_process
    async with _bridge_lock:
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
        _bridge_process = None
        _bridge_config.clear()
        PrintStyle.info("WhatsApp: bridge stopped")


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
    allowed_numbers: list[str] | None = None,
    mode: str = "dedicated",
) -> bool:
    """Start bridge if needed and wait for HTTP server only (not WA connection)."""
    global _bridge_process
    async with _bridge_lock:
        if _bridge_process and _bridge_process.poll() is None:
            if await _check_http_up(port):
                return True

        await _ensure_npm_install()

        cmd = [
            "node", BRIDGE_SCRIPT,
            "--port", str(port),
            "--session", session_dir,
            "--cache-dir", cache_dir,
            "--mode", mode,
        ]
        if allowed_numbers:
            cmd += ["--allowed-numbers", ",".join(allowed_numbers)]

        _kill_port_process(port)
        PrintStyle.info("WhatsApp: starting bridge for pairing")
        _bridge_process = _BridgeProcess(subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BRIDGE_DIR,
        ), port)
        _start_log_reader(_bridge_process)

        for _ in range(20):
            await asyncio.sleep(0.5)
            if _bridge_process.poll() is not None:
                PrintStyle.error("WhatsApp: bridge process exited unexpectedly")
                return False
            if await _check_http_up(port):
                return True

        return False


def is_process_alive() -> bool:
    return _bridge_process is not None and _bridge_process.poll() is None


def get_running_config() -> dict:
    return dict(_bridge_config)


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

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


async def _ensure_npm_install() -> None:
    node_modules = os.path.join(BRIDGE_DIR, "node_modules")
    if os.path.isdir(node_modules):
        return
    PrintStyle.info("WhatsApp: installing bridge dependencies")
    proc = await asyncio.create_subprocess_exec(
        "npm", "install", "--production",
        cwd=BRIDGE_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        PrintStyle.error(f"WhatsApp: npm install failed: {stdout.decode()}")
        raise RuntimeError("npm install failed")


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
    def _reader():
        assert process.stdout
        for line in iter(process.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                PrintStyle.standard(f"WhatsApp bridge: {text}")
        process.stdout.close()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
