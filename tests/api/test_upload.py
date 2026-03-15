"""Tests for python/api/upload.py — UploadFile API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.upload import UploadFile


def _make_handler(app=None, lock=None):
    return UploadFile(app=app or MagicMock(), thread_lock=lock or threading.Lock())


def _make_file_storage(filename="test.txt"):
    storage = MagicMock()
    storage.filename = filename
    storage.save = MagicMock()
    return storage


class TestUploadFile:
    @pytest.mark.asyncio
    async def test_process_raises_when_no_file_part(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.files = {}

        with pytest.raises(Exception, match="No file part"):
            await handler.process({}, request)

    @pytest.mark.asyncio
    async def test_process_returns_filenames_on_success(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage("doc.pdf")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "file"
        request.files.getlist = MagicMock(return_value=[storage])

        with patch("python.api.upload.files.get_abs_path", return_value=str(tmp_path / "usr/uploads/doc.pdf")), \
             patch("python.api.upload.safe_filename", return_value="doc.pdf"):
            (tmp_path / "usr" / "uploads").mkdir(parents=True)
            result = await handler.process({}, request)

        assert result == {"filenames": ["doc.pdf"]}

    @pytest.mark.asyncio
    async def test_process_skips_empty_filename(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        storage = _make_file_storage("")
        storage.filename = ""
        request = MagicMock()
        request.files = {"file": [storage]}
        request.files.getlist = MagicMock(return_value=[storage])

        with patch("python.api.upload.safe_filename", return_value=""):
            result = await handler.process({}, request)

        assert result == {"filenames": []}

    @pytest.mark.asyncio
    async def test_process_handles_multiple_files(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        s1 = _make_file_storage("a.txt")
        s2 = _make_file_storage("b.txt")
        request = MagicMock()
        request.files = MagicMock()
        request.files.__contains__ = lambda self, k: k == "file"
        request.files.getlist = MagicMock(return_value=[s1, s2])

        def get_path(*parts):
            return str(tmp_path / "usr" / "uploads" / parts[-1])

        with patch("python.api.upload.files.get_abs_path", side_effect=get_path), \
             patch("python.api.upload.safe_filename", side_effect=lambda x: x):
            (tmp_path / "usr" / "uploads").mkdir(parents=True)
            result = await handler.process({}, request)

        assert result["filenames"] == ["a.txt", "b.txt"]

    @pytest.mark.asyncio
    async def test_allowed_file_returns_true(self, mock_app):
        handler = _make_handler(*mock_app)
        assert handler.allowed_file("any.xyz") is True
