"""Tests for python/api/chat_export.py — ExportChat API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_export import ExportChat


def _make_handler(app=None, lock=None):
    return ExportChat(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestExportChat:
    @pytest.mark.asyncio
    async def test_exports_chat_and_returns_content(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_export.persist_chat") as mock_persist:
            mock_persist.export_json_chat.return_value = '{"messages": []}'
            result = await handler.process({"ctxid": "ctx-123"}, MagicMock())

        assert result["message"] == "Chats exported."
        assert result["ctxid"] == "ctx-123"
        assert result["content"] == '{"messages": []}'
        mock_persist.export_json_chat.assert_called_once_with(mock_ctx)

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
