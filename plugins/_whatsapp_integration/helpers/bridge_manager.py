"""
WhatsApp bridge subprocess manager.

No agent/tool dependencies.
"""

import asyncio
import os
import subprocess
import threading
from pathlib import Path

from helpers.print_style import PrintStyle


_bridge_process: subprocess.Popen | None = None
_bridge_lock = asyncio.Lock()

BRIDGE_DIR = str(Path(__file__).parent.parent / "whatsapp-bridge")
BRIDGE_SCRIPT = os.path.join(BRIDGE_DIR, "bridge.js")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

async def start_bridge(
    port: int,
    session_dir: str,
    cache_dir: str,
    allowed_users: list[str] | None = None,
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
        ]
        if allowed_users:
            cmd += ["--allowed-users", ",".join(allowed_users)]

        PrintStyle.info("WhatsApp: starting bridge")
        _bridge_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BRIDGE_DIR,
        )
        _start_log_reader(_bridge_process)

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
    allowed_users: list[str] | None = None,
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
        ]
        if allowed_users:
            cmd += ["--allowed-users", ",".join(allowed_users)]

        PrintStyle.info("WhatsApp: starting bridge for pairing")
        _bridge_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=BRIDGE_DIR,
        )
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


def _start_log_reader(process: subprocess.Popen) -> None:
    def _reader():
        assert process.stdout
        for line in iter(process.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                PrintStyle.standard(f"WhatsApp bridge: {text}")
        process.stdout.close()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
