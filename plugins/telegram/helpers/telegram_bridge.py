"""
Telegram transport layer using aiogram 3.x.

Implements CommunicationBridge for Telegram Bot API.
Handles text messages, document/photo attachments, and bot commands.
Voice note support is deferred to Sprint 2.
"""

import asyncio
import logging
import os
import threading
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction

from plugins.comms_core.helpers.bridge_base import (
    CommunicationBridge,
    BridgeConfig,
    InboundMessage,
    NormalisedAttachment,
)
from plugins.comms_core.helpers import bridge_registry


def _load_config() -> BridgeConfig:
    """Resolve configuration with priority: Settings UI -> env vars -> defaults.

    TEMPORARY: When plugin-scoped settings land (Phase 2), this will read
    from get_plugin_settings("telegram") instead of the core settings dataclass.
    """
    from python.helpers import settings as a0_settings

    s = a0_settings.get_settings()

    # Allowed users: settings UI field or env var, comma-separated
    allowed_raw = s.get("telegram_allowed_chat_ids", "") or os.environ.get(
        "TELEGRAM_ALLOWED_CHAT_IDS", ""
    )
    allowed = {x.strip() for x in allowed_raw.split(",") if x.strip()}

    return BridgeConfig(
        default_project=(
            s.get("telegram_default_project", "")
            or os.environ.get("TELEGRAM_DEFAULT_PROJECT", "")
        ),
        context_lifetime_hours=int(
            s.get("telegram_context_lifetime", 0)
            or os.environ.get("TELEGRAM_CONTEXT_LIFETIME", "24")
        ),
        voice_reply_mode=(
            s.get("telegram_voice_reply_mode", "")
            or os.environ.get("TELEGRAM_VOICE_REPLY_MODE", "text")
        ),
        allowed_users=allowed,
        message_timeout=int(
            s.get("telegram_message_timeout", 0)
            or os.environ.get("TELEGRAM_MESSAGE_TIMEOUT", "300")
        ),
    )


def _get_bot_token() -> str:
    """Get bot token with priority: secrets manager -> env var."""
    from python.helpers.secrets import get_default_secrets_manager

    secrets = get_default_secrets_manager().load_secrets()
    token = secrets.get("TELEGRAM_BOT_TOKEN", "") or os.environ.get(
        "TELEGRAM_BOT_TOKEN", ""
    )
    return token


