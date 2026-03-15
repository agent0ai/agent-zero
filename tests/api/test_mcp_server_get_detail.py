"""Tests for python/api/mcp_server_get_detail.py — McpServerGetDetail API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.mcp_server_get_detail import McpServerGetDetail


def _make_handler(app=None, lock=None):
    return McpServerGetDetail(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMcpServerGetDetail:
    @pytest.mark.asyncio
    async def test_process_returns_error_when_server_name_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({}, MagicMock())

        assert result["success"] is False
        assert result["error"] == "Missing server_name"

    @pytest.mark.asyncio
    async def test_process_returns_detail_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_detail = {"name": "filesystem", "command": "npx", "status": "running"}

        with patch("python.api.mcp_server_get_detail.MCPConfig") as MockMCP:
            mock_instance = MagicMock()
            mock_instance.get_server_detail.return_value = mock_detail
            MockMCP.get_instance.return_value = mock_instance

            result = await handler.process(
                {"server_name": "filesystem"}, MagicMock()
            )

        assert result["success"] is True
        assert result["detail"] == mock_detail
