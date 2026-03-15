"""Tests for python/api/restart.py — Restart API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.restart import Restart


def _make_handler(app=None, lock=None):
    return Restart(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestRestart:
    @pytest.mark.asyncio
    async def test_process_calls_reload(self):
        handler = _make_handler()
        with patch("python.api.restart.process.reload") as mock_reload:
            result = await handler.process({}, MagicMock())
        mock_reload.assert_called_once()
        assert isinstance(result, Response)
        assert result.status_code == 200
