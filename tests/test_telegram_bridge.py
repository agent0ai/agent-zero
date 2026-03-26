"""
Tests for plugins/telegram/helpers/telegram_bridge.py

Covers singleton pattern, config loading, token reload,
message chunking, and send_text/send_voice behaviour.
All tests run fully offline — no real Telegram API calls.
"""

import asyncio
import sys
import threading
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Fake aiogram stubs (avoid real HTTP)
# ---------------------------------------------------------------------------

class FakeBot:
    """Minimal aiogram.Bot replacement that records calls."""

    def __init__(self, token: str):
        self.token = token
        self.send_message = AsyncMock()
        self.send_voice = AsyncMock()
        self.send_chat_action = AsyncMock()
        self.get_file = AsyncMock()
        self.download_file = AsyncMock()
        self.close = AsyncMock()
        self.session = MagicMock()
        self.session.close = AsyncMock()


class FakeDispatcher:
    """Minimal aiogram.Dispatcher replacement."""

    def __init__(self, **kwargs):
        self._handlers = {}
        self.start_polling = AsyncMock()
        self.stop_polling = AsyncMock()

    def message(self, *args, **kwargs):
        """Decorator stub that captures the handler."""
        def decorator(func):
            self._handlers["message"] = func
            return func
        return decorator


@pytest.fixture(autouse=True)
def patch_aiogram(monkeypatch):
    """Replace aiogram.Bot and Dispatcher with fakes globally."""
    monkeypatch.setattr(
        "plugins.telegram.helpers.telegram_bridge.Bot", FakeBot
    )
    monkeypatch.setattr(
        "plugins.telegram.helpers.telegram_bridge.Dispatcher", FakeDispatcher
    )


@pytest.fixture(autouse=True)
def reset_singleton():
    """Clear singleton before and after each test."""
    from plugins.telegram.helpers.telegram_bridge import TelegramBridge
    TelegramBridge.reset_instance()
    yield
    TelegramBridge.reset_instance()


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _patch_config(monkeypatch, settings: dict | None = None, token: str = "test-token-123"):
    """Set up monkeypatches for config loading and secrets."""
    s = settings or {}
    monkeypatch.setattr(
        "plugins.telegram.helpers.telegram_bridge._load_config",
        lambda: __import__(
            "plugins.comms_core.helpers.bridge_base", fromlist=["BridgeConfig"]
        ).BridgeConfig(
            allowed_users=set(s.get("allowed", [])),
            message_timeout=s.get("timeout", 300),
        ),
    )
    monkeypatch.setattr(
        "plugins.telegram.helpers.telegram_bridge._get_bot_token",
        lambda: token,
    )


# ---------------------------------------------------------------------------
# Singleton pattern tests
# ---------------------------------------------------------------------------

