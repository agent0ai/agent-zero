"""Tests for python/api/rename_work_dir_file.py — RenameWorkDirFile API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.rename_work_dir_file import RenameWorkDirFile


def _make_handler(app=None, lock=None):
    return RenameWorkDirFile(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestRenameWorkDirFile:
    @pytest.mark.asyncio
    async def test_process_returns_error_when_new_name_empty(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"path": "/a0/old.txt", "newName": "", "currentPath": "/a0"},
            MagicMock(),
        )

        assert result == {"error": "New name is required"}

    @pytest.mark.asyncio
    async def test_process_returns_error_when_new_name_whitespace_only(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"path": "/a0/old.txt", "newName": "   ", "currentPath": "/a0"},
            MagicMock(),
        )

        assert result == {"error": "New name is required"}

    @pytest.mark.asyncio
    async def test_process_returns_error_when_path_missing_for_rename(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"action": "rename", "newName": "new.txt", "currentPath": "/a0"},
            MagicMock(),
        )

        assert result == {"error": "Path is required"}

    @pytest.mark.asyncio
    async def test_process_returns_error_when_parent_path_missing_for_create_folder(
        self, mock_app
    ):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"action": "create-folder", "newName": "newdir", "parentPath": ""},
            MagicMock(),
        )

        assert result == {"error": "Parent path is required"}

    @pytest.mark.asyncio
    async def test_process_returns_data_on_rename_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_files = [{"name": "renamed.txt"}]

        with patch(
            "python.api.rename_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=[True, mock_files],
        ):
            result = await handler.process(
                {
                    "path": "/a0/old.txt",
                    "newName": "renamed.txt",
                    "currentPath": "/a0",
                },
                MagicMock(),
            )

        assert result == {"data": mock_files}

    @pytest.mark.asyncio
    async def test_process_returns_data_on_create_folder_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_files = [{"name": "newdir"}]

        with patch(
            "python.api.rename_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            side_effect=[True, mock_files],
        ):
            result = await handler.process(
                {
                    "action": "create-folder",
                    "newName": "newdir",
                    "parentPath": "/a0",
                    "currentPath": "/a0",
                },
                MagicMock(),
            )

        assert result == {"data": mock_files}

    @pytest.mark.asyncio
    async def test_process_returns_error_on_rename_failure(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.rename_work_dir_file.runtime.call_development_function",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await handler.process(
                {
                    "path": "/a0/old.txt",
                    "newName": "new.txt",
                    "currentPath": "/a0",
                },
                MagicMock(),
            )

        assert result == {"error": "Rename failed"}
