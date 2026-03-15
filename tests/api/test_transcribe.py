"""Tests for python/api/transcribe.py — Transcribe API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.transcribe import Transcribe


def _make_handler(app=None, lock=None):
    return Transcribe(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe_returns_result_on_success(self):
        handler = _make_handler()
        mock_result = {"text": "transcribed text", "language": "en"}
        with patch("python.api.transcribe.settings.get_settings", return_value={"stt_model_size": "base"}), \
             patch("python.api.transcribe.whisper.transcribe", new_callable=AsyncMock, return_value=mock_result):
            result = await handler.process({"audio": b"fake_audio"}, MagicMock())
        assert result["text"] == "transcribed text"
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_transcribe_use_context_when_ctxid_provided(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.transcribe.settings.get_settings", return_value={"stt_model_size": "base"}), \
             patch("python.api.transcribe.whisper.transcribe", new_callable=AsyncMock, return_value={}):
            await handler.process({"audio": b"data", "ctxid": "ctx-1"}, MagicMock())
        handler.use_context.assert_called_once_with("ctx-1")

    @pytest.mark.asyncio
    async def test_transcribe_passes_settings_to_whisper(self):
        handler = _make_handler()
        with patch("python.api.transcribe.settings.get_settings", return_value={"stt_model_size": "large-v3"}) as mock_settings, \
             patch("python.api.transcribe.whisper.transcribe", new_callable=AsyncMock) as mock_transcribe:
            await handler.process({"audio": b"data"}, MagicMock())
        mock_transcribe.assert_called_once_with("large-v3", b"data")
