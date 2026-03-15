"""Tests for python/helpers/whisper.py — preload, transcribe, is_downloading, is_downloaded (mocked)."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestWhisperPreload:
    @pytest.mark.asyncio
    async def test_preload_loads_model(self):
        mock_model = MagicMock()
        with patch("python.helpers.whisper.whisper") as mw:
            mw.load_model.return_value = mock_model
        with patch("python.helpers.whisper.files") as mf:
            mf.get_abs_path.return_value = "/tmp/models/whisper"
        with patch("python.helpers.whisper.PrintStyle"):
            with patch("python.helpers.whisper.NotificationManager"):
                from python.helpers import whisper
                await whisper.preload("base")
        mw.load_model.assert_called_once_with(
            name="base",
            download_root="/tmp/models/whisper",
        )

    @pytest.mark.asyncio
    async def test_preload_raises_on_error(self):
        with patch("python.helpers.whisper.whisper") as mw:
            mw.load_model.side_effect = RuntimeError("load failed")
        with patch("python.helpers.whisper.files"):
            with patch("python.helpers.whisper.PrintStyle"):
                with patch("python.helpers.whisper.NotificationManager"):
                    from python.helpers import whisper
                    with pytest.raises(RuntimeError):
                        await whisper.preload("base")


class TestWhisperIsDownloading:
    @pytest.mark.asyncio
    async def test_is_downloading_returns_bool(self):
        with patch("python.helpers.whisper.is_updating_model", False):
            from python.helpers import whisper
            result = await whisper.is_downloading()
        assert isinstance(result, bool)


class TestWhisperIsDownloaded:
    @pytest.mark.asyncio
    async def test_is_downloaded_false_when_no_model(self):
        with patch("python.helpers.whisper._model", None):
            from python.helpers import whisper
            result = await whisper.is_downloaded()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_downloaded_true_when_model_loaded(self):
        with patch("python.helpers.whisper._model", MagicMock()):
            from python.helpers import whisper
            result = await whisper.is_downloaded()
        assert result is True


class TestWhisperTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe_decodes_and_transcribes(self):
        import base64
        audio_b64 = base64.b64encode(b"fake_audio_data").decode()
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "hello world"}

        with patch("python.helpers.whisper._model", mock_model):
            with patch("python.helpers.whisper._preload", AsyncMock()):
                with patch("tempfile.NamedTemporaryFile") as mt:
                    mock_file = MagicMock()
                    mock_file.name = "/tmp/fake.wav"
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=None)
                    mt.return_value = mock_file
                with patch("os.remove"):
                    from python.helpers import whisper
                    result = await whisper.transcribe("base", audio_b64)

        assert result["text"] == "hello world"
        mock_model.transcribe.assert_called_once()
