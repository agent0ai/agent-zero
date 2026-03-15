"""Tests for python/api/projects.py — Projects API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.projects import Projects


def _make_handler(app=None, lock=None):
    return Projects(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestProjects:
    @pytest.mark.asyncio
    async def test_list_action_returns_ok_with_data(self):
        handler = _make_handler()
        with patch.object(handler, "get_active_projects_list", return_value=[]):
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_list_options_action_returns_options(self):
        handler = _make_handler()
        with patch.object(handler, "get_active_projects_options", return_value=[{"key": "p1", "label": "Project 1"}]):
            result = await handler.process({"action": "list_options"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == [{"key": "p1", "label": "Project 1"}]

    @pytest.mark.asyncio
    async def test_load_action_returns_project_data(self):
        handler = _make_handler()
        with patch.object(handler, "load_project", return_value={"name": "proj1"}):
            result = await handler.process({"action": "load", "name": "proj1"}, MagicMock())
        assert result["ok"] is True
        assert result["data"]["name"] == "proj1"

    @pytest.mark.asyncio
    async def test_create_action_creates_project(self):
        handler = _make_handler()
        project_data = {"name": "new-proj", "title": "New Project"}
        with patch.object(handler, "create_project", return_value=project_data):
            result = await handler.process({"action": "create", "project": project_data}, MagicMock())
        assert result["ok"] is True
        assert result["data"]["name"] == "new-proj"

    @pytest.mark.asyncio
    async def test_activate_action_requires_context_and_name(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch.object(handler, "activate_project", return_value={"success": True}):
            result = await handler.process({
                "action": "activate", "context_id": "ctx-1", "name": "proj1"
            }, MagicMock())
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        handler = _make_handler()
        result = await handler.process({"action": "invalid"}, MagicMock())
        assert result["ok"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_returns_error_with_message(self):
        handler = _make_handler()
        with patch.object(handler, "get_active_projects_list", side_effect=Exception("db error")):
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is False
        assert "db error" in result["error"]
