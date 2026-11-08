from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlencode

from helpers import files
from helpers.localization import Localization


STATE_DIR = Path(files.get_abs_path("usr", "plugins", "_desktop", "virtual_desktop"))
DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 900
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
MIN_WIDTH = 360
MIN_HEIGHT = 240
SESSION_PATH = "/desktop/session"
XPRA_HTML_ROOT_CANDIDATES = (
    Path("/usr/share/xpra/www"),
)
XPRA_START_ENV = {
    "XPRA_SYSTEM_DBUS_TIMEOUT": "1",
    "XPRA_SYSTEM_CUPS_TIMEOUT": "1",
}


ResizeCallback = Callable[[int, int], dict[str, Any]]


@dataclass
class VirtualDesktopEndpoint:
    token: str
    host: str
    port: int
    owner: str = "desktop"
    title: str = "Desktop"
    resize: ResizeCallback | None = None
    password: str = field(default="", repr=False)


class VirtualDesktopRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._endpoints: dict[str, VirtualDesktopEndpoint] = {}

    def register(self, endpoint: VirtualDesktopEndpoint) -> None:
        with self._lock:
            self._endpoints[str(endpoint.token)] = endpoint

    def unregister(self, token: str) -> None:
        with self._lock:
            self._endpoints.pop(str(token), None)

    def proxy_for_token(self, token: str) -> VirtualDesktopEndpoint | None:
        with self._lock:
            endpoint = self._endpoints.get(str(token or ""))
            if not endpoint:
                return None
            return endpoint

    def resize(self, token: str, width: int, height: int) -> dict[str, Any]:
        with self._lock:
            endpoint = self._endpoints.get(str(token or ""))
        if not endpoint:
            return {"ok": False, "error": "Virtual desktop session not found."}
        if not endpoint.resize:
            return {"ok": True, "resized": False, "reason": "Session does not expose resize."}
        return endpoint.resize(width, height)


def register_session(
    *,
    token: str,
    host: str,
    port: int,
    owner: str = "desktop",
    title: str = "Desktop",
    resize: ResizeCallback | None = None,
    password: str = "",
) -> None:
    get_registry().register(
        VirtualDesktopEndpoint(
            token=str(token),
            host=str(host),
            port=int(port),
            owner=str(owner),
            title=str(title),
            resize=resize,
            password=password,
        ),
    )


def unregister_session(token: str) -> None:
    get_registry().unregister(token)


def proxy_for_token(token: str) -> VirtualDesktopEndpoint | None:
    return get_registry().proxy_for_token(token)


def resize_session(token: str, width: int, height: int) -> dict[str, Any]:
    return get_registry().resize(token, width, height)


def get_registry() -> VirtualDesktopRegistry:
    global _registry
    try:
        return _registry
    except NameError:
        _registry = VirtualDesktopRegistry()
        return _registry


def session_url(
    token: str,
    *,
    title: str = "Desktop",
    encoding: str = "jpeg",
    quality: int = 85,
    speed: int = 80,
    file_transfer: bool = True,
    printing: bool = True,
) -> str:
    quoted_token = quote(str(token), safe="")
    base_path = f"{SESSION_PATH}/{quoted_token}/"
    options = {
        "path": base_path,
        "title": title,
        "quality": str(max(0, min(100, int(quality)))),
        "speed": str(max(0, min(100, int(speed)))),
        "sharing": "true",
        "clipboard": "true",
        "clipboard_direction": "both",
        "clipboard_poll": "true",
        "clipboard_preferred_format": "text/plain",
        "printing": str(bool(printing)).lower(),
        "file_transfer": str(bool(file_transfer)).lower(),
        "sound": "false",
        "offscreen": "true",
        "floating_menu": "false",
        "xpramenu": "false",
    }
    if encoding:
        options["encoding"] = str(encoding)
    query = urlencode(options)
    return f"{base_path}index.html?{query}"


def collect_status() -> dict[str, Any]:
    binaries = {
        "xpra": shutil.which("xpra") or "",
        "Xvfb": shutil.which("Xvfb") or "",
        "xfce4-session": shutil.which("xfce4-session") or "",
        "dbus-launch": shutil.which("dbus-launch") or "",
        "xrandr": shutil.which("xrandr") or "",
        "xdotool": shutil.which("xdotool") or "",
        "xsetroot": shutil.which("xsetroot") or "",
    }
    packages = {
        "xpra-x11": _package_installed("xpra-x11") if binaries["xpra"] else False,
    }
    xpra_html_root = find_xpra_html_root()
    missing = [
        name
        for name in ("xpra", "Xvfb", "xfce4-session", "dbus-launch", "xrandr", "xdotool")
        if not binaries[name]
    ]
    if binaries["xpra"] and not packages["xpra-x11"]:
        missing.append("xpra-x11")
    if not xpra_html_root:
        missing.append("xpra-html5")
    healthy = not missing
    return {
        "ok": True,
        "healthy": healthy,
        "state": "healthy" if healthy else "missing",
        "binaries": binaries,
        "packages": packages,
        "xpra_html_root": str(xpra_html_root) if xpra_html_root else "",
        "message": (
            "Virtual desktop sessions are available."
            if healthy
            else f"Virtual desktop sessions need: {', '.join(missing)}."
        ),
    }


def find_xpra_html_root() -> Path | None:
    for root in XPRA_HTML_ROOT_CANDIDATES:
        if (root / "index.html").exists() or (root / "connect.html").exists():
            return root
    return None


