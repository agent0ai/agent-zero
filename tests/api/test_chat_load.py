"""Tests for python/api/chat_load.py — LoadChats API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_load import LoadChats


def _make_handler(app=None, lock=None):
    return LoadChats(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestLoadChats:
    @pytest.mark.asyncio
    async def test_loads_chats_and_returns_ctxids(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.chat_load.persist_chat") as mock_persist:
            mock_persist.load_json_chats.return_value = ["ctx-1", "ctx-2"]
            result = await handler.process({"chats": [{"id": "c1"}, {"id": "c2"}]}, MagicMock())

        assert result["message"] == "Chats loaded."
        assert result["ctxids"] == ["ctx-1", "ctx-2"]
        mock_persist.load_json_chats.assert_called_once_with([{"id": "c1"}, {"id": "c2"}])

    @pytest.mark.asyncio
    async def test_empty_chats_raises_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No chats provided"):
            await handler.process({"chats": []}, MagicMock())

    @pytest.mark.asyncio
    async def test_missing_chats_raises_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with pytest.raises(Exception, match="No chats provided"):
            await handler.process({}, MagicMock())

    @pytest.mark.asyncio
    async def test_delegates_to_load_json_chats(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        chats = [{"id": "chat-1", "name": "Test"}]

        with patch("python.api.chat_load.persist_chat") as mock_persist:
            mock_persist.load_json_chats.return_value = ["loaded-ctx"]
            result = await handler.process({"chats": chats}, MagicMock())

        mock_persist.load_json_chats.assert_called_once_with(chats)
        assert result["ctxids"] == ["loaded-ctx"]
