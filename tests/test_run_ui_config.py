import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.ui_server import UiServerRuntime


def test_socketio_engine_configuration_defaults():
    server = UiServerRuntime.create().socketio_server.eio

    assert server.ping_interval == 45
    assert server.ping_timeout == 120
    assert server.max_http_buffer_size == 50 * 1024 * 1024


def test_socketio_engine_configuration_uses_env_overrides(monkeypatch):
    monkeypatch.setenv("A0_SOCKETIO_PING_INTERVAL_SECONDS", "30")
    monkeypatch.setenv("A0_SOCKETIO_PING_TIMEOUT_SECONDS", "90")

    server = UiServerRuntime.create().socketio_server.eio

    assert server.ping_interval == 30
    assert server.ping_timeout == 90
    assert server.max_http_buffer_size == 50 * 1024 * 1024
