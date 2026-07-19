from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SESSION_ID = "agent-zero-desktop"
PLUGIN_NAME = "_desktop"
BASE_DIR = Path(os.environ.get("A0_BASE_DIR") or ("/a0" if Path("/a0").exists() else PROJECT_ROOT))
STATE_DIR = BASE_DIR / "usr" / "plugins" / PLUGIN_NAME
RETIRED_STATE_DIR = BASE_DIR / "usr" / PLUGIN_NAME
SESSION_DIR = STATE_DIR / "sessions"
PROFILE_DIR = STATE_DIR / "profiles"
SCREENSHOT_DIR = Path(os.environ.get("A0_DESKTOP_SCREENSHOT_DIR") or BASE_DIR / "tmp" / "desktop" / "screenshots")
RECENT_SCREENSHOT_SECONDS = 600
_SAFE_CONTEXT_RE = re.compile(r"[^a-zA-Z0-9_.-]+")
_SCREENSHOT_SUFFIXES = {".png", ".jpg", ".jpeg", ".xwd"}


def session_manifest_path(session_id: str = SESSION_ID) -> Path:
    return Path(os.environ.get("A0_DESKTOP_MANIFEST") or SESSION_DIR / f"{session_id}.json")


def context_screenshot_dir(context_id: str = "") -> Path:
    return SCREENSHOT_DIR / _safe_context_id(context_id)


def chat_screenshot_dir(context_id: str = "") -> Path:
    return BASE_DIR / "usr" / "chats" / _safe_context_id(context_id) / "screenshots" / "desktop"


def normalize_a0_path(path: str | Path) -> str:
    candidate = Path(path)
    try:
        relative = candidate.resolve(strict=False).relative_to(BASE_DIR.resolve(strict=False))
    except ValueError:
        return str(candidate)
    return "/a0/" + str(relative).replace(os.sep, "/")


def _safe_context_id(context_id: str = "") -> str:
    raw = str(context_id or os.environ.get("A0_DESKTOP_CONTEXT_ID") or "default")
    return _SAFE_CONTEXT_RE.sub("_", raw).strip("._") or "default"


def session_manifest_exists(session_id: str = SESSION_ID) -> bool:
    return session_manifest_path(session_id).exists()


def collect_state(
    *,
    include_screenshot: bool = False,
    screenshot_path: str | Path | None = None,
    context_id: str = "",
    screenshot_transport: str = "ephemeral",
) -> dict[str, Any]:
    errors: list[str] = []
    env_info = resolve_environment(errors=errors)
    display = env_info["display"]
    profile_dir = env_info["profile_dir"]
    env = display_env(display=display, profile_dir=profile_dir)

    capabilities = collect_capabilities()
    for name in ("xdotool", "xrandr", "xwininfo", "xprop"):
        if not capabilities.get(name):
            errors.append(f"{name} is not installed; install Desktop runtime dependencies through the _desktop plugin hook.")

    size = collect_display_size(env, capabilities, errors)
    pointer = collect_pointer(env, capabilities, errors)
    active_window = collect_active_window(env, capabilities, errors)
    windows = collect_windows(env, capabilities, errors)
    screenshot = latest_screenshot(context_id=context_id)

    if include_screenshot:
        screenshot = capture_screenshot(
            env,
            capabilities,
            path=screenshot_path,
            errors=errors,
            context_id=context_id,
            transport=screenshot_transport,
        )

    return stable_state(
        context_id=context_id,
        display=display,
        profile_dir=profile_dir,
        size=size,
        pointer=pointer,
        active_window=active_window,
        windows=windows,
        screenshot=screenshot,
        capabilities=capabilities,
        errors=errors,
    )


