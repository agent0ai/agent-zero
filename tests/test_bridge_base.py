"""
Tests for plugins/comms_core/helpers/bridge_base.py

Covers NormalisedAttachment, access control, command handling,
outbound dispatch, agent communication, and timeout behaviour.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins.comms_core.helpers.bridge_base import (
    BridgeConfig,
    CommunicationBridge,
    InboundMessage,
    NormalisedAttachment,
    OutboundMessage,
)


# ---------------------------------------------------------------------------
# FakeBridge: concrete CommunicationBridge for testing
# ---------------------------------------------------------------------------

class FakeBridge(CommunicationBridge):
    """Concrete bridge subclass that records calls instead of hitting a network."""

    def __init__(self, config: BridgeConfig | None = None):
        super().__init__(config or BridgeConfig())
        self.sent_texts: list[dict] = []
        self.sent_voices: list[dict] = []
        self.typing_indicators: list[dict] = []

    @property
    def platform_name(self) -> str:
        return "fake"

    async def start_transport(self) -> None:
        pass

    async def stop_transport(self) -> None:
        pass

    async def send_text(self, chat_id: str, text: str, reply_to: str | None = None) -> None:
        self.sent_texts.append({"chat_id": chat_id, "text": text, "reply_to": reply_to})

    async def send_voice(self, chat_id: str, audio_bytes: bytes, reply_to: str | None = None) -> None:
        self.sent_voices.append({"chat_id": chat_id, "audio_bytes": audio_bytes, "reply_to": reply_to})

    async def send_typing_indicator(self, chat_id: str, action: str = "typing") -> None:
        self.typing_indicators.append({"chat_id": chat_id, "action": action})

    async def download_attachment(self, platform_file_ref):
        return NormalisedAttachment(filename="file.txt", content_bytes=b"data", mime_type="text/plain")


def _make_message(text: str = "hello", user_id: str = "u1", chat_id: str = "c1", msg_id: str = "m1") -> InboundMessage:
    return InboundMessage(
        platform="fake",
        platform_chat_id=chat_id,
        platform_user_id=user_id,
        platform_message_id=msg_id,
        text=text,
    )


# ---------------------------------------------------------------------------
# NormalisedAttachment tests
# ---------------------------------------------------------------------------

class TestNormalisedAttachment:
    def test_save_to_disk_creates_file(self, tmp_path):
        att = NormalisedAttachment(filename="test.txt", content_bytes=b"hello", mime_type="text/plain")
        path = att.save_to_disk(str(tmp_path))
        assert os.path.exists(path)
        assert Path(path).read_bytes() == b"hello"
        assert os.path.basename(path) == "test.txt"

    def test_save_to_disk_sanitizes_path_traversal(self, tmp_path):
        att = NormalisedAttachment(filename="../../etc/passwd", content_bytes=b"nope", mime_type="text/plain")
        path = att.save_to_disk(str(tmp_path))
        # Should be saved inside tmp_path, not in ../../etc/
        assert Path(path).parent == tmp_path
        assert os.path.basename(path) == "passwd"

    def test_save_to_disk_empty_filename_fallback(self, tmp_path):
        att = NormalisedAttachment(filename="", content_bytes=b"data", mime_type="text/plain")
        path = att.save_to_disk(str(tmp_path))
        assert os.path.basename(path) == "attachment"

    def test_save_to_disk_dot_filename_fallback(self, tmp_path):
        att = NormalisedAttachment(filename=".", content_bytes=b"data", mime_type="text/plain")
        path = att.save_to_disk(str(tmp_path))
        assert os.path.basename(path) == "attachment"

    def test_save_to_disk_dotdot_filename_fallback(self, tmp_path):
        att = NormalisedAttachment(filename="..", content_bytes=b"data", mime_type="text/plain")
        path = att.save_to_disk(str(tmp_path))
        assert os.path.basename(path) == "attachment"

    def test_save_to_disk_creates_upload_dir(self, tmp_path):
        upload_dir = str(tmp_path / "nested" / "dir")
        att = NormalisedAttachment(filename="file.bin", content_bytes=b"\x00\x01", mime_type="application/octet-stream")
        path = att.save_to_disk(upload_dir)
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# Access control tests
# ---------------------------------------------------------------------------

class TestAccessControl:
    @pytest.mark.asyncio
    async def test_allowed_users_empty_allows_everyone(self):
        bridge = FakeBridge(BridgeConfig(allowed_users=set()))
        msg = _make_message(text="/id", user_id="anyone")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 1  # /id responded

    @pytest.mark.asyncio
    async def test_allowed_users_rejects_unauthorised(self):
        bridge = FakeBridge(BridgeConfig(allowed_users={"allowed_user"}))
        msg = _make_message(text="hello", user_id="intruder")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 0
        assert len(bridge.typing_indicators) == 0

    @pytest.mark.asyncio
    async def test_allowed_users_accepts_authorised(self):
        """Authorised user should pass access control and reach command handler."""
        bridge = FakeBridge(BridgeConfig(allowed_users={"u1"}))
        msg = _make_message(text="/id", user_id="u1")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 1


# ---------------------------------------------------------------------------
# Command handling tests
# ---------------------------------------------------------------------------

class TestCommandHandling:
    @pytest.mark.asyncio
    async def test_start_command(self):
        bridge = FakeBridge()
        msg = _make_message(text="/start")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 1
        assert "Agent Zero" in bridge.sent_texts[0]["text"]

    @pytest.mark.asyncio
    async def test_help_command(self):
        bridge = FakeBridge()
        msg = _make_message(text="/help")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 1
        assert "/reset" in bridge.sent_texts[0]["text"]

    @pytest.mark.asyncio
    async def test_reset_command(self, monkeypatch):
        bridge = FakeBridge()
        # Pre-populate a mapping
        bridge._chat_map.set("c1", "ctx-123", "u1")
        assert bridge._chat_map.get_context_id("c1") == "ctx-123"

        msg = _make_message(text="/reset")
        await bridge.handle_inbound(msg)

        assert bridge._chat_map.get_context_id("c1") is None
        assert "reset" in bridge.sent_texts[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_status_command_no_context(self):
        bridge = FakeBridge()
        bridge._running = True
        msg = _make_message(text="/status")
        await bridge.handle_inbound(msg)
        text = bridge.sent_texts[0]["text"]
        assert "running" in text
        assert "fake" in text

    @pytest.mark.asyncio
    async def test_status_command_with_context(self):
        bridge = FakeBridge()
        bridge._running = True
        bridge._chat_map.set("c1", "ctx-abc", "u1")
        msg = _make_message(text="/status")
        await bridge.handle_inbound(msg)
        assert "ctx-abc" in bridge.sent_texts[0]["text"]

    @pytest.mark.asyncio
    async def test_id_command(self):
        bridge = FakeBridge()
        msg = _make_message(text="/id", user_id="user42", chat_id="chat99")
        await bridge.handle_inbound(msg)
        text = bridge.sent_texts[0]["text"]
        assert "user42" in text
        assert "chat99" in text

    @pytest.mark.asyncio
    async def test_unrecognised_command_passes_through(self, monkeypatch):
        """Unknown /commands should pass through to the agent, not be swallowed."""
        bridge = FakeBridge()
        # Mock _communicate_with_agent to track that it was called
        communicate_called = False

        async def fake_communicate(message, context_id, typing_action):
            nonlocal communicate_called
            communicate_called = True
            return "agent response"

        monkeypatch.setattr(bridge, "_communicate_with_agent", fake_communicate)

        msg = _make_message(text="/unknown_cmd")
        await bridge.handle_inbound(msg)
        assert communicate_called

    @pytest.mark.asyncio
    async def test_empty_message_ignored(self):
        bridge = FakeBridge()
        msg = _make_message(text="   ")
        await bridge.handle_inbound(msg)
        assert len(bridge.sent_texts) == 0


# ---------------------------------------------------------------------------
# Outbound dispatch tests
# ---------------------------------------------------------------------------

class TestOutboundDispatch:
    @pytest.mark.asyncio
    async def test_text_outbound_routes_to_send_text(self):
        bridge = FakeBridge()
        outbound = OutboundMessage(platform_chat_id="c1", text="hello")
        await bridge.handle_outbound(outbound)
        assert len(bridge.sent_texts) == 1
        assert bridge.sent_texts[0]["text"] == "hello"
        assert len(bridge.sent_voices) == 0

    @pytest.mark.asyncio
    async def test_voice_outbound_routes_to_send_voice(self):
        bridge = FakeBridge()
        outbound = OutboundMessage(
            platform_chat_id="c1", text="", voice_audio_bytes=b"audio_data"
        )
        await bridge.handle_outbound(outbound)
        assert len(bridge.sent_voices) == 1
        assert bridge.sent_voices[0]["audio_bytes"] == b"audio_data"
        assert len(bridge.sent_texts) == 0

    @pytest.mark.asyncio
    async def test_reply_to_forwarded(self):
        bridge = FakeBridge()
        outbound = OutboundMessage(
            platform_chat_id="c1", text="reply", reply_to_message_id="m5"
        )
        await bridge.handle_outbound(outbound)
        assert bridge.sent_texts[0]["reply_to"] == "m5"


# ---------------------------------------------------------------------------
# Agent communication tests
# ---------------------------------------------------------------------------

class FakeDeferredTask:
    """Controllable stand-in for DeferredTask."""

    def __init__(self, result_value: str = "agent says hi", ready: bool = True):
        self._result = result_value
        self._ready = ready

    def is_ready(self) -> bool:
        return self._ready

    async def result(self):
        return self._result


class TestAgentCommunication:
    @pytest.mark.asyncio
    async def test_timeout_sends_error_message(self, monkeypatch):
        bridge = FakeBridge(BridgeConfig(message_timeout=1))

        async def stuck_communicate(message, context_id, typing_action):
            raise asyncio.TimeoutError()

        monkeypatch.setattr(bridge, "_communicate_with_agent", stuck_communicate)

        msg = _make_message(text="do something slow")
        await bridge.handle_inbound(msg)

        assert len(bridge.sent_texts) == 1
        assert "timed out" in bridge.sent_texts[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_exception_sends_sorry_message(self, monkeypatch):
        bridge = FakeBridge()

        async def broken_communicate(message, context_id, typing_action):
            raise RuntimeError("LLM broke")

        monkeypatch.setattr(bridge, "_communicate_with_agent", broken_communicate)

        msg = _make_message(text="trigger error")
        await bridge.handle_inbound(msg)

        assert len(bridge.sent_texts) == 1
        assert "sorry" in bridge.sent_texts[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_successful_response_sent_with_reply(self, monkeypatch):
        bridge = FakeBridge()

        async def good_communicate(message, context_id, typing_action):
            return "I'm the agent"

        monkeypatch.setattr(bridge, "_communicate_with_agent", good_communicate)

        msg = _make_message(text="hello agent", msg_id="m42")
        await bridge.handle_inbound(msg)

        assert len(bridge.sent_texts) == 1
        assert bridge.sent_texts[0]["text"] == "I'm the agent"
        assert bridge.sent_texts[0]["reply_to"] == "m42"

    @pytest.mark.asyncio
    async def test_empty_response_not_sent(self, monkeypatch):
        bridge = FakeBridge()

        async def empty_communicate(message, context_id, typing_action):
            return ""

        monkeypatch.setattr(bridge, "_communicate_with_agent", empty_communicate)

        msg = _make_message(text="silent agent")
        await bridge.handle_inbound(msg)

        # typing indicator sent, but no text response
        assert len(bridge.typing_indicators) == 1
        assert len(bridge.sent_texts) == 0


# ---------------------------------------------------------------------------
# Start/stop lifecycle tests
# ---------------------------------------------------------------------------

class TestLifecycle:
    @pytest.mark.asyncio
    async def test_start_sets_running(self, monkeypatch):
        bridge = FakeBridge()
        # Patch chat_map.load to avoid filesystem
        monkeypatch.setattr(bridge._chat_map, "load", AsyncMock())
        await bridge.start()
        assert bridge.is_running is True

    @pytest.mark.asyncio
    async def test_start_idempotent(self, monkeypatch):
        bridge = FakeBridge()
        monkeypatch.setattr(bridge._chat_map, "load", AsyncMock())
        await bridge.start()
        await bridge.start()  # second call should be no-op
        assert bridge.is_running is True

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, monkeypatch):
        bridge = FakeBridge()
        monkeypatch.setattr(bridge._chat_map, "load", AsyncMock())
        monkeypatch.setattr(bridge._chat_map, "save", AsyncMock())
        await bridge.start()
        await bridge.stop()
        assert bridge.is_running is False

    def test_active_chats_reflects_mapping(self):
        bridge = FakeBridge()
        assert bridge.active_chats == 0
        bridge._chat_map.set("c1", "ctx1")
        assert bridge.active_chats == 1
