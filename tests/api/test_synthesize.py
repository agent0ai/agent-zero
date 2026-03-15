"""Tests for python/api/synthesize.py — Synthesize API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.synthesize import Synthesize


def _make_handler(app=None, lock=None):
    return Synthesize(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_synthesize_returns_audio_on_success(self):
        handler = _make_handler()
        mock_audio = b"fake_audio_data"
        with patch("python.api.synthesize.kokoro_tts.synthesize_sentences", new_callable=AsyncMock, return_value=mock_audio):
            result = await handler.process({"text": "Hello world"}, MagicMock())
        assert result["success"] is True
        assert result["audio"] == mock_audio

    @pytest.mark.asyncio
    async def test_synthesize_uses_empty_text_default(self):
        handler = _make_handler()
        with patch("python.api.synthesize.kokoro_tts.synthesize_sentences", new_callable=AsyncMock) as mock_synth:
            await handler.process({}, MagicMock())
        mock_synth.assert_called_once_with([""])

    @pytest.mark.asyncio
    async def test_synthesize_passes_text_to_tts(self):
        handler = _make_handler()
        with patch("python.api.synthesize.kokoro_tts.synthesize_sentences", new_callable=AsyncMock) as mock_synth:
            await handler.process({"text": "Test sentence"}, MagicMock())
        mock_synth.assert_called_once_with(["Test sentence"])

    @pytest.mark.asyncio
    async def test_synthesize_use_context_when_ctxid_provided(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx) as mock_use_ctx, \
             patch("python.api.synthesize.kokoro_tts.synthesize_sentences", new_callable=AsyncMock, return_value=b"audio"):
            await handler.process({"text": "Hi", "ctxid": "ctx-1"}, MagicMock())
            mock_use_ctx.assert_called_once_with("ctx-1")

    @pytest.mark.asyncio
    async def test_synthesize_returns_error_on_exception(self):
        handler = _make_handler()
        with patch("python.api.synthesize.kokoro_tts.synthesize_sentences", new_callable=AsyncMock, side_effect=Exception("TTS failed")):
            result = await handler.process({"text": "Hello"}, MagicMock())
        assert result["success"] is False
        assert "TTS failed" in result["error"]
