"""Tests for python/api/mcp_servers_status.py — McpServersStatuss API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.mcp_servers_status import McpServersStatuss


def _make_handler(app=None, lock=None):
    return McpServersStatuss(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMcpServersStatus:
    @pytest.mark.asyncio
    async def test_process_returns_success_with_status(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_status = [{"name": "server1", "status": "running"}]

        with patch("python.api.mcp_servers_status.MCPConfig") as MockMCP:
            mock_instance = MagicMock()
            mock_instance.get_servers_status.return_value = mock_status
            MockMCP.get_instance.return_value = mock_instance

            result = await handler.process({}, MagicMock())

        assert result["success"] is True
        assert result["status"] == mock_status
