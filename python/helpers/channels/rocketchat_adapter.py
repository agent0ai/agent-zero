"""Rocket.Chat channel adapter."""

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
        return ChannelFactory.register("rocketchat")(cls)
    return cls


@_register
class RocketChatAdapter(ChannelBridge):
    """Adapter for Rocket.Chat via REST API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        msg = raw_payload.get("message", raw_payload) if "message" in raw_payload else raw_payload
        user = msg.get("u", {})
        return NormalizedMessage(
            id=msg.get("_id", ""),
            channel="rocketchat",
            sender_id=user.get("_id", ""),
            sender_name=user.get("username", user.get("name", "")),
            text=msg.get("msg", ""),
            timestamp=float(msg.get("ts", {}).get("$date", time.time() * 1000)) / 1000.0
            if isinstance(msg.get("ts"), dict)
            else time.time(),
            metadata={
                "rid": msg.get("rid", ""),
                "channel_name": raw_payload.get("channel_name", ""),
                "msg_type": msg.get("t", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to {rocketchat_url}/api/v1/chat.sendMessage
        return {"rid": target_id, "msg": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        token = self.config.get("rocketchat_webhook_token", "")
        if not token:
            return True
        header_token = headers.get("X-Rocketchat-Token", "")
        return hmac.compare_digest(token, header_token)

    async def connect(self) -> None:
        # TODO: authenticate with rocketchat_url using user_id + auth_token
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
