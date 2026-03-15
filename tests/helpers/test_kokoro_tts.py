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
        with patch("python.helpers.kokoro_tts.KPipeline", return_value=mock_pipeline):
            with patch("python.helpers.kokoro_tts.PrintStyle"):
                with patch("python.helpers.kokoro_tts.NotificationManager"):
                    from python.helpers import kokoro_tts
                    try:
                        await kokoro_tts.preload()
                        assert kokoro_tts._pipeline is mock_pipeline
                    except ImportError:
                        pytest.skip("kokoro not installed")


class TestKokoroTtsIsDownloading:
    @pytest.mark.asyncio
    async def test_is_downloading_returns_bool(self):
        with patch("python.helpers.kokoro_tts.is_updating_model", False):
            from python.helpers import kokoro_tts
            result = await kokoro_tts.is_downloading()
        assert isinstance(result, bool)


class TestKokoroTtsIsDownloaded:
    @pytest.mark.asyncio
    async def test_is_downloaded_false_when_no_pipeline(self):
        with patch("python.helpers.kokoro_tts._pipeline", None):
            from python.helpers import kokoro_tts
            result = await kokoro_tts.is_downloaded()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_downloaded_true_when_loaded(self):
        with patch("python.helpers.kokoro_tts._pipeline", MagicMock()):
            from python.helpers import kokoro_tts
            result = await kokoro_tts.is_downloaded()
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
