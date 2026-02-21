import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_socketio_engine_configuration_defaults():
    source = (PROJECT_ROOT / "run_ui.py").read_text(encoding="utf-8")

    assert re.search(r"ping_interval\s*=\s*25\b", source)
    assert re.search(r"ping_timeout\s*=\s*120\b", source)
    assert re.search(r"max_http_buffer_size\s*=\s*50\s*\*\s*1024\s*\*\s*1024", source)


def test_websocket_client_keepalive_matches_server_timeout():
    source = (PROJECT_ROOT / "webui" / "js" / "websocket.js").read_text(encoding="utf-8")

    assert re.search(r"pingInterval:\s*25000\b", source)
    assert re.search(r"pingTimeout:\s*120000\b", source)
