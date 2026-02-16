"""
Tests for plugins/comms_core/tools/channel_send.py

Covers missing param validation, unknown platform handling,
and successful send via handle_outbound.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins.comms_core.tools.channel_send import ChannelSend


def _make_tool(args: dict) -> ChannelSend:
    """Create a ChannelSend instance with the given args dict."""
    tool = object.__new__(ChannelSend)
    tool.args = args
    tool.agent = MagicMock()
    tool.name = "channel_send"
    tool.message = ""
    return tool


# ---------------------------------------------------------------------------
# Missing parameters
# ---------------------------------------------------------------------------

class TestMissingParams:
    @pytest.mark.asyncio
    async def test_missing_all_params(self):
        tool = _make_tool({})
        resp = await tool.execute()
        assert "platform" in resp.message
        assert "chat_id" in resp.message
        assert "message" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_missing_platform(self):
        tool = _make_tool({"chat_id": "c1", "message": "hi"})
        resp = await tool.execute()
        assert "platform" in resp.message
        assert "chat_id" not in resp.message
        assert "message" not in resp.message

    @pytest.mark.asyncio
    async def test_missing_chat_id(self):
        tool = _make_tool({"platform": "telegram", "message": "hi"})
        resp = await tool.execute()
        assert "chat_id" in resp.message
        assert "platform" not in resp.message

    @pytest.mark.asyncio
    async def test_missing_message(self):
        tool = _make_tool({"platform": "telegram", "chat_id": "c1"})
        resp = await tool.execute()
        assert "message" in resp.message
        assert "platform" not in resp.message


# ---------------------------------------------------------------------------
# Unknown platform
# ---------------------------------------------------------------------------

class TestUnknownPlatform:
    @pytest.mark.asyncio
    async def test_no_bridge_registered(self, monkeypatch):
        from plugins.comms_core.helpers import bridge_registry
        monkeypatch.setattr(bridge_registry, "get_bridge", lambda p: None)
        monkeypatch.setattr(bridge_registry, "list_platforms", lambda: ["slack"])

        tool = _make_tool({"platform": "discord", "chat_id": "c1", "message": "hi"})
        resp = await tool.execute()
        assert "No active bridge" in resp.message
        assert "discord" in resp.message
        assert "slack" in resp.message

    @pytest.mark.asyncio
    async def test_no_bridges_at_all(self, monkeypatch):
        from plugins.comms_core.helpers import bridge_registry
        monkeypatch.setattr(bridge_registry, "get_bridge", lambda p: None)
        monkeypatch.setattr(bridge_registry, "list_platforms", lambda: [])

        tool = _make_tool({"platform": "telegram", "chat_id": "c1", "message": "hi"})
        resp = await tool.execute()
        assert "none" in resp.message


# ---------------------------------------------------------------------------
# Successful send
# ---------------------------------------------------------------------------

class TestSuccessfulSend:
    @pytest.mark.asyncio
    async def test_sends_outbound_message(self, monkeypatch):
        captured = []
        mock_bridge = AsyncMock()
        mock_bridge.handle_outbound = AsyncMock(side_effect=lambda msg: captured.append(msg))

        from plugins.comms_core.helpers import bridge_registry
        monkeypatch.setattr(bridge_registry, "get_bridge", lambda p: mock_bridge)

        tool = _make_tool({"platform": "telegram", "chat_id": "chat-123", "message": "hello world"})
        resp = await tool.execute()

        assert "sent" in resp.message.lower()
        assert resp.break_loop is False
        assert len(captured) == 1
        outbound = captured[0]
        assert outbound.platform_chat_id == "chat-123"
        assert outbound.text == "hello world"

    @pytest.mark.asyncio
    async def test_response_includes_platform_and_chat(self, monkeypatch):
        mock_bridge = AsyncMock()
        from plugins.comms_core.helpers import bridge_registry
        monkeypatch.setattr(bridge_registry, "get_bridge", lambda p: mock_bridge)

        tool = _make_tool({"platform": "slack", "chat_id": "C0123", "message": "test"})
        resp = await tool.execute()

        assert "slack" in resp.message
        assert "C0123" in resp.message
