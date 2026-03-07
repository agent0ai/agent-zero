"""IRC channel adapter."""

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
        return ChannelFactory.register("irc")(cls)
    return cls


@_register
class IrcAdapter(ChannelBridge):
    """Adapter for IRC using the irc library."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        return NormalizedMessage(
            id=raw_payload.get("id", ""),
            channel="irc",
            sender_id=raw_payload.get("nick", ""),
            sender_name=raw_payload.get("nick", ""),
            text=raw_payload.get("text", raw_payload.get("message", "")),
            timestamp=float(raw_payload.get("timestamp", time.time())),
            metadata={
                "irc_channel": raw_payload.get("channel", ""),
                "command": raw_payload.get("command", "PRIVMSG"),
                "host": raw_payload.get("host", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: send PRIVMSG via irc.client connection
        return {"target": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # IRC does not use webhooks; messages arrive via persistent socket.
        return True

    async def connect(self) -> None:
        # TODO: connect to irc_server:irc_port, set nickname, join irc_channels
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        # TODO: part channels, close socket connection
        self.status = ChannelStatus.DISCONNECTED