def _package_installed(package: str) -> bool:
    if not shutil.which("dpkg-query"):
        return True
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Status}", package],
        check=False,
        text=True,
        capture_output=True,
        timeout=8,
    )
    return result.returncode == 0 and "install ok installed" in result.stdout


from helpers.native_display import normalize_size


def resize_display(*, display, width, height, max_width=MAX_WIDTH, max_height=MAX_HEIGHT,
                   window_class="", keys=(), xauthority="", home="", settle_seconds=0.15):
    from helpers import native_display
    result = native_display.resize_display(
        display=display, width=width, height=height, max_width=max_width, max_height=max_height,
        env=_display_env(display, xauthority=xauthority, home=home), settle_seconds=settle_seconds)
    if result.get('ok') and window_class:
        fit_window(display=display, width=result['width'], height=result['height'],
                   window_class=window_class, keys=keys, xauthority=xauthority, home=home)
    return result


def current_display_size(display, *, xauthority="", home=""):
    from helpers import native_display
    return native_display.current_display_size(display, env=_display_env(display, xauthority=xauthority, home=home))


def fit_window_until(
    *,
    display: int,
    width: int,
    height: int,
    window_class: str = "",
    keys: tuple[str, ...] = (),
    settle_seconds: float = 4.0,
    timeout_seconds: float = 10.0,
    process: subprocess.Popen[Any] | None = None,
    xauthority: str = "",
    home: str = "",
) -> None:
    xdotool = shutil.which("xdotool")
    if not xdotool:
        return
    deadline = time.time() + timeout_seconds
    settle_until = 0.0
    while time.time() < deadline:
        window_id = _find_window(display, window_class=window_class, xauthority=xauthority, home=home)
        if window_id:
            if not settle_until:
                settle_until = time.time() + settle_seconds
            fit_window(
                display=display,
                width=width,
                height=height,
                window_class=window_class,
                keys=keys,
                xauthority=xauthority,
                home=home,
            )
            if time.time() >= settle_until:
                return
            time.sleep(0.5)
            continue
        if process and process.poll() is not None:
            return
        time.sleep(0.25)


def fit_window(
    *,
    display: int,
    width: int,
    height: int,
    window_class: str = "",
    keys: tuple[str, ...] = (),
    xauthority: str = "",
    home: str = "",
) -> bool:
    xdotool = shutil.which("xdotool")
    if not xdotool:
        return False
    env = _display_env(display, xauthority=xauthority, home=home)
    window_id = _find_window(display, window_class=window_class, xauthority=xauthority, home=home)
    if not window_id:
        return False
    subprocess.run(
        [xdotool, "windowactivate", window_id],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        env=env,
    )
    subprocess.run(
        [xdotool, "windowmove", window_id, "0", "0", "windowsize", window_id, str(width), str(height)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        env=env,
    )
    for key in keys:
        subprocess.run(
            [xdotool, "key", "--clearmodifiers", key],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            env=env,
        )
    return True


def has_window(
    display: int,
    *,
    window_class: str = "",
    name: str = "",
    xauthority: str = "",
    home: str = "",
) -> bool:
    return bool(find_window(display, window_class=window_class, name=name, xauthority=xauthority, home=home))


def find_window(
    display: int,
    *,
    window_class: str = "",
    name: str = "",
    xauthority: str = "",
    home: str = "",
) -> str:
    return _find_window(display, window_class=window_class, name=name, xauthority=xauthority, home=home)


def close_windows(
    display: int,
    *,
    names: tuple[str, ...] = (),
    window_class: str = "",
    xauthority: str = "",
    home: str = "",
) -> int:
    xdotool = shutil.which("xdotool")
    if not xdotool:
        return 0
    closed = 0
    env = _display_env(display, xauthority=xauthority, home=home)
    for pattern in names:
        command = [xdotool, "search", "--onlyvisible"]
        if window_class:
            command.extend(["--class", window_class])
        command.extend(["--name", pattern])
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
            env=env,
        )
        for window_id in [line.strip() for line in result.stdout.splitlines() if line.strip()]:
            subprocess.run(
                [xdotool, "windowclose", window_id],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                env=env,
            )
            closed += 1
    return closed


def _find_window(
    display: int,
    *,
    window_class: str = "",
    name: str = "",
    xauthority: str = "",
    home: str = "",
) -> str:
    xdotool = shutil.which("xdotool")
    if not xdotool:
        return ""
    command = [xdotool, "search", "--onlyvisible"]
    if window_class:
        command.extend(["--class", window_class])
    if name:
        command.extend(["--name", name])
    if not window_class and not name:
        command.extend(["--name", "."])
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
        env=_display_env(display, xauthority=xauthority, home=home),
    )
    window_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return window_ids[-1] if window_ids else ""


def _display_env(display: int, *, xauthority: str = "", home: str = "") -> dict[str, str]:
    runtime_dir = STATE_DIR / "xdg-runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    try:
        runtime_dir.chmod(0o700)
    except OSError:
        pass
    env = {
        **os.environ,
        "DISPLAY": f":{display}",
        "XDG_RUNTIME_DIR": str(runtime_dir),
        "TZ": Localization.get().get_timezone(),
    }
    if home:
        env["HOME"] = home
    if xauthority:
        env["XAUTHORITY"] = xauthority
    return env
