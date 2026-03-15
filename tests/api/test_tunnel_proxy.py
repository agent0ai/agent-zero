"""Tests for python/api/tunnel_proxy.py — TunnelProxy API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.tunnel_proxy import TunnelProxy, process


def _make_handler(app=None, lock=None):
    return TunnelProxy(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestTunnelProxyProcess:
    @pytest.mark.asyncio
    async def test_forwards_to_local_process_when_service_fails(self):
        with patch("python.api.tunnel_proxy.requests.post", side_effect=Exception("Connection refused")), \
             patch("python.api.tunnel.process", new_callable=AsyncMock, return_value={"success": True}):
            result = await process({"action": "health"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_forwards_to_tunnel_service_when_ok(self):
        health_resp = MagicMock()
        health_resp.status_code = 200
        data_resp = MagicMock()
        data_resp.json.return_value = {"success": True, "tunnel_url": "https://x.serveo.net"}
        with patch("python.api.tunnel_proxy.requests.post", side_effect=[health_resp, data_resp]):
            result = await process({"action": "get"})
        assert result["success"] is True
        assert result["tunnel_url"] == "https://x.serveo.net"

    @pytest.mark.asyncio
    async def test_returns_error_on_json_decode_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("Invalid JSON")
        with patch("python.api.tunnel_proxy.requests.post", return_value=mock_response):
            result = await process({"action": "get"})
        assert "error" in result


class TestTunnelProxyHandler:
    @pytest.mark.asyncio
    async def test_handler_delegates_to_process(self):
        handler = _make_handler()
        with patch("python.api.tunnel_proxy.process", new_callable=AsyncMock, return_value={"success": True}):
            result = await handler.process({"action": "health"}, MagicMock())
        assert result["success"] is True