def capture_screenshot(
    env: dict[str, str] | None = None,
    capabilities: dict[str, str] | None = None,
    *,
    path: str | Path | None = None,
    errors: list[str] | None = None,
    context_id: str = "",
    transport: str = "ephemeral",
) -> dict[str, Any]:
    local_errors = errors if errors is not None else []
    capabilities = capabilities or collect_capabilities()
    if not env:
        env_errors: list[str] = []
        env_info = resolve_environment(errors=env_errors)
        local_errors.extend(env_errors)
        env = display_env(display=env_info["display"], profile_dir=env_info["profile_dir"])

    xwd = capabilities.get("xwd") or shutil.which("xwd") or ""
    if not xwd:
        message = "xwd is not installed; install x11-apps through the _desktop plugin hook."
        local_errors.append(message)
        return {"ok": False, "path": "", "format": "", "captured_at": "", "error": message}

    explicit_path = path is not None and str(path).strip() != ""
    transport_mode = str(transport or "").strip().lower()
    chat_scoped = bool(not explicit_path and transport_mode == "path" and str(context_id or "").strip())
    ephemeral_ref = not explicit_path and transport_mode != "path"
    screenshot_dir = chat_screenshot_dir(context_id) if chat_scoped else context_screenshot_dir(context_id)
    if not explicit_path and not chat_scoped:
        prune_context_screenshots(context_id=context_id)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    millis = int((time.time() % 1) * 1000)
    target = Path(path) if explicit_path else screenshot_dir / f"desktop-{timestamp}-{millis:03d}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw_path = target.with_suffix(".xwd")
    safe_context = _safe_context_id(context_id)

    result = run([xwd, "-root", "-silent", "-out", str(raw_path)], env=env, timeout=8)
    if result.returncode != 0:
        detail = command_output(result) or "xwd screenshot capture failed."
        local_errors.append(detail)
        raw_path.unlink(missing_ok=True)
        return {"ok": False, "path": "", "format": "", "captured_at": "", "error": detail}

    if target.suffix.lower() == ".xwd":
        if not explicit_path and not chat_scoped:
            prune_context_screenshots(context_id=context_id, keep_path=raw_path)
        return {
            "ok": True,
            "path": str(raw_path),
            "a0_path": normalize_a0_path(raw_path),
            "format": "xwd",
            "captured_at": iso_now(),
            "recent": True,
            "ephemeral": not explicit_path and not chat_scoped,
            "chat_scoped": chat_scoped,
            "context_id": safe_context,
            "error": "",
        }

    try:
        from PIL import Image

        with Image.open(raw_path) as image:
            image.save(target)
            width = int(image.width)
            height = int(image.height)
        raw_path.unlink(missing_ok=True)
        if ephemeral_ref:
            return ephemeral_screenshot_result(
                target,
                context_id=context_id,
                image_format=target.suffix.lower().lstrip(".") or "png",
                width=width,
                height=height,
            )
        if not explicit_path and not chat_scoped:
            prune_context_screenshots(context_id=context_id, keep_path=target)
        return {
            "ok": True,
            "path": str(target),
            "a0_path": normalize_a0_path(target),
            "format": target.suffix.lower().lstrip(".") or "png",
            "width": width,
            "height": height,
            "captured_at": iso_now(),
            "recent": True,
            "ephemeral": not explicit_path and not chat_scoped,
            "chat_scoped": chat_scoped,
            "context_id": safe_context,
            "error": "",
        }
    except Exception as exc:
        try:
            converted = convert_xwd_to_image(raw_path, target)
            raw_path.unlink(missing_ok=True)
            if ephemeral_ref:
                return ephemeral_screenshot_result(
                    target,
                    context_id=context_id,
                    image_format=target.suffix.lower().lstrip(".") or "png",
                    width=converted["width"],
                    height=converted["height"],
                )
            if not explicit_path and not chat_scoped:
                prune_context_screenshots(context_id=context_id, keep_path=target)
            return {
                "ok": True,
                "path": str(target),
                "a0_path": normalize_a0_path(target),
                "format": target.suffix.lower().lstrip(".") or "png",
                "width": converted["width"],
                "height": converted["height"],
                "captured_at": iso_now(),
                "recent": True,
                "ephemeral": not explicit_path and not chat_scoped,
                "chat_scoped": chat_scoped,
                "context_id": safe_context,
                "error": "",
            }
        except Exception as fallback_exc:
            message = f"Pillow could not convert the XWD screenshot: {exc}; fallback parser failed: {fallback_exc}"
        local_errors.append(message)
        if ephemeral_ref:
            raw_path.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            return {
                "ok": False,
                "path": "",
                "format": "",
                "captured_at": iso_now(),
                "recent": False,
                "ephemeral": True,
                "context_id": safe_context,
                "error": message,
            }
        return {
            "ok": True,
            "path": str(raw_path),
            "a0_path": normalize_a0_path(raw_path),
            "format": "xwd",
            "captured_at": iso_now(),
            "recent": True,
            "ephemeral": not explicit_path and not chat_scoped,
            "chat_scoped": chat_scoped,
            "context_id": safe_context,
            "error": message,
        }


