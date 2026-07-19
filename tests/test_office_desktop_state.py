from __future__ import annotations

import subprocess
import struct
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import virtual_desktop
from plugins._desktop.helpers import desktop_state


def _completed(command, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def test_desktop_state_collects_x11_state_from_mocked_tools(tmp_path, monkeypatch):
    session_dir = tmp_path / "sessions"
    profile_dir = tmp_path / "profiles" / desktop_state.SESSION_ID
    session_dir.mkdir(parents=True)
    profile_dir.mkdir(parents=True)
    (session_dir / f"{desktop_state.SESSION_ID}.json").write_text(
        '{"display": 120, "profile_dir": "%s"}' % profile_dir,
        encoding="utf-8",
    )

    monkeypatch.setattr(desktop_state, "SESSION_DIR", session_dir)
    monkeypatch.setattr(desktop_state, "PROFILE_DIR", tmp_path / "profiles")
    monkeypatch.setattr(desktop_state, "SCREENSHOT_DIR", tmp_path / "screenshots")
    monkeypatch.setattr(
        desktop_state.shutil,
        "which",
        lambda name: f"/usr/bin/{name}"
        if name in {"xdotool", "xrandr", "xwininfo", "xprop", "xwd", "xclip"}
        else "",
    )

    def fake_run(command, **kwargs):
        name = Path(command[0]).name
        if name == "xrandr":
            return _completed(command, stdout="Screen 0: current 1440 x 900, maximum 1920 x 1080\n")
        if name == "xdotool" and command[1:3] == ["getmouselocation", "--shell"]:
            return _completed(command, stdout="X=12\nY=34\nSCREEN=0\nWINDOW=111\n")
        if name == "xdotool" and command[1] == "getactivewindow":
            return _completed(command, stdout="111\n")
        if name == "xdotool" and command[1] == "search":
            return _completed(command, stdout="111\n222\n")
        if name == "xdotool" and command[1] == "getwindowname":
            return _completed(command, stdout={"111": "LibreOffice Calc", "222": "Terminal"}[command[2]] + "\n")
        if name == "xwininfo":
            geometry = {
                "111": (5, 7, 800, 600),
                "222": (20, 30, 640, 480),
            }[command[2]]
            return _completed(
                command,
                stdout=(
                    f"  Absolute upper-left X:  {geometry[0]}\n"
                    f"  Absolute upper-left Y:  {geometry[1]}\n"
                    f"  Width: {geometry[2]}\n"
                    f"  Height: {geometry[3]}\n"
                ),
            )
        if name == "xprop":
            window_id = command[2]
            if window_id == "111":
                return _completed(
                    command,
                    stdout='WM_CLASS(STRING) = "libreoffice", "libreoffice-calc"\n_NET_WM_PID(CARDINAL) = 4242\n',
                )
            return _completed(
                command,
                stdout='WM_CLASS(STRING) = "xfce4-terminal", "Xfce4-terminal"\n_NET_WM_PID(CARDINAL) = 4343\n',
            )
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(desktop_state.subprocess, "run", fake_run)

    state = desktop_state.collect_state()

    assert state["ok"] is True
    assert state["display"] == ":120"
    assert state["profile_dir"] == str(profile_dir)
    assert state["size"] == {"width": 1440, "height": 900}
    assert state["pointer"]["x"] == 12
    assert state["active_window"]["title"] == "LibreOffice Calc"
    assert state["active_window"]["class"] == "libreoffice-calc"
    assert state["active_window"]["geometry"]["width"] == 800
    assert [window["title"] for window in state["windows"]] == ["LibreOffice Calc", "Terminal"]


def test_desktop_state_allows_missing_active_window_when_display_is_reachable(tmp_path, monkeypatch):
    session_dir = tmp_path / "sessions"
    profile_dir = tmp_path / "profiles" / desktop_state.SESSION_ID
    session_dir.mkdir(parents=True)
    profile_dir.mkdir(parents=True)
    (session_dir / f"{desktop_state.SESSION_ID}.json").write_text(
        '{"display": 120, "profile_dir": "%s"}' % profile_dir,
        encoding="utf-8",
    )

    monkeypatch.setattr(desktop_state, "SESSION_DIR", session_dir)
    monkeypatch.setattr(desktop_state, "PROFILE_DIR", tmp_path / "profiles")
    monkeypatch.setattr(desktop_state.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(command, **kwargs):
        del kwargs
        name = Path(command[0]).name
        if name == "xrandr":
            return _completed(command, stdout="Screen 0: current 543 x 792, maximum 1920 x 1080\n")
        if name == "xdotool" and command[1:3] == ["getmouselocation", "--shell"]:
            return _completed(command, stdout="X=43\nY=244\nSCREEN=0\nWINDOW=18874412\n")
        if name == "xdotool" and command[1] == "getactivewindow":
            return _completed(
                command,
                returncode=1,
                stderr="XGetWindowProperty[_NET_ACTIVE_WINDOW] failed (code=1)\n",
            )
        if name == "xdotool" and command[1] == "search":
            return _completed(command, stdout="18874412\n")
        if name == "xdotool" and command[1] == "getwindowname":
            return _completed(command, stdout="Desktop\n")
        if name == "xwininfo":
            return _completed(
                command,
                stdout=(
                    "  Absolute upper-left X:  0\n"
                    "  Absolute upper-left Y:  0\n"
                    "  Width: 543\n"
                    "  Height: 792\n"
                ),
            )
        if name == "xprop":
            return _completed(command, stdout='WM_CLASS(STRING) = "xfdesktop", "Xfdesktop"\n')
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(desktop_state.subprocess, "run", fake_run)

    state = desktop_state.collect_state()

    assert state["ok"] is True
    assert state["active_window"] is None
    assert state["errors"] == []
    assert [window["title"] for window in state["windows"]] == ["Desktop"]


def test_desktop_state_screenshot_capture_uses_xwd_and_pillow_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop_state, "SCREENSHOT_DIR", tmp_path)
    capabilities = {"xwd": "/usr/bin/xwd"}
    env = {"DISPLAY": ":120"}

    def fake_run(command, *, env, timeout):
        raw_path = Path(command[command.index("-out") + 1])
        raw_path.write_bytes(b"xwd")
        return _completed(command)

    image_module = types.ModuleType("PIL.Image")

    class FakeImage:
        width = 320
        height = 240

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def save(self, target):
            Path(target).write_bytes(b"png")

    image_module.open = lambda _path: FakeImage()
    pil_module = types.ModuleType("PIL")
    pil_module.Image = image_module

    monkeypatch.setattr(desktop_state, "run", fake_run)
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_module)

    screenshot = desktop_state.capture_screenshot(env, capabilities, path=tmp_path / "shot.png", errors=[])

    assert screenshot["ok"] is True
    assert screenshot["path"] == str(tmp_path / "shot.png")
    assert screenshot["format"] == "png"
    assert screenshot["ephemeral"] is False
    assert (tmp_path / "shot.png").read_bytes() == b"png"
    assert not (tmp_path / "shot.xwd").exists()


