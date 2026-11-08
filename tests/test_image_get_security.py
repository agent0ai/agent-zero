import asyncio
import sys
import threading
from pathlib import Path

import pytest
from flask import Flask, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import image_get


def _patch_base_dir(monkeypatch, base_dir: Path, *, development: bool = False) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)

    def fake_get_abs_path(*parts: str) -> str:
        if len(parts) == 1 and Path(str(parts[0])).is_absolute():
            return str(Path(str(parts[0])))
        return str(base_dir.joinpath(*(str(part) for part in parts)))

    monkeypatch.setattr(image_get.files, "get_base_dir", lambda: str(base_dir))
    monkeypatch.setattr(image_get.files, "get_abs_path", fake_get_abs_path)
    monkeypatch.setattr(image_get.runtime, "is_development", lambda: development)


async def _request_image(path: str):
    app = Flask("test_image_get_security")
    handler = image_get.ImageGet(app, threading.Lock())
    with app.test_request_context("/api/image_get"):
        return await handler.process({"path": path}, request)


def test_image_get_serves_images_inside_base_dir(tmp_path, monkeypatch):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir)
    image_path = base_dir / "usr" / "uploads" / "safe.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    response = asyncio.run(_request_image(str(image_path)))

    assert response.status_code == 200
    assert response.headers["X-File-Type"] == "image"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("development", [False, True])
def test_image_get_blocks_image_paths_outside_base_dir(tmp_path, monkeypatch, development):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir, development=development)
    outside_image = tmp_path / "outside.png"
    outside_image.write_bytes(b"outside")

    response = asyncio.run(_request_image(str(outside_image)))

    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Path is outside of allowed directory"


@pytest.mark.parametrize("development", [False, True])
def test_image_get_blocks_symlink_escape_from_base_dir(tmp_path, monkeypatch, development):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir, development=development)
    outside_image = tmp_path / "secret.png"
    outside_image.write_bytes(b"secret")
    link_path = base_dir / "usr" / "uploads" / "linked.png"
    link_path.parent.mkdir(parents=True)
    link_path.symlink_to(outside_image)

    response = asyncio.run(_request_image(str(link_path)))

    assert response.status_code == 403


@pytest.mark.parametrize("development", [False, True])
def test_image_get_hardens_svg_responses(tmp_path, monkeypatch, development):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir, development=development)
    svg_path = base_dir / "usr" / "uploads" / "payload.svg"
    svg_path.parent.mkdir(parents=True)
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        encoding="utf-8",
    )

    response = asyncio.run(_request_image(str(svg_path)))

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"].startswith("sandbox;")
    assert "script-src 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_image_get_development_serves_local_a0_path(tmp_path, monkeypatch):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir, development=True)
    image_path = base_dir / "usr" / "uploads" / "local.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"local image")

    def no_dispatch(*args, **kwargs):
        raise AssertionError("Images must be read locally")

    monkeypatch.setattr(image_get.runtime, "call_development_function", no_dispatch)
    response = asyncio.run(_request_image("/a0/usr/uploads/local.png"))
    try:
        assert response.status_code == 200
        assert b"".join(response.response) == b"local image"
    finally:
        response.close()


def test_image_get_development_missing_file_uses_icon_without_rfc(tmp_path, monkeypatch):
    base_dir = tmp_path / "a0"
    _patch_base_dir(monkeypatch, base_dir, development=True)

    def no_dispatch(*args, **kwargs):
        raise AssertionError("Missing images must not trigger RFC")

    monkeypatch.setattr(image_get.runtime, "call_development_function", no_dispatch)
    monkeypatch.setattr(
        image_get,
        "_send_fallback_icon",
        lambda _icon_name: image_get.Response("fallback", status=200),
    )
    response = asyncio.run(_request_image("/a0/usr/uploads/missing.png"))
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "fallback"
