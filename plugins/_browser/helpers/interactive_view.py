from __future__ import annotations

import os
import select
import shutil
import socket
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from helpers import files, virtual_desktop
from helpers.print_style import PrintStyle


DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
START_TIMEOUT_SECONDS = 15.0


def keyboard_options() -> dict[str, str]:
    """Resolve the configured XKB keyboard layout for browser displays."""
    from plugins._browser.helpers.config import (
        KEYBOARD_LAYOUT_KEY,
        KEYBOARD_VARIANT_KEY,
        get_browser_config,
    )

    config = get_browser_config()
    return {
        "layout": str(config.get(KEYBOARD_LAYOUT_KEY, "") or "").strip(),
        "variant": str(config.get(KEYBOARD_VARIANT_KEY, "") or "").strip(),
    }


def collect_status() -> dict[str, Any]:
    binaries = {
        name: shutil.which(name) or ""
        for name in ("Xvfb", "xpra", "xrandr")
    }
    html_root = virtual_desktop.find_xpra_html_root()
    missing = [name for name, path in binaries.items() if not path]
    if not html_root:
        missing.append("xpra-html5")
    return {
        "available": not missing,
        "missing": missing,
        "binaries": binaries,
        "xpra_html_root": str(html_root or ""),
    }


class BrowserInteractiveView:
    """Own one private X display and its optional Xpra viewer."""

    def __init__(self, context_id: str) -> None:
        self.context_id = str(context_id)
        self.token = f"browser-{uuid.uuid4().hex}"
        self.state_dir = Path(files.get_abs_path("tmp", "browser", "displays", self.token))
        self.display: int | None = None
        self.port = 0
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self._xvfb: subprocess.Popen[Any] | None = None
        self._xpra: subprocess.Popen[Any] | None = None
        self._lock = threading.RLock()

    @property
    def display_name(self) -> str:
        return f":{self.display}" if self.display is not None else ""

    def ensure_display(self) -> str:
        with self._lock:
            if self._running(self._xvfb) and self.display is not None:
                return self.display_name

            self._stop_locked()
            xvfb = shutil.which("Xvfb")
            if not xvfb:
                return ""

            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.state_dir.chmod(0o700)
            read_fd, write_fd = os.pipe()
            try:
                process = subprocess.Popen(
                    [
                        xvfb,
                        "-displayfd",
                        str(write_fd),
                        "-screen",
                        "0",
                        f"{virtual_desktop.MAX_WIDTH}x{virtual_desktop.MAX_HEIGHT}x24",
                        "+extension",
                        "GLX",
                        "+extension",
                        "RANDR",
                        "+extension",
                        "RENDER",
                        "+extension",
                        "Composite",
                        "-nolisten",
                        "tcp",
                        "-noreset",
                        "-ac",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    pass_fds=(write_fd,),
                )
            except OSError:
                os.close(read_fd)
                return ""
            finally:
                os.close(write_fd)

            try:
                ready, _, _ = select.select([read_fd], [], [], 5)
                display_number = os.read(read_fd, 32).decode().strip() if ready else ""
            finally:
                os.close(read_fd)

            if not display_number.isdigit() or process.poll() is not None:
                self._terminate(process)
                return ""

            self._xvfb = process
            self.display = int(display_number)
            self._apply_keyboard_layout()
            self.resize(self.width, self.height)
            return self.display_name

    def ensure_viewer(self, width: int = 0, height: int = 0) -> dict[str, Any]:
        with self._lock:
            display_name = self.ensure_display()
            if not display_name:
                return self._unavailable("Xvfb is unavailable.")

            status = collect_status()
            if not status["available"]:
                return self._unavailable(
                    f"Interactive Browser runtime needs: {', '.join(status['missing'])}."
                )

            self.resize(width or self.width, height or self.height)
            if not self._running(self._xpra):
                try:
                    self._start_xpra(str(status["binaries"]["xpra"]))
                except Exception as exc:
                    PrintStyle.warning(f"Interactive Browser viewer failed to start: {exc}")
                    self._terminate(self._xpra)
                    self._xpra = None
                    self.port = 0
                    virtual_desktop.unregister_session(self.token)
                    return self._unavailable(str(exc))

            virtual_desktop.register_session(
                token=self.token,
                host="127.0.0.1",
                port=self.port,
                owner="browser",
                title="Browser",
                resize=self.resize,
            )
            return {
                "available": True,
                "token": self.token,
                "url": virtual_desktop.session_url(
                    self.token,
                    title="Browser",
                    encoding="",
                    quality=90,
                    speed=90,
                    file_transfer=False,
                    printing=False,
                ),
                "width": self.width,
                "height": self.height,
            }

    def resize(self, width: int, height: int) -> dict[str, Any]:
        with self._lock:
            target_width, target_height = virtual_desktop.normalize_size(width, height)
            self.width = target_width
            self.height = target_height
            if self.display is None or not self._running(self._xvfb):
                return {
                    "ok": False,
                    "error": "Browser display is unavailable.",
                    "width": target_width,
                    "height": target_height,
                }
            result = virtual_desktop.resize_display(
                display=self.display,
                width=target_width,
                height=target_height,
                settle_seconds=0,
            )
            return result

    def close(self) -> None:
        with self._lock:
            self._stop_locked()
        shutil.rmtree(self.state_dir, ignore_errors=True)

    def _apply_keyboard_layout(self) -> None:
        """Apply the configured XKB layout to this private display."""
        if self.display is None:
            return
        options = keyboard_options()
        if not options["layout"]:
            return
        setxkbmap = shutil.which("setxkbmap")
        if not setxkbmap:
            return
        command = [setxkbmap, "-display", self.display_name, "-layout", options["layout"]]
        if options["variant"]:
            command.extend(["-variant", options["variant"]])
        try:
            subprocess.run(
                command,
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _keyboard_xpra_args(self) -> list[str]:
        options = keyboard_options()
        if not options["layout"]:
            return []
        args = [
            "--keyboard-sync=no",
            "--keyboard-layout", options["layout"],
        ]
        if options["variant"]:
            args.extend(["--keyboard-variant", options["variant"]])
        return args

    def _start_xpra(self, xpra: str) -> None:
        self.port = self._free_port()
        runtime_dir = self.state_dir / "runtime"
        socket_dir = self.state_dir / "sockets"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        socket_dir.mkdir(parents=True, exist_ok=True)
        runtime_dir.chmod(0o700)
        env = {
            **virtual_desktop.XPRA_START_ENV,
            **os.environ,
            "DISPLAY": self.display_name,
            "XDG_RUNTIME_DIR": str(runtime_dir),
        }
        self._xpra = subprocess.Popen(
            [
                xpra,
                "shadow",
                self.display_name,
                "--daemon=no",
                "--mdns=no",
                "--mmap=no",
                "--html=on",
                "--tray=no",
                "--system-tray=no",
                "--notifications=no",
                "--clipboard=yes",
                "--clipboard-direction=both",
                "--file-transfer=no",
                "--open-files=no",
                "--open-url=no",
                "--printing=no",
                "--audio=no",
                "--speaker=off",
                "--microphone=off",
                "--sharing=yes",
                "--resize-display=yes",
                "--encoding=auto",
                "--quality=90",
                "--speed=90",
                *self._keyboard_xpra_args(),
                f"--bind-tcp=127.0.0.1:{self.port}",
                f"--socket-dir={socket_dir}",
                f"--log-dir={self.state_dir}",
                "--log-file=xpra.log",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self._wait_for_port(self._xpra, self.port)

    def _stop_locked(self) -> None:
        virtual_desktop.unregister_session(self.token)
        self._terminate(self._xpra)
        self._terminate(self._xvfb)
        self._xpra = None
        self._xvfb = None
        self.port = 0
        self.display = None

    def _unavailable(self, error: str) -> dict[str, Any]:
        return {
            "available": False,
            "error": str(error or "Interactive Browser viewer is unavailable."),
        }

    @staticmethod
    def _running(process: subprocess.Popen[Any] | None) -> bool:
        return bool(process and process.poll() is None)

    @staticmethod
    def _terminate(process: subprocess.Popen[Any] | None) -> None:
        if not process or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    @staticmethod
    def _free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    @staticmethod
    def _wait_for_port(
        process: subprocess.Popen[Any],
        port: int,
        timeout: float = START_TIMEOUT_SECONDS,
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Xpra exited before its Browser endpoint was ready.")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.1)
        raise TimeoutError("Timed out waiting for the interactive Browser endpoint.")