def convert_xwd_to_image(raw_path: Path, target: Path) -> dict[str, int]:
    from PIL import Image

    data = raw_path.read_bytes()
    header, _ = parse_xwd_header(data)
    width = header["pixmap_width"]
    height = header["pixmap_height"]
    bytes_per_line = header["bytes_per_line"]
    bits_per_pixel = header["bits_per_pixel"]
    color_table_size = header["ncolors"] * 12
    pixel_offset = header["header_size"] + color_table_size
    if width <= 0 or height <= 0 or bytes_per_line <= 0:
        raise ValueError("invalid XWD dimensions")
    pixel_size = height * bytes_per_line
    if pixel_offset + pixel_size > len(data):
        raise ValueError("truncated XWD pixel data")

    if (header["red_mask"], header["green_mask"], header["blue_mask"]) != (
        0x00FF0000,
        0x0000FF00,
        0x000000FF,
    ):
        raise ValueError("unsupported XWD visual masks")
    raw_mode = {
        (24, 0): "BGR",
        (24, 1): "RGB",
        (32, 0): "BGRX",
        (32, 1): "XRGB",
    }.get((bits_per_pixel, header["byte_order"]))
    if not raw_mode:
        raise ValueError(f"unsupported XWD pixel layout: {bits_per_pixel} bpp")

    image = Image.frombytes(
        "RGB",
        (width, height),
        data[pixel_offset : pixel_offset + pixel_size],
        "raw",
        raw_mode,
        bytes_per_line,
        1,
    )
    image.save(target)
    return {"width": width, "height": height}


def parse_xwd_header(data: bytes) -> tuple[dict[str, int], str]:
    if len(data) < 100:
        raise ValueError("XWD header is too short")
    field_names = (
        "header_size",
        "file_version",
        "pixmap_format",
        "pixmap_depth",
        "pixmap_width",
        "pixmap_height",
        "xoffset",
        "byte_order",
        "bitmap_unit",
        "bitmap_bit_order",
        "bitmap_pad",
        "bits_per_pixel",
        "bytes_per_line",
        "visual_class",
        "red_mask",
        "green_mask",
        "blue_mask",
        "bits_per_rgb",
        "colormap_entries",
        "ncolors",
        "window_width",
        "window_height",
        "window_x",
        "window_y",
        "window_bdrwidth",
    )
    for endian in ("big", "little"):
        values = [int.from_bytes(data[index : index + 4], endian, signed=False) for index in range(0, 100, 4)]
        header = dict(zip(field_names, values, strict=True))
        if 100 <= header["header_size"] <= len(data) and header["file_version"] == 7:
            return header, endian
    raise ValueError("unsupported XWD header")


def resolve_environment(*, errors: list[str] | None = None, session_id: str = SESSION_ID) -> dict[str, str]:
    local_errors = errors if errors is not None else []
    manifest = session_manifest_path(session_id)
    payload: dict[str, Any] = {}
    if manifest.exists():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            local_errors.append(f"Desktop session manifest is unreadable: {exc}")
    elif not (os.environ.get("A0_DESKTOP_DISPLAY") or os.environ.get("DISPLAY")):
        local_errors.append(f"Desktop session manifest not found at {manifest}; open the Desktop canvas before GUI control.")

    display_value = str(
        os.environ.get("A0_DESKTOP_DISPLAY")
        or payload.get("display")
        or os.environ.get("DISPLAY")
        or ""
    ).strip()
    if display_value.startswith(":"):
        display = display_value
    elif display_value:
        display = f":{display_value}"
    else:
        display = ""
        local_errors.append("Desktop DISPLAY is unavailable; the persistent Desktop session is not running.")

    profile_dir = _state_path_from_retired_root(
        Path(
            os.environ.get("A0_DESKTOP_PROFILE")
            or os.environ.get("A0_DESKTOP_HOME")
            or payload.get("profile_dir")
            or os.environ.get("HOME")
            or PROFILE_DIR / session_id
        )
    )

    return {
        "display": display,
        "profile_dir": str(profile_dir),
        "manifest": str(manifest),
    }