def test_desktop_state_shell_screenshot_path_is_context_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop_state, "BASE_DIR", tmp_path)
    monkeypatch.setattr(desktop_state, "SCREENSHOT_DIR", tmp_path / "tmp" / "desktop" / "screenshots")
    capabilities = {"xwd": "/usr/bin/xwd"}
    env = {"DISPLAY": ":120"}

    def fake_run(command, *, env, timeout):
        raw_path = Path(command[command.index("-out") + 1])
        raw_path.write_bytes(b"xwd")
        return _completed(command)

    image_module = types.ModuleType("PIL.Image")

    class FakeImage:
        width = 320
        height = 240

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def save(self, target):
            Path(target).write_bytes(b"png")

    image_module.open = lambda _path: FakeImage()
    pil_module = types.ModuleType("PIL")
    pil_module.Image = image_module

    monkeypatch.setattr(desktop_state, "run", fake_run)
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_module)
    stale_path = tmp_path / "tmp" / "desktop" / "screenshots" / "ctx_id" / "stale.png"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_bytes(b"stale")

    screenshot = desktop_state.capture_screenshot(
        env,
        capabilities,
        errors=[],
        context_id="ctx/id",
        transport="path",
    )

    path = Path(screenshot["path"])
    assert screenshot["ok"] is True
    assert screenshot["ephemeral"] is False
    assert screenshot["chat_scoped"] is True
    assert screenshot["context_id"] == "ctx_id"
    assert screenshot["a0_path"].startswith("/a0/usr/chats/ctx_id/screenshots/desktop/desktop-")
    assert path.parent == tmp_path / "usr" / "chats" / "ctx_id" / "screenshots" / "desktop"
    assert path.name.startswith("desktop-")
    assert desktop_state.latest_screenshot(context_id="ctx/id")["path"] == str(path)
    assert stale_path.exists()


