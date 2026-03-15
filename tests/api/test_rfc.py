"""Tests for python/api/rfc.py — RFC API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.rfc import RFC


def _make_handler(app=None, lock=None):
    return RFC(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestRFC:
    def test_requires_csrf_returns_false(self):
        assert RFC.requires_csrf() is False

    def test_requires_auth_returns_false(self):
        assert RFC.requires_auth() is False

    @pytest.mark.asyncio
    async def test_process_delegates_to_runtime_handle_rfc(self):
        handler = _make_handler()
        mock_result = {"success": True, "data": "rfc result"}
        with patch("python.api.rfc.runtime.handle_rfc", new_callable=AsyncMock, return_value=mock_result):
            result = await handler.process({"action": "get"}, MagicMock())
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_process_passes_input_to_handle_rfc(self):
        handler = _make_handler()
        input_data = {"action": "set", "key": "value"}
        with patch("python.api.rfc.runtime.handle_rfc", new_callable=AsyncMock) as mock_handle:
            await handler.process(input_data, MagicMock())
        mock_handle.assert_called_once_with(input_data)