class TelegramBridge(CommunicationBridge):
    """Telegram transport layer using aiogram 3.x."""

    _instance: "TelegramBridge | None" = None
    _instance_lock = threading.RLock()

    def __init__(self):
        config = _load_config()
        super().__init__(config)

        token = _get_bot_token()
        if not token:
            raise ValueError(
                "Telegram bot token not configured. Set it in Settings -> Secrets "
                "as TELEGRAM_BOT_TOKEN or via TELEGRAM_BOT_TOKEN environment variable."
            )
        self._token = token
        self._bot = Bot(token=token)
        self._dp = Dispatcher()
        self._polling_task: asyncio.Task | None = None
        self._register_handlers()

    @classmethod
    def get_instance(cls) -> "TelegramBridge":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = TelegramBridge()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Used for hot-reload."""
        with cls._instance_lock:
            cls._instance = None

    def reload_config(self) -> None:
        """Reload configuration from settings/env vars. Called on hot-reload."""
        self.config = _load_config()
        # Check if token changed — requires recreating the Bot instance
        new_token = _get_bot_token()
        if new_token and new_token != self._token:
            self._token = new_token
            self._bot = Bot(token=new_token)
            self.logger.info("Telegram bot token changed, recreated Bot instance")

    @property
    def platform_name(self) -> str:
        return "telegram"

    def _register_handlers(self) -> None:
        """Register aiogram message handlers."""

        @self._dp.message()
        async def on_message(message: types.Message) -> None:
            # Build normalised inbound message
            text = message.text or message.caption or ""
            attachments: list[NormalisedAttachment] = []

            # Handle document attachments
            if message.document:
                att = await self._download_document(message.document)
                if att:
                    attachments.append(att)

            # Handle photo attachments (take largest size)
            if message.photo:
                photo = message.photo[-1]
                att = await self._download_photo(photo)
                if att:
                    attachments.append(att)

            inbound = InboundMessage(
                platform="telegram",
                platform_chat_id=str(message.chat.id),
                platform_user_id=(
                    str(message.from_user.id) if message.from_user else ""
                ),
                platform_message_id=str(message.message_id),
                text=text,
                attachments=attachments,
                raw_event=message,
            )

            await self.handle_inbound(inbound)

    async def start_transport(self) -> None:
        """Start aiogram polling."""
        bridge_registry.register(self)
        self.logger.info("Starting Telegram bot polling")
        self._polling_task = asyncio.create_task(
            self._dp.start_polling(self._bot, handle_signals=False)
        )

    async def stop_transport(self) -> None:
        """Stop aiogram polling."""
        bridge_registry.unregister("telegram")
        await self._dp.stop_polling()
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        await self._bot.close()
        await self._bot.session.close()

    async def send_text(
        self, chat_id: str, text: str, reply_to: str | None = None
    ) -> None:
        """Send text message, splitting if needed (Telegram 4096 char limit)."""
        max_len = 4096
        chunks = [text[i : i + max_len] for i in range(0, len(text), max_len)]
        for i, chunk in enumerate(chunks):
            kwargs: dict = {"chat_id": int(chat_id), "text": chunk}
            if reply_to and i == 0:
                kwargs["reply_to_message_id"] = int(reply_to)
            await self._bot.send_message(**kwargs)

    async def send_voice(
        self, chat_id: str, audio_bytes: bytes, reply_to: str | None = None
    ) -> None:
        """Send OGG/Opus voice note. (Sprint 2)"""
        voice_file = types.BufferedInputFile(audio_bytes, filename="voice.ogg")
        kwargs: dict = {"chat_id": int(chat_id), "voice": voice_file}
        if reply_to:
            kwargs["reply_to_message_id"] = int(reply_to)
        await self._bot.send_voice(**kwargs)

    async def send_typing_indicator(
        self, chat_id: str, action: str = "typing"
    ) -> None:
        """Send chat action indicator to Telegram."""
        action_map = {
            "typing": ChatAction.TYPING,
            "record_voice": ChatAction.RECORD_VOICE,
            "upload_document": ChatAction.UPLOAD_DOCUMENT,
        }
        tg_action = action_map.get(action, ChatAction.TYPING)
        await self._bot.send_chat_action(chat_id=int(chat_id), action=tg_action)

    async def download_attachment(
        self, platform_file_ref: Any
    ) -> NormalisedAttachment:
        """Download a file from Telegram."""
        doc = platform_file_ref
        content = await self._download_file(doc.file_id)
        return NormalisedAttachment(
            filename=getattr(doc, "file_name", None) or "file",
            content_bytes=content,
            mime_type=getattr(doc, "mime_type", None) or "application/octet-stream",
        )

    async def _download_file(self, file_id: str) -> bytes:
        """Download a file from Telegram by file_id."""
        file = await self._bot.get_file(file_id)
        bio = await self._bot.download_file(file.file_path)
        return bio.read()

    async def _download_document(
        self, doc: types.Document
    ) -> NormalisedAttachment | None:
        try:
            content = await self._download_file(doc.file_id)
            return NormalisedAttachment(
                filename=doc.file_name or "document",
                content_bytes=content,
                mime_type=doc.mime_type or "application/octet-stream",
            )
        except Exception as e:
            self.logger.error(f"Failed to download document: {e}")
            return None

    async def _download_photo(
        self, photo: types.PhotoSize
    ) -> NormalisedAttachment | None:
        try:
            content = await self._download_file(photo.file_id)
            return NormalisedAttachment(
                filename="photo.jpg",
                content_bytes=content,
                mime_type="image/jpeg",
            )
        except Exception as e:
            self.logger.error(f"Failed to download photo: {e}")
            return None
