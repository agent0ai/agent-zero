"""LINE channel adapter."""

from __future__ import annotations

import hashlib
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
        return ChannelFactory.register("line")(cls)
    return cls


@_register
class LineAdapter(ChannelBridge):
    """Adapter for LINE via Messaging API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        events = raw_payload.get("events", [])
        event = events[0] if events else raw_payload
        source = event.get("source", {})
        message = event.get("message", {})
        return NormalizedMessage(
            id=message.get("id", ""),
            channel="line",
            sender_id=source.get("userId", ""),
            sender_name=source.get("userId", ""),
            text=message.get("text", ""),
            timestamp=float(event.get("timestamp", time.time() * 1000)) / 1000.0,
            metadata={
                "reply_token": event.get("replyToken", ""),
                "source_type": source.get("type", ""),
                "group_id": source.get("groupId", ""),
                "message_type": message.get("type", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to https://api.line.me/v2/bot/message/push
        return {"to": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        channel_secret = self.config.get("line_channel_secret", "")
        signature = headers.get("X-Line-Signature", "")
        if not channel_secret or not signature:
            return False
        import base64

        digest = hmac.new(channel_secret.encode(), body, hashlib.sha256).digest()
        computed = base64.b64encode(digest).decode()
        return hmac.compare_digest(computed, signature)

    async def connect(self) -> None:
        # TODO: verify line_channel_access_token with LINE API
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
