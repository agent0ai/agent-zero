"""Tests for python/api/download_work_dir_file.py — DownloadFile API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.download_work_dir_file import (
    DownloadFile,
    stream_file_download,
    make_disposition,
)


def _make_handler(app=None, lock=None):
    return DownloadFile(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMakeDisposition:
    def test_ascii_filename(self):
        result = make_disposition("document.pdf")
        assert "filename=" in result
        assert "document.pdf" in result
        assert "filename*=" in result

    def test_utf8_filename(self):
        result = make_disposition("café.txt")
        assert "attachment" in result
        assert "filename*=" in result


class TestStreamFileDownload:
    def test_raises_for_unsupported_source_type(self):
        with pytest.raises(ValueError, match="Unsupported file source type"):
            stream_file_download(MagicMock(), "test.txt")

    def test_streams_from_bytesio(self):
        from io import BytesIO
        data = BytesIO(b"hello world")
        resp = stream_file_download(data, "test.txt")
        assert resp.status_code == 200
        assert b"hello world" in b"".join(resp.response)


class TestDownloadFile:
    @pytest.mark.asyncio
    async def test_get_methods_returns_get(self):
        assert DownloadFile.get_methods() == ["GET"]

    @pytest.mark.asyncio
    async def test_process_raises_when_no_path(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.args = {}

        with pytest.raises(ValueError, match="No file path provided"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_prepends_slash_to_relative_path(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.args = {"path": "a0/file.txt"}

        with patch(
            "python.api.download_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value={"exists": False},
        ):
            with pytest.raises(Exception, match="not found"):
                await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_raises_when_file_not_found(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.args = {"path": "/a0/missing.txt"}

        with patch(
            "python.api.download_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value={"exists": False},
        ):
            with pytest.raises(Exception, match="not found"):
                await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_returns_stream_for_file_in_development(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.args = {"path": "/a0/doc.txt"}

        file_info_result = {
            "exists": True,
            "is_dir": False,
            "is_file": True,
            "abs_path": "/tmp/doc.txt",
            "file_name": "doc.txt",
        }

        with patch(
            "python.api.download_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=[
                file_info_result,
                b"SGVsbG8gV29ybGQ=",  # base64 "Hello World"
            ],
        ), patch(
            "python.api.download_work_dir_file.runtime.is_development",
            return_value=True,
        ):
            result = await handler.process({}, request)

        assert result.status_code == 200
        assert b"Hello World" in b"".join(result.response)
