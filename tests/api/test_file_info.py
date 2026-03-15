"""Tests for python/api/file_info.py — FileInfoApi handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.file_info import FileInfoApi


def _make_handler(app=None, lock=None):
    return FileInfoApi(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestFileInfoApi:
    @pytest.mark.asyncio
    async def test_process_returns_file_info(self, mock_app, tmp_path):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        info_result = {
            "input_path": "/a0/test.txt",
            "abs_path": str(tmp_path / "a0" / "test.txt"),
            "exists": True,
            "is_dir": False,
            "is_file": True,
            "is_link": False,
            "size": 42,
            "modified": 12345.0,
            "created": 12340.0,
            "permissions": 0o644,
            "dir_path": str(tmp_path / "a0"),
            "file_name": "test.txt",
            "file_ext": ".txt",
            "message": "",
        }

        with patch(
            "python.api.file_info.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=info_result,
        ):
            result = await handler.process({"path": "/a0/test.txt"}, MagicMock())

        assert result == info_result
        assert result["exists"] is True
        assert result["is_file"] is True

    @pytest.mark.asyncio
    async def test_process_uses_empty_path_default(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        info_result = {"exists": False, "message": "File  not found."}

        with patch(
            "python.api.file_info.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=info_result,
        ) as mock_call:
            await handler.process({}, MagicMock())

        mock_call.assert_called_once()
        assert mock_call.call_args[0][1] == ""

    @pytest.mark.asyncio
    async def test_process_passes_path_from_input(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.file_info.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value={"exists": False},
        ) as mock_call:
            await handler.process({"path": "/a0/deep/file.txt"}, MagicMock())

        mock_call.assert_called_once()
        assert mock_call.call_args[0][1] == "/a0/deep/file.txt"
