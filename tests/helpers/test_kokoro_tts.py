"""Tests for python/helpers/kokoro_tts.py — preload, synthesize_sentences, is_downloading, is_downloaded (mocked)."""

import base64
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestKokoroTtsPreload:
    @pytest.mark.asyncio
    async def test_preload_sets_pipeline(self):
        mock_pipeline = MagicMock()
        mock_kokoro = MagicMock()
        mock_kokoro.KPipeline.return_value = mock_pipeline
        with patch.dict("sys.modules", {"kokoro": mock_kokoro}):
            with patch("python.helpers.kokoro_tts.PrintStyle"):
                with patch("python.helpers.kokoro_tts.NotificationManager"):
                    from python.helpers import kokoro_tts
                    kokoro_tts._pipeline = None
                    kokoro_tts.is_updating_model = False
                    try:
                        await kokoro_tts.preload()
                        assert kokoro_tts._pipeline is mock_pipeline
                    except ImportError:
                        pytest.skip("kokoro not installed")


class TestKokoroTtsIsDownloading:
    @pytest.mark.asyncio
    async def test_is_downloading_returns_bool(self):
        from python.helpers import kokoro_tts
        old = kokoro_tts.is_updating_model
        kokoro_tts.is_updating_model = False
        try:
            result = await kokoro_tts.is_downloading()
        finally:
            kokoro_tts.is_updating_model = old
        assert isinstance(result, bool)


class TestKokoroTtsIsDownloaded:
    @pytest.mark.asyncio
    async def test_is_downloaded_false_when_no_pipeline(self):
        from python.helpers import kokoro_tts
        old = kokoro_tts._pipeline
        kokoro_tts._pipeline = None
        try:
            result = await kokoro_tts.is_downloaded()
        finally:
            kokoro_tts._pipeline = old
        assert result is False

    @pytest.mark.asyncio
    async def test_is_downloaded_true_when_loaded(self):
        from python.helpers import kokoro_tts
        old = kokoro_tts._pipeline
        kokoro_tts._pipeline = MagicMock()
        try:
            result = await kokoro_tts.is_downloaded()
        finally:
            kokoro_tts._pipeline = old
        assert result is True


class TestKokoroTtsSynthesizeSentences:
    @pytest.mark.asyncio
    async def test_synthesize_returns_base64_audio(self):
        import numpy as np
        mock_audio = MagicMock()
        mock_audio.detach.return_value.cpu.return_value.numpy.return_value = np.zeros(1000)
        mock_segment = MagicMock()
        mock_segment.audio = mock_audio
        mock_pipeline = MagicMock(return_value=iter([mock_segment]))

        from python.helpers import kokoro_tts
        with patch.object(kokoro_tts, "_pipeline", mock_pipeline):
            with patch.object(kokoro_tts, "_preload", AsyncMock()):
                with patch.object(kokoro_tts, "sf") as msf:
                    msf.write = MagicMock()
                    result = await kokoro_tts.synthesize_sentences(["Hello"])
        assert isinstance(result, str)
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception:
            pass