def _state_path_from_retired_root(path: Path) -> Path:
    try:
        relative = path.resolve(strict=False).relative_to(
            RETIRED_STATE_DIR.resolve(strict=False)
        )
    except ValueError:
        return path
    return STATE_DIR / relative


def display_env(*, display: str, profile_dir: str) -> dict[str, str]:
    env = {
        **os.environ,
        "HOME": profile_dir,
        "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME") or str(Path(profile_dir) / ".config"),
        "XDG_DATA_HOME": os.environ.get("XDG_DATA_HOME") or str(Path(profile_dir) / ".local" / "share"),
        "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME") or str(Path(profile_dir) / ".cache"),
        "XDG_CURRENT_DESKTOP": os.environ.get("XDG_CURRENT_DESKTOP") or "XFCE",
    }
    if display:
        env["DISPLAY"] = display
    xauthority = os.environ.get("A0_DESKTOP_XAUTHORITY") or str(Path(profile_dir) / ".Xauthority")
    if Path(xauthority).exists():
        env["XAUTHORITY"] = xauthority
    return env


def collect_capabilities() -> dict[str, str]:
    return {
        name: shutil.which(name) or ""
        for name in (
            "xdotool",
            "xrandr",
            "xwininfo",
            "xprop",
            "xwd",
            "xclip",
        )
    }


def collect_display_size(env: dict[str, str], capabilities: dict[str, str], errors: list[str]) -> dict[str, int]:
    if not capabilities.get("xrandr"):
        return {"width": 0, "height": 0}
    result = run([capabilities["xrandr"], "-q"], env=env, timeout=4)
    if result.returncode != 0:
        errors.append(command_output(result) or "xrandr could not read the Desktop display.")
        return {"width": 0, "height": 0}
    match = re.search(r"\bcurrent\s+(\d+)\s+x\s+(\d+)", result.stdout)
    if not match:
        errors.append("xrandr output did not include the current Desktop size.")
        return {"width": 0, "height": 0}
    return {"width": int(match.group(1)), "height": int(match.group(2))}


def collect_pointer(env: dict[str, str], capabilities: dict[str, str], errors: list[str]) -> dict[str, int]:
    if not capabilities.get("xdotool"):
        return {"x": 0, "y": 0, "screen": 0, "window": 0}
    result = run([capabilities["xdotool"], "getmouselocation", "--shell"], env=env, timeout=3)
    if result.returncode != 0:
        errors.append(command_output(result) or "xdotool could not read the pointer location.")
        return {"x": 0, "y": 0, "screen": 0, "window": 0}
    values = parse_shell_values(result.stdout)
    return {
        "x": int_value(values.get("X")),
        "y": int_value(values.get("Y")),
        "screen": int_value(values.get("SCREEN")),
        "window": int_value(values.get("WINDOW")),
    }


def collect_active_window(env: dict[str, str], capabilities: dict[str, str], errors: list[str]) -> dict[str, Any] | None:
    if not capabilities.get("xdotool"):
        return None
    result = run([capabilities["xdotool"], "getactivewindow"], env=env, timeout=3)
    if result.returncode != 0:
        return None
    window_id = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not window_id:
        return None
    return collect_window(env, capabilities, window_id, errors)


