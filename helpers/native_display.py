"""Standard-library XRandR operations shared by host desktops and guest browsers."""
import math
import os
import re
import shutil
import subprocess
import time
from typing import Any
DEFAULT_WIDTH, DEFAULT_HEIGHT = 1440, 900
MAX_WIDTH, MAX_HEIGHT = 1920, 1080
MIN_WIDTH, MIN_HEIGHT = 360, 240

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
    settle_seconds: float = 0.15,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    target_width, target_height = normalize_size(width, height, max_width=max_width, max_height=max_height)
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return {"ok": False, "error": "xrandr is not installed."}

    env = env or {**os.environ, "DISPLAY": f":{display}"}
    current_before = current_display_size(display, env=env)
    if current_before == (target_width, target_height):
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
    if settle_seconds > 0:
        time.sleep(settle_seconds)
    current = current_display_size(display, env=env)
    ok = current == (target_width, target_height)
    if ok:
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


def current_display_size(display: int, *, env: dict[str, str] | None = None) -> tuple[int, int] | None:
    xrandr = shutil.which("xrandr")
    if not xrandr:
        return None
    result = subprocess.run(
        [xrandr, "-q"],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
        env=env or {**os.environ, "DISPLAY": f":{display}"},
    )
    match = re.search(r"\bcurrent\s+(\d+)\s+x\s+(\d+)", result.stdout)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))