def test_desktop_state_default_screenshot_returns_ephemeral_ref(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop_state, "SCREENSHOT_DIR", tmp_path)
    capabilities = {"xwd": "/usr/bin/xwd"}
    env = {"DISPLAY": ":120"}

    def fake_run(command, *, env, timeout):
        raw_path = Path(command[command.index("-out") + 1])
        raw_path.write_bytes(b"xwd")
        return _completed(command)

    image_module = types.ModuleType("PIL.Image")

    class FakeImage:
        width = 320
        height = 240

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def save(self, target):
            Path(target).write_bytes(b"png")

    image_module.open = lambda _path: FakeImage()
    pil_module = types.ModuleType("PIL")
    pil_module.Image = image_module

    monkeypatch.setattr(desktop_state, "run", fake_run)
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_module)

    screenshot = desktop_state.capture_screenshot(
        env,
        capabilities,
        errors=[],
        context_id="ctx/id",
    )

    assert screenshot["ok"] is True
    assert screenshot["path"] == ""
    assert screenshot["ephemeral"] is True
    assert screenshot["ephemeral_ref"].startswith("a0-ephemeral-image://")
    assert screenshot["vision_load"]["tool_args"]["paths"] == [screenshot["ephemeral_ref"]]
    assert screenshot["context_id"] == "ctx_id"
    assert not (tmp_path / "ctx_id").exists()


def test_desktop_prompt_context_recommends_structured_state_before_screenshots():
    context = desktop_state.compact_prompt_context(
        {
            "display": ":120",
            "size": {"width": 1280, "height": 720},
            "pointer": {"x": 10, "y": 20},
            "active_window": {"title": "Terminal", "class": "Xfce4-terminal"},
            "windows": [{"title": "Terminal", "class": "Xfce4-terminal"}],
            "screenshot": {},
            "context_id": "ctx_id",
            "errors": [],
        }
    )

    assert "state --json --context-id ctx_id for structured checks" in context
    assert "observe --json --screenshot --context-id ctx_id before coordinate or visual-OCR actions" in context
    assert "before any coordinate action" not in context


def test_virtual_desktop_system_display_normalization_rejects_portrait_viewports():
    assert virtual_desktop.normalize_desktop_display_size(395, 1080) == (
        virtual_desktop.DEFAULT_WIDTH,
        virtual_desktop.DEFAULT_HEIGHT,
    )
    assert virtual_desktop.normalize_desktop_display_size(1600, 900) == (1600, 900)


@pytest.mark.parametrize(
    ("byte_order", "pixel_bytes"),
    (
        (0, bytes.fromhex("0000ff00") + bytes.fromhex("00ff0000")),
        (1, bytes.fromhex("00ff0000") + bytes.fromhex("0000ff00")),
    ),
)
def test_xwd_fallback_parser_handles_truecolor_pixels(tmp_path, byte_order, pixel_bytes):
    from PIL import Image

    raw_path = tmp_path / "shot.xwd"
    target = tmp_path / "shot.png"
    header_values = [
        100,  # header_size
        7,  # file_version
        2,  # pixmap_format
        24,  # pixmap_depth
        2,  # pixmap_width
        1,  # pixmap_height
        0,  # xoffset
        byte_order,
        32,  # bitmap_unit
        1,  # bitmap_bit_order
        32,  # bitmap_pad
        32,  # bits_per_pixel
        8,  # bytes_per_line
        4,  # visual_class: TrueColor
        0x00FF0000,  # red_mask
        0x0000FF00,  # green_mask
        0x000000FF,  # blue_mask
        8,  # bits_per_rgb
        256,  # colormap_entries
        0,  # ncolors
        2,  # window_width
        1,  # window_height
        0,  # window_x
        0,  # window_y
        0,  # window_bdrwidth
    ]
    raw_path.write_bytes(struct.pack(">25I", *header_values) + pixel_bytes)

    converted = desktop_state.convert_xwd_to_image(raw_path, target)

    assert converted == {"width": 2, "height": 1}
    with Image.open(target) as image:
        assert image.mode == "RGB"
        assert image.size == (2, 1)
        assert list(image.getdata()) == [(255, 0, 0), (0, 255, 0)]
