"""Tests for python/api/mcp_servers_apply.py — McpServersApply API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.mcp_servers_apply import McpServersApply


def _make_handler(app=None, lock=None):
    return McpServersApply(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMcpServersApply:
    @pytest.mark.asyncio
    async def test_process_returns_success_with_status(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_status = [{"name": "server1", "status": "running"}]

        with patch(
            "python.api.mcp_servers_apply.set_settings_delta",
        ), patch(
            "python.api.mcp_servers_apply.asyncio.sleep",
            new_callable=AsyncMock,
        ), patch(
            "python.api.mcp_servers_apply.MCPConfig"
        ) as MockMCP:
            mock_instance = MagicMock()
            mock_instance.get_servers_status.return_value = mock_status
            MockMCP.get_instance.return_value = mock_instance

            result = await handler.process(
                {"mcp_servers": '[{"name":"s1"}]'}, MagicMock()
            )

        assert result["success"] is True
        assert result["status"] == mock_status

    @pytest.mark.asyncio
    async def test_process_returns_false_on_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.mcp_servers_apply.set_settings_delta",
            side_effect=Exception("Settings error"),
        ):
            result = await handler.process(
                {"mcp_servers": "[]"}, MagicMock()
            )

        assert result["success"] is False
        assert "Settings error" in result["error"]
