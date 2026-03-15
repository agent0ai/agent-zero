"""Tests for python/api/tunnel.py — Tunnel API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.tunnel import Tunnel, process, stop


def _make_handler(app=None, lock=None):
    return Tunnel(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestTunnelProcess:
    @pytest.mark.asyncio
    async def test_health_action_returns_success(self):
        result = await process({"action": "health"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_action_returns_tunnel_status(self):
        mock_manager = MagicMock()
        mock_manager.get_tunnel_url.return_value = "https://abc.serveo.net"
        mock_manager.is_running = True
        with patch("python.api.tunnel.TunnelManager.get_instance", return_value=mock_manager):
            result = await process({"action": "get"})
        assert result["success"] is True
        assert result["tunnel_url"] == "https://abc.serveo.net"
        assert result["is_running"] is True

    @pytest.mark.asyncio
    async def test_create_action_starts_tunnel(self):
        mock_manager = MagicMock()
        mock_manager.start_tunnel.return_value = "https://abc.serveo.net"
        mock_manager.get_last_error.return_value = None
        mock_manager.get_notifications.return_value = []
        with patch("python.api.tunnel.TunnelManager.get_instance", return_value=mock_manager), \
             patch("python.api.tunnel.runtime.get_web_ui_port", return_value=5000):
            result = await process({"action": "create", "provider": "serveo"})
        assert result["success"] is True
        assert result["tunnel_url"] == "https://abc.serveo.net"

    @pytest.mark.asyncio
    async def test_create_action_returns_error_when_failed(self):
        mock_manager = MagicMock()
        mock_manager.start_tunnel.return_value = None
        mock_manager.get_last_error.return_value = "Connection failed"
        mock_manager.get_notifications.return_value = []
        with patch("python.api.tunnel.TunnelManager.get_instance", return_value=mock_manager), \
             patch("python.api.tunnel.runtime.get_web_ui_port", return_value=5000):
            result = await process({"action": "create"})
        assert result["success"] is False
        assert "Connection failed" in result["message"]

    def test_stop_action_stops_tunnel(self):
        mock_manager = MagicMock()
        with patch("python.api.tunnel.TunnelManager.get_instance", return_value=mock_manager):
            result = stop()
        assert result["success"] is True
        mock_manager.stop_tunnel.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        result = await process({"action": "invalid"})
        assert result["success"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_default_action_is_get(self):
        mock_manager = MagicMock()
        mock_manager.get_tunnel_url.return_value = None
        mock_manager.is_running = False
        with patch("python.api.tunnel.TunnelManager.get_instance", return_value=mock_manager):
            result = await process({})
        assert result["success"] is False
        assert "tunnel_url" in result


class TestTunnelHandler:
    @pytest.mark.asyncio
    async def test_handler_delegates_to_process(self):
        handler = _make_handler()
        with patch("python.api.tunnel.process", new_callable=AsyncMock, return_value={"success": True}):
            result = await handler.process({"action": "health"}, MagicMock())
        assert result["success"] is True
