"""Google Chat channel adapter."""

from __future__ import annotations

import time
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelStatus, NormalizedMessage

try:
    from python.helpers.channel_factory import ChannelFactory
except ImportError:  # pragma: no cover
    ChannelFactory = None  # type: ignore[assignment,misc]


def _register(cls: type) -> type:
    if ChannelFactory is not None:
        return ChannelFactory.register("google_chat")(cls)
    return cls


@_register
class GoogleChatAdapter(ChannelBridge):
    """Adapter for Google Chat via Google Workspace API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        message = raw_payload.get("message", raw_payload)
        sender = message.get("sender", {})
        space = raw_payload.get("space", message.get("space", {}))
        return NormalizedMessage(
            id=message.get("name", ""),
            channel="google_chat",
            sender_id=sender.get("name", ""),
            sender_name=sender.get("displayName", ""),
            text=message.get("text", message.get("argumentText", "")),
            timestamp=float(message.get("createTime", time.time())),
            metadata={
                "space_name": space.get("name", ""),
                "space_type": space.get("type", ""),
                "thread_name": message.get("thread", {}).get("name", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to Google Chat API spaces/{space}/messages
        return {"space": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # TODO: validate Google-issued Bearer token in Authorization header
        token = headers.get("Authorization", "")
        # In production, verify JWT against Google's public keys
        return bool(token)

    async def connect(self) -> None:
        # TODO: authenticate with google_chat_credentials_json service account
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
