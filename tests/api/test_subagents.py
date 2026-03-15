"""Tests for python/api/subagents.py — Subagents API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.subagents import Subagents


def _make_handler(app=None, lock=None):
    return Subagents(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestSubagents:
    @pytest.mark.asyncio
    async def test_list_action_returns_ok_with_data(self):
        handler = _make_handler()
        with patch.object(handler, "get_subagents_list", return_value=[]) as mock_list:
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == []
        mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_action_returns_agent_data(self):
        handler = _make_handler()
        agent_data = {"name": "my-agent", "config": {}}
        with patch.object(handler, "load_agent", return_value=agent_data):
            result = await handler.process({"action": "load", "name": "my-agent"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == agent_data

    @pytest.mark.asyncio
    async def test_load_action_raises_when_name_missing(self):
        handler = _make_handler()
        result = await handler.process({"action": "load"}, MagicMock())
        assert result["ok"] is False
        assert "Subagent name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_save_action_saves_and_returns_data(self):
        handler = _make_handler()
        saved = {"name": "agent1", "config": {}}
        with patch.object(handler, "save_agent", return_value=saved):
            result = await handler.process({"action": "save", "name": "agent1", "data": {}}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == saved

    @pytest.mark.asyncio
    async def test_save_action_raises_when_name_missing(self):
        handler = _make_handler()
        result = await handler.process({"action": "save", "data": {}}, MagicMock())
        assert result["ok"] is False
        assert "Subagent name is required" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_action_calls_delete_agent(self):
        handler = _make_handler()
        with patch.object(handler, "delete_agent", return_value=None):
            result = await handler.process({"action": "delete", "name": "agent1"}, MagicMock())
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        handler = _make_handler()
        result = await handler.process({"action": "invalid"}, MagicMock())
        assert result["ok"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_use_context_when_context_id_provided(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch.object(handler, "get_subagents_list", return_value=[]):
            result = await handler.process({"action": "list", "context_id": "ctx-123"}, MagicMock())
        assert result["ok"] is True
        handler.use_context.assert_called_once_with("ctx-123")
