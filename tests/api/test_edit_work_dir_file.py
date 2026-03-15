"""Tests for python/api/edit_work_dir_file.py — EditWorkDirFile API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.edit_work_dir_file import EditWorkDirFile


def _make_handler(app=None, lock=None):
    return EditWorkDirFile(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestEditWorkDirFile:
    @pytest.mark.asyncio
    async def test_get_methods_returns_get_and_post(self):
        assert set(EditWorkDirFile.get_methods()) == {"GET", "POST"}

    @pytest.mark.asyncio
    async def test_get_returns_error_when_path_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "GET"
        request.args = {}

        result = await handler.process({}, request)

        assert result == {"error": "Path is required"}

    @pytest.mark.asyncio
    async def test_get_prepends_slash_to_relative_path(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "GET"
        request.args = {"path": "a0/file.txt"}

        with patch(
            "python.api.edit_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value={"path": "/a0/file.txt", "content": "hello"},
        ):
            result = await handler.process({}, request)

        assert result["data"]["content"] == "hello"

    @pytest.mark.asyncio
    async def test_post_returns_error_when_path_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        result = await handler.process({}, request)

        assert result == {"error": "Path is required"}

    @pytest.mark.asyncio
    async def test_post_returns_error_when_content_not_string(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        result = await handler.process({"path": "/a0/f.txt", "content": 123}, request)

        assert result == {"error": "Content must be a string"}

    @pytest.mark.asyncio
    async def test_post_returns_error_when_file_too_large(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"
        large_content = "x" * (1024 * 1024 + 1)

        result = await handler.process(
            {"path": "/a0/f.txt", "content": large_content}, request
        )

        assert result == {"error": "File exceeds 1 MB and cannot be edited"}

    @pytest.mark.asyncio
    async def test_post_returns_ok_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        with patch(
            "python.api.edit_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await handler.process(
                {"path": "/a0/f.txt", "content": "new content"}, request
            )

        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_extract_error_message_from_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        with patch(
            "python.api.edit_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=Exception("Traceback:\n  File x\n  File y\nValueError: actual error"),
        ):
            result = await handler.process(
                {"path": "/a0/f.txt", "content": "x"}, request
            )

        assert "error" in result
        assert "actual error" in result["error"]
