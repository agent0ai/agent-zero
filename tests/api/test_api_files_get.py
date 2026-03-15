"""Tests for python/api/api_files_get.py — ApiFilesGet API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.api_files_get import ApiFilesGet


def _make_handler(app=None, lock=None):
    return ApiFilesGet(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiFilesGet:
    def test_requires_auth_false(self):
        assert ApiFilesGet.requires_auth() is False

    def test_requires_csrf_false(self):
        assert ApiFilesGet.requires_csrf() is False

    def test_requires_api_key_true(self):
        assert ApiFilesGet.requires_api_key() is True

    def test_get_methods_returns_post(self):
        assert ApiFilesGet.get_methods() == ["POST"]

    @pytest.mark.asyncio
    async def test_process_returns_400_when_paths_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({}, MagicMock())

        assert result.status_code == 400
        assert b"paths array is required" in result.response[0]

    @pytest.mark.asyncio
    async def test_process_returns_400_when_paths_not_list(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({"paths": "not-a-list"}, MagicMock())

        assert result.status_code == 400
        assert b"paths must be an array" in result.response[0]

    @pytest.mark.asyncio
    async def test_process_returns_base64_files_for_valid_paths(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        test_file = tmp_path / "doc.txt"
        test_file.write_bytes(b"file content")
        ext_path = str(test_file)

        result = await handler.process({"paths": [ext_path]}, MagicMock())

        assert isinstance(result, dict)
        assert "doc.txt" in result
        import base64
        assert base64.b64decode(result["doc.txt"]) == b"file content"

    @pytest.mark.asyncio
    async def test_process_converts_internal_path_to_external(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        uploads_dir = tmp_path / "usr" / "uploads"
        uploads_dir.mkdir(parents=True)
        (uploads_dir / "uploaded.pdf").write_bytes(b"pdf content")

        with patch("python.api.api_files_get.os.path.exists", return_value=True), \
             patch("python.api.api_files_get.files.get_abs_path", return_value=str(uploads_dir / "uploaded.pdf")):
            result = await handler.process(
                {"paths": ["/a0/tmp/uploads/uploaded.pdf"]}, MagicMock()
            )

        assert "uploaded.pdf" in result
