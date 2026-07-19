from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlencode

from helpers import files


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


ResizeCallback = Callable[[int, int], dict[str, Any]]


@dataclass
class VirtualDesktopEndpoint:
    token: str
    host: str
    port: int
    owner: str = "desktop"
    title: str = "Desktop"
    resize: ResizeCallback | None = None


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
) -> None:
    get_registry().register(
        VirtualDesktopEndpoint(
            token=str(token),
            host=str(host),
            port=int(port),
            owner=str(owner),
            title=str(title),
            resize=resize,
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


def session_url(token: str, *, title: str = "Desktop") -> str:
    quoted_token = quote(str(token), safe="")
    base_path = f"{SESSION_PATH}/{quoted_token}/"
    query = urlencode(
        {
            "path": base_path,
            "title": title,
            "encoding": "jpeg",
            "quality": "85",
            "speed": "80",
            "sharing": "true",
            "clipboard": "true",
            "clipboard_direction": "both",
            "clipboard_poll": "true",
            "clipboard_preferred_format": "text/plain",
            "printing": "true",
            "file_transfer": "true",
            "sound": "false",
            "offscreen": "true",
            "floating_menu": "false",
            "xpramenu": "false",
        },
    )
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


def normalize_size(
    width: int | float | str,
    height: int | float | str,
    *,
    max_width: int = MAX_WIDTH,
    max_height: int = MAX_HEIGHT,
    min_width: int = MIN_WIDTH,
    min_height: int = MIN_HEIGHT,
) -> tuple[int, int]:
    requested_width = max(1, int(float(width or DEFAULT_WIDTH)))
    requested_height = max(1, int(float(height or DEFAULT_HEIGHT)))
    scale = min(max_width / requested_width, max_height / requested_height, 1.0)
    if scale < 1.0:
        requested_width = max(1, math.floor(requested_width * scale))
        requested_height = max(1, math.floor(requested_height * scale))
    return (
        max(min_width, min(max_width, requested_width)),
        max(min_height, min(max_height, requested_height)),
    )


def resize_display(
    *,
    display: int,
    width: int,
    height: int,
    max_width: int = MAX_WIDTH,
    max_height: int = MAX_HEIGHT,
    window_class: str = "",
    keys: tuple[str, ...] = (),
    xauthority: str = "",
    home: str = "",
) -> dict[str, Any]:
    target_width, target_height = normalize_size(width, height, max_width=max_width, max_height=max_height)
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return {"ok": False, "error": "xrandr is not installed."}

    env = _display_env(display, xauthority=xauthority, home=home)
    current_before = current_display_size(display, xauthority=xauthority, home=home)
    if current_before == (target_width, target_height):
        if window_class:
            fit_window(
                display=display,
                width=target_width,
                height=target_height,
                window_class=window_class,
                keys=keys,
                xauthority=xauthority,
                home=home,
            )
        return {"ok": True, "width": target_width, "height": target_height, "resized": False}

    _ensure_xrandr_mode(env, target_width, target_height)
    result = _select_xrandr_mode(env, target_width, target_height)
    if result.returncode != 0:
        result = subprocess.run(
            [xrandr, "--fb", f"{target_width}x{target_height}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
            env=env,
        )
    time.sleep(0.15)
    current = current_display_size(display, xauthority=xauthority, home=home)
    ok = current == (target_width, target_height)
    if ok:
        if window_class:
            fit_window(
                display=display,
                width=target_width,
                height=target_height,
                window_class=window_class,
                keys=keys,
                xauthority=xauthority,
                home=home,
            )
        return {"ok": True, "width": target_width, "height": target_height, "resized": True}
    detail = (result.stderr or result.stdout or "xrandr resize failed").strip()
    return {
        "ok": False,
        "error": detail,
        "width": current[0] if current else target_width,
        "height": current[1] if current else target_height,
    }


def _ensure_xrandr_mode(env: dict[str, str], width: int, height: int) -> None:
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return
    output, existing_modes = _xrandr_output_modes(env)
    if not output:
        return
    mode = f"{width}x{height}"
    if mode not in existing_modes:
        subprocess.run(
            [xrandr, "--newmode", mode, "0", str(width), "0", "0", "0", str(height), "0", "0", "0"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            env=env,
        )
        subprocess.run(
            [xrandr, "--addmode", output, mode],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            env=env,
        )


def _select_xrandr_mode(env: dict[str, str], width: int, height: int) -> subprocess.CompletedProcess[str]:
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return subprocess.CompletedProcess([], 1, "", "xrandr is not installed.")
    output, _ = _xrandr_output_modes(env)
    if not output:
        return subprocess.CompletedProcess([], 1, "", "No connected XRandR output found.")
    mode = f"{width}x{height}"
    return subprocess.run(
        [xrandr, "--output", output, "--mode", mode],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
        env=env,
    )


def _xrandr_output_modes(env: dict[str, str]) -> tuple[str, set[str]]:
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return "", set()
    result = subprocess.run(
        [xrandr, "-q"],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
        env=env,
    )
    output = ""
    modes: set[str] = set()
    for line in result.stdout.splitlines():
        output_match = re.match(r"^(\S+)\s+connected\b", line)
        if output_match:
            output = output_match.group(1)
            continue
        if output:
            mode_match = re.match(r"^\s+(\d+x\d+)\b", line)
            if mode_match:
                modes.add(mode_match.group(1))
    return output, modes


def current_display_size(display: int, *, xauthority: str = "", home: str = "") -> tuple[int, int] | None:
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return None
    result = subprocess.run(
        [xrandr, "-q"],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
        env=_display_env(display, xauthority=xauthority, home=home),
    )
    match = re.search(r"\bcurrent\s+(\d+)\s+x\s+(\d+)", result.stdout)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


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
    }
    if home:
        env["HOME"] = home
    if xauthority:
        env["XAUTHORITY"] = xauthority
    return env
