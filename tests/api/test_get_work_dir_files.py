"""Tests for python/api/get_work_dir_files.py — GetWorkDirFiles API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.get_work_dir_files import GetWorkDirFiles


def _make_handler(app=None, lock=None):
    return GetWorkDirFiles(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetWorkDirFiles:
    @pytest.mark.asyncio
    async def test_get_methods_returns_get(self):
        assert GetWorkDirFiles.get_methods() == ["GET"]

    @pytest.mark.asyncio
    async def test_process_returns_files_for_path(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_files = [{"name": "file1.txt", "path": "/a0/file1.txt"}]
        request = MagicMock()
        request.args = {"path": "/a0/subdir"}

        with patch(
            "python.api.get_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=mock_files,
        ):
            result = await handler.process({}, request)

        assert result == {"data": mock_files}

    @pytest.mark.asyncio
    async def test_process_normalizes_work_dir_to_a0(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_files = []
        request = MagicMock()
        request.args = {"path": "$WORK_DIR"}

        with patch(
            "python.api.get_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=mock_files,
        ) as mock_call:
            result = await handler.process({}, request)

        mock_call.assert_called_once()
        assert mock_call.call_args[0][1] == "/a0"
        assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_process_uses_empty_path_when_not_provided(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.args = {}

        with patch(
            "python.api.get_work_dir_files.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_call:
            await handler.process({}, request)

        mock_call.assert_called_once()
        assert mock_call.call_args[0][1] == ""
