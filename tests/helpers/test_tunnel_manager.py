"""Tests for python/helpers/tunnel_manager.py — TunnelManager singleton, notifications, start/stop."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.tunnel_manager import TunnelManager


@pytest.fixture(autouse=True)
def reset_tunnel_manager():
    """Reset singleton between tests."""
    with TunnelManager._lock:
        old = TunnelManager._instance
        TunnelManager._instance = None
    yield
    with TunnelManager._lock:
        TunnelManager._instance = old


class TestTunnelManagerSingleton:
    def test_get_instance_returns_singleton(self):
        a = TunnelManager.get_instance()
        b = TunnelManager.get_instance()
        assert a is b

    def test_init_state(self):
        tm = TunnelManager.get_instance()
        assert tm.tunnel is None
        assert tm.tunnel_url is None
        assert tm.is_running is False
        assert tm.provider is None
        assert tm.notifications.maxlen == 50


class TestTunnelManagerNotifications:
    def test_on_notify_appends_notification(self):
        tm = TunnelManager.get_instance()
        mock_data = MagicMock()
        mock_data.event.value = "info"
        mock_data.message = "Tunnel started"
        mock_data.data = {"url": "https://x.example.com"}
        tm._on_notify(mock_data)
        assert len(tm.notifications) == 1
        assert tm.notifications[0]["event"] == "info"
        assert tm.notifications[0]["message"] == "Tunnel started"

    def test_get_notifications_returns_and_clears(self):
        tm = TunnelManager.get_instance()
        tm.notifications.append({"event": "info", "message": "test", "data": None})
        result = tm.get_notifications()
        assert len(result) == 1
        assert result[0]["message"] == "test"
        assert len(tm.notifications) == 0

    def test_get_last_error_returns_recent_error(self):
        tm = TunnelManager.get_instance()
        tm.notifications.append({"event": "info", "message": "ok", "data": None})
        tm.notifications.append({"event": "error", "message": "Connection failed", "data": None})
        assert tm.get_last_error() == "Connection failed"

    def test_get_last_error_returns_none_when_no_error(self):
        tm = TunnelManager.get_instance()
        tm.notifications.clear()
        tm.notifications.append({"event": "info", "message": "ok", "data": None})
        assert tm.get_last_error() is None


class TestTunnelManagerStartStop:
    def test_start_tunnel_returns_existing_url_if_running(self):
        tm = TunnelManager.get_instance()
        tm.is_running = True
        tm.tunnel_url = "https://abc.serveo.net"
        with patch.object(tm, "_ensure_subscribed"):
            result = tm.start_tunnel(port=80, provider="serveo")
        assert result == "https://abc.serveo.net"

    def test_stop_tunnel_returns_false_when_not_running(self):
        tm = TunnelManager.get_instance()
        tm.tunnel = None
        tm.is_running = False
        assert tm.stop_tunnel() is False

    def test_stop_tunnel_stops_and_clears_state(self):
        tm = TunnelManager.get_instance()
        tm.tunnel = MagicMock()
        tm.is_running = True
        tm.tunnel_url = "https://x.example.com"
        tm.provider = "serveo"
        result = tm.stop_tunnel()
        assert result is True
        assert tm.is_running is False
        assert tm.tunnel_url is None
        assert tm.provider is None

    def test_get_tunnel_url_returns_none_when_not_running(self):
        tm = TunnelManager.get_instance()
        tm.is_running = False
        assert tm.get_tunnel_url() is None

    def test_get_tunnel_url_returns_url_when_running(self):
        tm = TunnelManager.get_instance()
        tm.is_running = True
        tm.tunnel_url = "https://xyz.serveo.net"
        assert tm.get_tunnel_url() == "https://xyz.serveo.net"
