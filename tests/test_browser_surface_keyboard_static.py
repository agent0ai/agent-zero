from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vnc_viewer_exposes_keyboard_input():
    vnc = (ROOT / "plugins/_browser/webui/vnc.js").read_text()
    assert "sendKeyboardInput" in vnc
    assert "keysymdef" in vnc
    for name in ("Backspace", "Enter", "ArrowUp", "Page_Down"):
        assert name in vnc


def test_store_prefers_vnc_session_before_viewer_input_fallback():
    store = (ROOT / "plugins/_browser/webui/browser-store.js").read_text()
    start = store.index("async sendSurfaceKeyboardInput")
    body = store[start:start + 900]
    assert "a0BrowserViewer" in body
    assert body.index("sendKeyboardInput") < body.index("browser_viewer_input")


def test_dox_documents_vnc_delivery_and_fallback():
    dox = (ROOT / "plugins/_browser/AGENTS.md").read_text()
    assert "interactive VNC session" in dox
    assert "viewer-input event" in dox
