import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_index_registers_root_scoped_service_worker():
    index_html = read_text("webui/index.html")

    assert 'rel="manifest" href="/js/manifest.json"' in index_html
    assert "navigator.serviceWorker.register('/sw.js', { scope: '/' })" in index_html


def test_login_page_exposes_same_pwa_metadata():
    login_html = read_text("webui/login.html")

    assert 'rel="manifest" href="/js/manifest.json"' in login_html
    assert "navigator.serviceWorker.register('/sw.js', { scope: '/' })" in login_html


def test_manifest_includes_installable_png_icons():
    manifest = json.loads(read_text("webui/js/manifest.json"))
    icons = {(icon["src"], icon["sizes"], icon["type"]) for icon in manifest["icons"]}

    assert manifest["id"] == "/"
    assert manifest["scope"] == "/"
    assert ("/public/icon-192.png", "192x192", "image/png") in icons
    assert ("/public/icon-512.png", "512x512", "image/png") in icons


def test_service_worker_files_exist_and_are_non_empty():
    root_sw = PROJECT_ROOT / "webui/sw.js"
    legacy_sw = PROJECT_ROOT / "webui/js/sw.js"

    assert root_sw.stat().st_size > 0
    assert legacy_sw.stat().st_size > 0
    assert 'self.addEventListener("fetch"' in root_sw.read_text(encoding="utf-8")
