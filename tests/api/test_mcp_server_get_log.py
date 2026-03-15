"""Tests for python/api/mcp_server_get_log.py — McpServerGetLog API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.mcp_server_get_log import McpServerGetLog


def _make_handler(app=None, lock=None):
    return McpServerGetLog(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMcpServerGetLog:
    @pytest.mark.asyncio
    async def test_process_returns_error_when_server_name_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({}, MagicMock())

        assert result["success"] is False
        assert result["error"] == "Missing server_name"

    @pytest.mark.asyncio
    async def test_process_returns_log_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_log = ["log line 1", "log line 2"]

        with patch("python.api.mcp_server_get_log.MCPConfig") as MockMCP:
            mock_instance = MagicMock()
            mock_instance.get_server_log.return_value = mock_log
            MockMCP.get_instance.return_value = mock_instance

            result = await handler.process(
                {"server_name": "filesystem"}, MagicMock()
            )

        assert result["success"] is True
        assert result["log"] == mock_log
