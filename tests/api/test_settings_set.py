"""Tests for python/api/settings_set.py — SetSettings API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.settings_set import SetSettings


def _make_handler():
    return SetSettings(app=MagicMock(), thread_lock=threading.Lock())


class TestSetSettings:
    @pytest.mark.asyncio
    async def test_sets_settings_from_input(self):
        handler = _make_handler()
        input_data = {"chat_model": "new-model", "workdir_path": "/a0"}
        mock_backend = {"chat_model": "new-model", "workdir_path": "/a0"}

        with patch("python.api.settings_set.settings.convert_in", return_value=mock_backend), \
             patch("python.api.settings_set.settings.set_settings", return_value=mock_backend), \
             patch("python.api.settings_set.settings.convert_out", return_value=mock_backend):
            result = await handler.process(input_data, MagicMock())

        assert result == mock_backend

    @pytest.mark.asyncio
    async def test_uses_settings_key_when_present(self):
        handler = _make_handler()
        input_data = {"settings": {"chat_model": "from-settings-key"}}
        mock_backend = {"chat_model": "from-settings-key"}

        with patch("python.api.settings_set.settings.Settings") as MockSettings, \
             patch("python.api.settings_set.settings.convert_in", return_value=mock_backend), \
             patch("python.api.settings_set.settings.set_settings", return_value=mock_backend), \
             patch("python.api.settings_set.settings.convert_out", return_value=mock_backend):
            await handler.process(input_data, MagicMock())
        MockSettings.assert_called_once_with(**{"chat_model": "from-settings-key"})

    @pytest.mark.asyncio
    async def test_uses_input_directly_when_no_settings_key(self):
        handler = _make_handler()
        input_data = {"chat_model": "direct-input"}
        mock_backend = {"chat_model": "direct-input"}

        with patch("python.api.settings_set.settings.Settings") as MockSettings, \
             patch("python.api.settings_set.settings.convert_in", return_value=mock_backend), \
             patch("python.api.settings_set.settings.set_settings", return_value=mock_backend), \
             patch("python.api.settings_set.settings.convert_out", return_value=mock_backend):
            await handler.process(input_data, MagicMock())
        MockSettings.assert_called_once_with(**input_data)
