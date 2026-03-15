"""Tests for python/api/upload_work_dir_files.py — UploadWorkDirFiles API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.upload_work_dir_files import UploadWorkDirFiles


def _make_handler(app=None, lock=None):
    return UploadWorkDirFiles(app=app or MagicMock(), thread_lock=lock or threading.Lock())


def _make_file_storage(filename="test.txt", content=b"content"):
    storage = MagicMock()
    storage.filename = filename
    storage.stream = MagicMock()
    storage.stream.read = MagicMock(return_value=content)
    return storage


class TestUploadWorkDirFiles:
    @pytest.mark.asyncio
    async def test_process_raises_when_no_files(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.files = {}
        request.form = {"path": "/a0"}

        with pytest.raises(Exception, match="No files uploaded"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_returns_success_when_all_uploaded(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage("doc.txt")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"path": "/a0"}

        with patch(
            "python.api.upload_work_dir_files.upload_files",
            new_callable=AsyncMock,
            return_value=(["doc.txt"], []),
        ), patch(
            "python.api.upload_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=[{"name": "doc.txt"}],
        ):
            result = await handler.process({}, request)

        assert result["message"] == "Files uploaded successfully"
        assert result["successful"] == ["doc.txt"]
        assert result["failed"] == []
        assert "data" in result

    @pytest.mark.asyncio
    async def test_process_returns_partial_when_some_failed(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage("doc.txt")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"path": "/a0"}

        with patch(
            "python.api.upload_work_dir_files.upload_files",
            new_callable=AsyncMock,
            return_value=(["doc.txt"], ["bad.txt"]),
        ), patch(
            "python.api.upload_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await handler.process({}, request)

        assert result["message"] == "Some files failed to upload"
        assert result["successful"] == ["doc.txt"]
        assert result["failed"] == ["bad.txt"]

    @pytest.mark.asyncio
    async def test_process_raises_when_all_failed(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage("bad.txt")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.files.getlist = MagicMock(return_value=[storage])
        request.form = {"path": "/a0"}

        with patch(
            "python.api.upload_work_dir_files.upload_files",
            new_callable=AsyncMock,
            return_value=([], ["bad.txt"]),
        ):
            with pytest.raises(Exception, match="All uploads failed"):
                await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_uses_getlist_for_files(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.files = MagicMock()
        request.files.getlist = MagicMock(return_value=[])
        request.files.__contains__ = lambda self, k: k == "files[]"
        request.form = {"path": "/a0"}

        with patch(
            "python.api.upload_work_dir_files.upload_files",
            new_callable=AsyncMock,
            return_value=([], []),
        ), patch(
            "python.api.upload_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await handler.process({}, request)

        assert "data" in result
