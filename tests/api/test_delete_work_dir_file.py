"""Tests for python/api/delete_work_dir_file.py — DeleteWorkDirFile API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.delete_work_dir_file import DeleteWorkDirFile


def _make_handler(app=None, lock=None):
    return DeleteWorkDirFile(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestDeleteWorkDirFile:
    @pytest.mark.asyncio
    async def test_process_returns_data_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_files = [{"name": "remaining.txt"}]

        with patch(
            "python.api.delete_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=[True, mock_files],
        ):
            result = await handler.process(
                {"path": "/a0/to_delete.txt", "currentPath": "/a0"}, MagicMock()
            )

        assert result == {"data": mock_files}

    @pytest.mark.asyncio
    async def test_process_prepends_slash_to_relative_path(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.delete_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=[True, []],
        ) as mock_call:
            await handler.process(
                {"path": "a0/file.txt", "currentPath": "/a0"}, MagicMock()
            )

        assert mock_call.call_args_list[0][0][1] == "/a0/file.txt"

    @pytest.mark.asyncio
    async def test_process_returns_error_when_delete_fails(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.delete_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await handler.process(
                {"path": "/a0/missing.txt", "currentPath": "/a0"}, MagicMock()
            )

        assert result == {"error": "File not found or could not be deleted"}

    @pytest.mark.asyncio
    async def test_process_returns_error_on_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.delete_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=Exception("Permission denied"),
        ):
            result = await handler.process(
                {"path": "/a0/protected.txt", "currentPath": "/a0"}, MagicMock()
            )

        assert "error" in result
        assert "Permission denied" in result["error"]
