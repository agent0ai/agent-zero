"""Tests for python/api/knowledge_path_get.py — GetKnowledgePath API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.knowledge_path_get import GetKnowledgePath


def _make_handler(app=None, lock=None):
    return GetKnowledgePath(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetKnowledgePath:
    @pytest.mark.asyncio
    async def test_process_raises_when_no_ctxid(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({}, MagicMock())

    @pytest.mark.asyncio
    async def test_process_returns_path_for_context(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.knowledge_path_get.projects.get_context_project_name",
                 return_value=None,
             ), \
             patch(
                 "python.api.knowledge_path_get.memory.get_custom_knowledge_subdir_abs",
                 return_value="/tmp/knowledge",
             ), \
             patch(
                 "python.api.knowledge_path_get.files.normalize_a0_path",
                 return_value="/a0/knowledge",
             ):
            result = await handler.process({"ctxid": "ctx-1"}, MagicMock())

        assert result["ok"] is True
        assert result["path"] == "/a0/knowledge"

    @pytest.mark.asyncio
    async def test_process_uses_project_path_when_project_exists(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.knowledge_path_get.projects.get_context_project_name",
                 return_value="my-project",
             ), \
             patch(
                 "python.api.knowledge_path_get.projects.get_project_meta_folder",
                 return_value="/projects/my-project/knowledge",
             ), \
             patch(
                 "python.api.knowledge_path_get.files.normalize_a0_path",
                 return_value="/a0/projects/my-project/knowledge",
             ):
            result = await handler.process({"ctxid": "ctx-1"}, MagicMock())

        assert result["ok"] is True
        assert "my-project" in result["path"] or "knowledge" in result["path"]
