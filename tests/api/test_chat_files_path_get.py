"""Tests for python/api/chat_files_path_get.py — GetChatFilesPath API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_files_path_get import GetChatFilesPath


def _make_handler(app=None, lock=None):
    return GetChatFilesPath(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetChatFilesPath:
    @pytest.mark.asyncio
    async def test_returns_project_folder_when_project_exists(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_files_path_get.projects") as mock_projects, \
             patch("python.api.chat_files_path_get.files") as mock_files:
            mock_projects.get_context_project_name.return_value = "my-project"
            mock_projects.get_project_folder.return_value = "/a0/projects/my-project"
            mock_files.normalize_a0_path.return_value = "/a0/projects/my-project"

            result = await handler.process({"ctxid": "ctx-123"}, MagicMock())

        assert result["ok"] is True
        assert result["path"] == "/a0/projects/my-project"

    @pytest.mark.asyncio
    async def test_returns_workdir_when_no_project(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_files_path_get.projects") as mock_projects, \
             patch("python.api.chat_files_path_get.settings") as mock_settings:
            mock_projects.get_context_project_name.return_value = None
            mock_settings.get_settings.return_value = {"workdir_path": "/a0/workdir"}

            result = await handler.process({"ctxid": "ctx-123"}, MagicMock())

        assert result["ok"] is True
        assert result["path"] == "/a0/workdir"

    @pytest.mark.asyncio
    async def test_empty_ctxid_raises_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({"ctxid": ""}, MagicMock())

    @pytest.mark.asyncio
    async def test_missing_ctxid_raises_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({}, MagicMock())