def collect_windows(env: dict[str, str], capabilities: dict[str, str], errors: list[str]) -> list[dict[str, Any]]:
    if not capabilities.get("xdotool"):
        return []
    result = run([capabilities["xdotool"], "search", "--onlyvisible", "--name", "."], env=env, timeout=4)
    if result.returncode != 0:
        detail = command_output(result)
        if detail:
            errors.append(detail)
        return []
    windows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for window_id in result.stdout.splitlines():
        window_id = window_id.strip()
        if not window_id or window_id in seen:
            continue
        seen.add(window_id)
        windows.append(collect_window(env, capabilities, window_id, errors))
    return windows


def collect_window(
    env: dict[str, str],
    capabilities: dict[str, str],
    window_id: str,
    errors: list[str],
) -> dict[str, Any]:
    props = collect_window_props(env, capabilities, window_id)
    geometry = collect_window_geometry(env, capabilities, window_id)
    return {
        "id": str(window_id),
        "title": props.get("title", ""),
        "class": props.get("class", ""),
        "name": props.get("name", ""),
        "pid": int_value(props.get("pid")),
        "geometry": geometry,
    }


def collect_window_geometry(env: dict[str, str], capabilities: dict[str, str], window_id: str) -> dict[str, int]:
    geometry = {"x": 0, "y": 0, "width": 0, "height": 0}
    if not capabilities.get("xwininfo"):
        return geometry
    result = run([capabilities["xwininfo"], "-id", str(window_id)], env=env, timeout=3)
    if result.returncode != 0:
        return geometry
    patterns = {
        "x": r"Absolute upper-left X:\s*(-?\d+)",
        "y": r"Absolute upper-left Y:\s*(-?\d+)",
        "width": r"Width:\s*(\d+)",
        "height": r"Height:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, result.stdout)
        if match:
            geometry[key] = int(match.group(1))
    return geometry


def collect_window_props(env: dict[str, str], capabilities: dict[str, str], window_id: str) -> dict[str, str]:
    props = {"title": "", "class": "", "name": "", "pid": ""}
    xdotool = capabilities.get("xdotool")
    if xdotool:
        result = run([xdotool, "getwindowname", str(window_id)], env=env, timeout=3)
        if result.returncode == 0:
            props["title"] = result.stdout.strip()
    xprop = capabilities.get("xprop")
    if not xprop:
        return props
    result = run([xprop, "-id", str(window_id), "WM_CLASS", "WM_NAME", "_NET_WM_NAME", "_NET_WM_PID"], env=env, timeout=3)
    if result.returncode != 0:
        return props
    parsed = parse_xprop(result.stdout)
    title = parsed.get("_NET_WM_NAME") or parsed.get("WM_NAME") or props["title"]
    props["title"] = title
    props["class"] = parsed.get("WM_CLASS_CLASS", "")
    props["name"] = parsed.get("WM_CLASS_NAME", "")
    props["pid"] = parsed.get("_NET_WM_PID", "")
    return props


def parse_xprop(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip().split("(", 1)[0]
        raw_value = raw_value.strip()
        quoted = re.findall(r'"([^"]*)"', raw_value)
        if key == "WM_CLASS" and quoted:
            values["WM_CLASS_NAME"] = quoted[0]
            values["WM_CLASS_CLASS"] = quoted[-1]
            continue
        if quoted:
            values[key] = quoted[-1]
            continue
        match = re.search(r"-?\d+", raw_value)
        values[key] = match.group(0) if match else raw_value
    return values


def latest_screenshot(*, context_id: str = "") -> dict[str, Any]:
    chat_dir = chat_screenshot_dir(context_id)
    chat_latest = _latest_screenshot_from_dir(
        chat_dir,
        context_id=context_id,
        ephemeral=False,
        chat_scoped=True,
        prune_older=False,
    )
    if chat_latest.get("ok"):
        return chat_latest

    prune_context_screenshots(context_id=context_id, max_age_seconds=RECENT_SCREENSHOT_SECONDS)
    screenshot_dir = context_screenshot_dir(context_id)
    return _latest_screenshot_from_dir(
        screenshot_dir,
        context_id=context_id,
        ephemeral=True,
        chat_scoped=False,
        prune_older=True,
    )


def _latest_screenshot_from_dir(
    screenshot_dir: Path,
    *,
    context_id: str = "",
    ephemeral: bool,
    chat_scoped: bool,
    prune_older: bool,
) -> dict[str, Any]:
    if not screenshot_dir.exists():
        return {"ok": False, "path": "", "format": "", "captured_at": "", "recent": False}
    candidates = [
        path
        for path in screenshot_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _SCREENSHOT_SUFFIXES
    ]
    if not candidates:
        return {"ok": False, "path": "", "format": "", "captured_at": "", "recent": False}
    latest = max(candidates, key=lambda item: item.stat().st_mtime)
    if prune_older:
        for candidate in candidates:
            if candidate != latest:
                candidate.unlink(missing_ok=True)
    age = max(0.0, time.time() - latest.stat().st_mtime)
    return {
        "ok": True,
        "path": str(latest),
        "a0_path": normalize_a0_path(latest),
        "format": latest.suffix.lower().lstrip("."),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(latest.stat().st_mtime)),
        "recent": age <= RECENT_SCREENSHOT_SECONDS,
        "ephemeral": ephemeral,
        "chat_scoped": chat_scoped,
        "context_id": _safe_context_id(context_id),
    }


def stable_state(
    *,
    display: str,
    profile_dir: str,
    context_id: str = "",
    size: dict[str, int] | None = None,
    pointer: dict[str, int] | None = None,
    active_window: dict[str, Any] | None = None,
    windows: list[dict[str, Any]] | None = None,
    screenshot: dict[str, Any] | None = None,
    capabilities: dict[str, str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    clean_errors = [str(error) for error in errors or [] if str(error)]
    return {
        "ok": not clean_errors,
        "context_id": _safe_context_id(context_id),
        "display": display,
        "profile_dir": profile_dir,
        "size": size or {"width": 0, "height": 0},
        "pointer": pointer or {"x": 0, "y": 0, "screen": 0, "window": 0},
        "active_window": active_window,
        "windows": windows or [],
        "screenshot": screenshot or {"ok": False, "path": "", "format": "", "captured_at": "", "recent": False},
        "capabilities": capabilities or collect_capabilities(),
        "errors": clean_errors,
    }


def compact_prompt_context(state: dict[str, Any] | None = None) -> str:
    state = state if state is not None else collect_state(include_screenshot=False)
    if not state.get("display"):
        return ""
    lines = ["[DESKTOP STATE]"]
    size = state.get("size") or {}
    pointer = state.get("pointer") or {}
    lines.append(
        f"- display={state.get('display', '')} size={size.get('width', 0)}x{size.get('height', 0)} "
        f"pointer={pointer.get('x', 0)},{pointer.get('y', 0)}"
    )
    active = state.get("active_window") or {}
    if active:
        lines.append(
            f"- active={active.get('title', '') or '<untitled>'} "
            f"class={active.get('class', '') or active.get('name', '')}"
        )
    visible = []
    for window in state.get("windows") or []:
        title = window.get("title") or "<untitled>"
        window_class = window.get("class") or window.get("name") or ""
        visible.append(f"{title} ({window_class})" if window_class else title)
        if len(visible) >= 5:
            break
    if visible:
        lines.append("- visible=" + "; ".join(visible))
    screenshot = state.get("screenshot") or {}
    if screenshot.get("recent") and screenshot.get("path"):
        ephemeral = " ephemeral" if screenshot.get("ephemeral") else ""
        screenshot_ref = screenshot.get("a0_path") or screenshot["path"]
        lines.append(f"- recent_screenshot={screenshot_ref}{ephemeral}")
    context_id = str(state.get("context_id") or "").strip()
    if context_id:
        lines.append(f"- screenshot_context={context_id}")
    context_arg = f" --context-id {context_id}" if context_id else ""
    lines.append(
        "- next=plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh state --json"
        f"{context_arg} for structured checks; use observe --json --screenshot"
        f"{context_arg} "
        "before coordinate or visual-OCR actions; prefer sequence/focus/key/paste/save/app-native helpers first."
    )
    lines.append(
        "- verify=for terminal/CLI-agent output, use the screenshot path from a fresh final "
        "observe --json --screenshot captured after the response appears."
    )
    if state.get("errors"):
        lines.append("- errors=" + "; ".join(str(item) for item in state["errors"][:2]))
    return "\n".join(lines)


def parse_shell_values(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def run(command: list[str], *, env: dict[str, str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return subprocess.CompletedProcess(command, 124, stdout, stderr or "command timed out")


def command_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or "").strip()


def image_width(path: Path) -> int:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width)
    except Exception:
        return 0


def image_height(path: Path) -> int:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.height)
    except Exception:
        return 0


def ephemeral_screenshot_result(
    path: Path,
    *,
    context_id: str = "",
    image_format: str = "png",
    width: int = 0,
    height: int = 0,
) -> dict[str, Any]:
    from helpers import ephemeral_images

    mime = "image/jpeg" if image_format.lower() in {"jpg", "jpeg"} else "image/png"
    safe_context = _safe_context_id(context_id)
    ref = ephemeral_images.put_image_bytes(
        context_id=str(context_id or "").strip(),
        mime=mime,
        payload=path.read_bytes(),
        name=path.name,
    )
    path.unlink(missing_ok=True)
    prune_context_screenshots(context_id=context_id)
    return {
        "ok": True,
        "path": "",
        "format": image_format,
        "mime": mime,
        "width": width,
        "height": height,
        "captured_at": iso_now(),
        "recent": True,
        "ephemeral": True,
        "ephemeral_ref": ref,
        "context_id": safe_context,
        "vision_load": {
            "tool_name": "vision_load",
            "tool_args": {"paths": [ref]},
        },
        "error": "",
    }


def prune_context_screenshots(
    *,
    context_id: str = "",
    keep_path: Path | None = None,
    max_age_seconds: float | None = None,
) -> None:
    screenshot_dir = context_screenshot_dir(context_id)
    if not screenshot_dir.exists():
        return
    keep = keep_path.resolve(strict=False) if keep_path else None
    now = time.time()
    for candidate in screenshot_dir.iterdir():
        if not candidate.is_file() or candidate.suffix.lower() not in _SCREENSHOT_SUFFIXES:
            continue
        if keep is not None and candidate.resolve(strict=False) == keep:
            continue
        if max_age_seconds is not None:
            try:
                if now - candidate.stat().st_mtime <= max_age_seconds:
                    continue
            except OSError:
                pass
        candidate.unlink(missing_ok=True)
    try:
        screenshot_dir.rmdir()
    except OSError:
        pass


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observe the Agent Zero persistent Linux Desktop state.")
    subparsers = parser.add_subparsers(dest="command")

    state_parser = subparsers.add_parser("state")
    state_parser.add_argument("--json", action="store_true")
    state_parser.add_argument("--screenshot", action="store_true")
    state_parser.add_argument("--context-id", default="")

    observe_parser = subparsers.add_parser("observe")
    observe_parser.add_argument("--json", action="store_true")
    observe_parser.add_argument("--screenshot", action="store_true")
    observe_parser.add_argument("--context-id", default="")

    screenshot_parser = subparsers.add_parser("screenshot")
    screenshot_parser.add_argument("path", nargs="?")
    screenshot_parser.add_argument("--json", action="store_true")
    screenshot_parser.add_argument("--context-id", default="")

    args = parser.parse_args(argv)
    command = args.command or "state"
    if command in {"state", "observe"}:
        payload = collect_state(
            include_screenshot=bool(args.screenshot),
            context_id=str(args.context_id or ""),
            screenshot_transport="path",
        )
        print(json.dumps(payload, sort_keys=True))
        return 0 if payload.get("ok") else 1

    if command == "screenshot":
        errors: list[str] = []
        env_info = resolve_environment(errors=errors)
        payload = capture_screenshot(
            display_env(display=env_info["display"], profile_dir=env_info["profile_dir"]),
            collect_capabilities(),
            path=args.path,
            errors=errors,
            context_id=str(args.context_id or ""),
            transport="path",
        )
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(payload.get("path") or payload.get("error") or "")
        return 0 if payload.get("ok") else 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
