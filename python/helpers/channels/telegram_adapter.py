"""Telegram channel adapter."""

from __future__ import annotations

import hmac
import time
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelStatus, NormalizedMessage

try:
    from python.helpers.channel_factory import ChannelFactory
except ImportError:  # pragma: no cover
    ChannelFactory = None  # type: ignore[assignment,misc]


def _register(cls: type) -> type:
    if ChannelFactory is not None:
        return ChannelFactory.register("telegram")(cls)
    return cls


@_register
class TelegramAdapter(ChannelBridge):
    """Adapter for the Telegram messaging platform."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        message = raw_payload.get("message", raw_payload)
        from_user = message.get("from", {})
        chat = message.get("chat", {})
        return NormalizedMessage(
            id=str(message.get("message_id", "")),
            channel="telegram",
            sender_id=str(from_user.get("id", "")),
            sender_name=from_user.get("username", from_user.get("first_name", "")),
            text=message.get("text", ""),
            timestamp=float(message.get("date", time.time())),
            metadata={
                "chat_id": str(chat.get("id", "")),
                "chat_type": chat.get("type", ""),
                "update_id": raw_payload.get("update_id"),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        return {"chat_id": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        secret_token = self.config.get("secret_token", "")
        header_token = headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret_token:
            # No secret configured -- accept all (development mode)
            return True
        return hmac.compare_digest(secret_token, header_token)

    async def connect(self) -> None:
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
