"""Tests for python/api/knowledge_reindex.py — ReindexKnowledge API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.knowledge_reindex import ReindexKnowledge


def _make_handler(app=None, lock=None):
    return ReindexKnowledge(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestReindexKnowledge:
    @pytest.mark.asyncio
    async def test_process_raises_when_no_ctxid(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({}, MagicMock())

    @pytest.mark.asyncio
    async def test_process_returns_ok_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()
        mock_ctx.log = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.knowledge_reindex.memory.Memory.reload",
                 new_callable=AsyncMock,
             ):
            result = await handler.process({"ctxid": "ctx-1"}, MagicMock())

        assert result["ok"] is True
        assert result["message"] == "Knowledge re-indexed"

    @pytest.mark.asyncio
    async def test_process_calls_memory_reload(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()
        mock_ctx.log = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.knowledge_reindex.memory.Memory.reload",
                 new_callable=AsyncMock,
             ) as mock_reload:
            await handler.process({"ctxid": "ctx-1"}, MagicMock())

        mock_reload.assert_called_once_with(mock_ctx.agent0)

    @pytest.mark.asyncio
    async def test_process_calls_set_initial_progress(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.agent0 = MagicMock()
        mock_ctx.log = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch(
                 "python.api.knowledge_reindex.memory.Memory.reload",
                 new_callable=AsyncMock,
             ):
            await handler.process({"ctxid": "ctx-1"}, MagicMock())

        mock_ctx.log.set_initial_progress.assert_called_once()
