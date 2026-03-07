"""Viber channel adapter."""

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
        return ChannelFactory.register("viber")(cls)
    return cls


@_register
class ViberAdapter(ChannelBridge):
    """Adapter for Viber via Bot API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        sender = raw_payload.get("sender", {})
        message = raw_payload.get("message", {})
        return NormalizedMessage(
            id=raw_payload.get("message_token", str(raw_payload.get("timestamp", ""))),
            channel="viber",
            sender_id=sender.get("id", ""),
            sender_name=sender.get("name", ""),
            text=message.get("text", ""),
            timestamp=float(raw_payload.get("timestamp", time.time() * 1000)) / 1000.0,
            metadata={
                "event_type": raw_payload.get("event", ""),
                "message_type": message.get("type", ""),
                "avatar": sender.get("avatar", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to https://chatapi.viber.com/pa/send_message
        return {"receiver": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        auth_token = self.config.get("viber_auth_token", "")
        signature = headers.get("X-Viber-Content-Signature", "")
        if not auth_token or not signature:
            return False
        computed = hmac.new(auth_token.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    async def connect(self) -> None:
        # TODO: POST to https://chatapi.viber.com/pa/set_webhook
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        # TODO: remove webhook via Viber API
        self.status = ChannelStatus.DISCONNECTED
