"""Tests for python/api/settings_get.py — GetSettings API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.settings_get import GetSettings


def _make_handler():
    return GetSettings(app=MagicMock(), thread_lock=threading.Lock())


class TestGetSettings:
    @pytest.mark.asyncio
    async def test_returns_settings_dict(self):
        handler = _make_handler()
        mock_backend = {"chat_model": "test-model", "workdir_path": "/a0"}
        mock_out = {"chat_model": "test-model", "workdir_path": "/a0"}

        with patch("python.api.settings_get.settings.get_settings", return_value=mock_backend), \
             patch("python.api.settings_get.settings.convert_out", return_value=mock_out):
            result = await handler.process({}, MagicMock())

        assert result == mock_out

    @pytest.mark.asyncio
    async def test_calls_get_settings(self):
        handler = _make_handler()
        with patch("python.api.settings_get.settings.get_settings") as mock_get, \
             patch("python.api.settings_get.settings.convert_out", return_value={}):
            await handler.process({}, MagicMock())
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_convert_out_with_backend(self):
        handler = _make_handler()
        mock_backend = {"key": "value"}
        with patch("python.api.settings_get.settings.get_settings", return_value=mock_backend), \
             patch("python.api.settings_get.settings.convert_out") as mock_convert:
            await handler.process({}, MagicMock())
        mock_convert.assert_called_once_with(mock_backend)

    def test_get_methods_returns_get_and_post(self):
        assert GetSettings.get_methods() == ["GET", "POST"]