class TestSingleton:
    def test_get_instance_returns_same_object(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        a = TelegramBridge.get_instance()
        b = TelegramBridge.get_instance()
        assert a is b

    def test_reset_clears_instance(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        a = TelegramBridge.get_instance()
        TelegramBridge.reset_instance()
        b = TelegramBridge.get_instance()
        assert a is not b

    def test_no_token_raises_value_error(self, monkeypatch):
        _patch_config(monkeypatch, token="")
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        with pytest.raises(ValueError, match="[Tt]oken"):
            TelegramBridge()

    def test_platform_name(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()
        assert bridge.platform_name == "telegram"


# ---------------------------------------------------------------------------
# Config loading tests
# ---------------------------------------------------------------------------

class TestConfigLoading:
    def test_config_from_settings(self, monkeypatch):
        """_load_config reads from settings dict."""
        from python.helpers import settings as a0_settings

        fake_settings = {
            "telegram_allowed_chat_ids": "100,200,300",
            "telegram_default_project": "my-project",
            "telegram_context_lifetime": 48,
            "telegram_voice_reply_mode": "both",
            "telegram_message_timeout": 600,
        }
        monkeypatch.setattr(a0_settings, "get_settings", lambda: fake_settings)

        from plugins.telegram.helpers.telegram_bridge import _load_config
        config = _load_config()

        assert config.allowed_users == {"100", "200", "300"}
        assert config.default_project == "my-project"
        assert config.context_lifetime_hours == 48
        assert config.voice_reply_mode == "both"
        assert config.message_timeout == 600

    def test_config_fallback_to_env(self, monkeypatch):
        """_load_config falls back to env vars when settings are empty."""
        from python.helpers import settings as a0_settings
        monkeypatch.setattr(a0_settings, "get_settings", lambda: {})
        monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "42")
        monkeypatch.setenv("TELEGRAM_DEFAULT_PROJECT", "env-proj")
        monkeypatch.setenv("TELEGRAM_CONTEXT_LIFETIME", "12")
        monkeypatch.setenv("TELEGRAM_VOICE_REPLY_MODE", "voice")
        monkeypatch.setenv("TELEGRAM_MESSAGE_TIMEOUT", "120")

        from plugins.telegram.helpers.telegram_bridge import _load_config
        config = _load_config()

        assert config.allowed_users == {"42"}
        assert config.default_project == "env-proj"
        assert config.context_lifetime_hours == 12
        assert config.voice_reply_mode == "voice"
        assert config.message_timeout == 120

    def test_csv_parsing_strips_whitespace(self, monkeypatch):
        from python.helpers import settings as a0_settings
        monkeypatch.setattr(
            a0_settings, "get_settings",
            lambda: {"telegram_allowed_chat_ids": " 10 , 20 , 30 "},
        )

        from plugins.telegram.helpers.telegram_bridge import _load_config
        config = _load_config()
        assert config.allowed_users == {"10", "20", "30"}

    def test_empty_csv_yields_empty_set(self, monkeypatch):
        from python.helpers import settings as a0_settings
        monkeypatch.setattr(
            a0_settings, "get_settings",
            lambda: {"telegram_allowed_chat_ids": ""},
        )
        monkeypatch.delenv("TELEGRAM_ALLOWED_CHAT_IDS", raising=False)

        from plugins.telegram.helpers.telegram_bridge import _load_config
        config = _load_config()
        assert config.allowed_users == set()


# ---------------------------------------------------------------------------
# Reload config tests
# ---------------------------------------------------------------------------

class TestReloadConfig:
    def test_reload_recreates_bot_on_token_change(self, monkeypatch):
        _patch_config(monkeypatch, token="token-A")
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()
        old_bot = bridge._bot
        assert old_bot.token == "token-A"

        # Change token
        monkeypatch.setattr(
            "plugins.telegram.helpers.telegram_bridge._get_bot_token",
            lambda: "token-B",
        )
        bridge.reload_config()

        assert bridge._bot is not old_bot
        assert bridge._bot.token == "token-B"
        assert bridge._token == "token-B"

    def test_reload_keeps_bot_when_token_unchanged(self, monkeypatch):
        _patch_config(monkeypatch, token="same-token")
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()
        old_bot = bridge._bot

        bridge.reload_config()

        assert bridge._bot is old_bot


# ---------------------------------------------------------------------------
# send_text chunking tests
# ---------------------------------------------------------------------------

class TestSendText:
    @pytest.mark.asyncio
    async def test_short_message_single_chunk(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        await bridge.send_text("123", "Hello world")

        bridge._bot.send_message.assert_awaited_once_with(
            chat_id=123, text="Hello world"
        )

    @pytest.mark.asyncio
    async def test_long_message_chunked_at_4096(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        text = "A" * 5000  # exceeds 4096
        await bridge.send_text("456", text)

        calls = bridge._bot.send_message.await_args_list
        assert len(calls) == 2
        assert calls[0].kwargs["text"] == "A" * 4096
        assert calls[1].kwargs["text"] == "A" * 904

    @pytest.mark.asyncio
    async def test_reply_to_only_on_first_chunk(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        text = "B" * 5000
        await bridge.send_text("789", text, reply_to="42")

        calls = bridge._bot.send_message.await_args_list
        assert calls[0].kwargs.get("reply_to_message_id") == 42
        assert "reply_to_message_id" not in calls[1].kwargs

    @pytest.mark.asyncio
    async def test_exact_4096_no_extra_chunk(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        text = "C" * 4096
        await bridge.send_text("100", text)

        assert bridge._bot.send_message.await_count == 1


# ---------------------------------------------------------------------------
# send_voice tests
# ---------------------------------------------------------------------------

class TestSendVoice:
    @pytest.mark.asyncio
    async def test_send_voice_basic(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        await bridge.send_voice("123", b"audio_data")

        bridge._bot.send_voice.assert_awaited_once()
        call_kwargs = bridge._bot.send_voice.await_args.kwargs
        assert call_kwargs["chat_id"] == 123

    @pytest.mark.asyncio
    async def test_send_voice_with_reply_to(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        bridge = TelegramBridge.get_instance()

        await bridge.send_voice("123", b"audio", reply_to="99")

        call_kwargs = bridge._bot.send_voice.await_args.kwargs
        assert call_kwargs["reply_to_message_id"] == 99


# ---------------------------------------------------------------------------
# send_typing_indicator tests
# ---------------------------------------------------------------------------

class TestSendTypingIndicator:
    @pytest.mark.asyncio
    async def test_typing_action(self, monkeypatch):
        _patch_config(monkeypatch)
        from plugins.telegram.helpers.telegram_bridge import TelegramBridge
        from aiogram.enums import ChatAction
        bridge = TelegramBridge.get_instance()

        await bridge.send_typing_indicator("123", "typing")

        bridge._bot.send_chat_action.assert_awaited_once()
        call_kwargs = bridge._bot.send_chat_action.await_args.kwargs
        assert call_kwargs["chat_id"] == 123
        assert call_kwargs["action"] == ChatAction.TYPING
