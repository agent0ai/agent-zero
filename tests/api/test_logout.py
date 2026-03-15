"""Tests for python/api/logout.py — ApiLogout API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.logout import ApiLogout


def _make_handler(app=None, lock=None):
    return ApiLogout(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiLogout:
    def test_requires_auth_returns_false(self):
        assert ApiLogout.requires_auth() is False

    @pytest.mark.asyncio
    async def test_process_clears_session_and_returns_ok(self):
        handler = _make_handler()
        mock_session = MagicMock()
        import python.api.logout as _mod
        _orig = _mod.session
        _mod.session = mock_session
        try:
            result = await handler.process({}, MagicMock())
        finally:
            _mod.session = _orig
        mock_session.clear.assert_called_once()
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_process_pops_keys_on_clear_exception(self):
        handler = _make_handler()
        mock_session = MagicMock()
        mock_session.clear.side_effect = Exception("clear failed")
        import python.api.logout as _mod
        _orig = _mod.session
        _mod.session = mock_session
        try:
            result = await handler.process({}, MagicMock())
        finally:
            _mod.session = _orig
        mock_session.pop.assert_any_call("authentication", None)
        mock_session.pop.assert_any_call("csrf_token", None)
        assert result["ok"] is True
