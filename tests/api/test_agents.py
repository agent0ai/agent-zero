"""Tests for python/api/agents.py — Agents API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.agents import Agents


def _make_handler(app=None, lock=None):
    return Agents(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestAgents:
    @pytest.mark.asyncio
    async def test_list_action_returns_ok_with_data(self):
        handler = _make_handler()
        with patch("python.api.agents.subagents.get_all_agents_list", return_value=[]) as mock_get:
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == []
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_action_returns_agents_list(self):
        handler = _make_handler()
        agents = [{"name": "agent1"}, {"name": "agent2"}]
        with patch("python.api.agents.subagents.get_all_agents_list", return_value=agents):
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is True
        assert result["data"] == agents

    @pytest.mark.asyncio
    async def test_invalid_action_returns_error(self):
        handler = _make_handler()
        result = await handler.process({"action": "invalid"}, MagicMock())
        assert result["ok"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_action_returns_invalid_error(self):
        handler = _make_handler()
        result = await handler.process({"action": ""}, MagicMock())
        assert result["ok"] is False
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_returns_error_with_message(self):
        handler = _make_handler()
        with patch("python.api.agents.subagents.get_all_agents_list", side_effect=Exception("backend error")):
            result = await handler.process({"action": "list"}, MagicMock())
        assert result["ok"] is False
        assert "backend error" in result["error"]
