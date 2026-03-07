"""Slack channel adapter."""

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
        return ChannelFactory.register("slack")(cls)
    return cls


@_register
class SlackAdapter(ChannelBridge):
    """Adapter for the Slack messaging platform."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        event = raw_payload.get("event", raw_payload)
        return NormalizedMessage(
            id=event.get("client_msg_id", event.get("ts", "")),
            channel="slack",
            sender_id=event.get("user", ""),
            sender_name=event.get("user", ""),
            text=event.get("text", ""),
            timestamp=float(event.get("ts", time.time())),
            metadata={
                "channel_id": event.get("channel", ""),
                "team_id": raw_payload.get("team_id", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        return {"channel": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        signing_secret = self.config.get("signing_secret", "")
        timestamp = headers.get("X-Slack-Request-Timestamp", "")
        signature = headers.get("X-Slack-Signature", "")
        if not all([signing_secret, timestamp, signature]):
            return False
        try:
            base = f"v0:{timestamp}:{body.decode()}".encode()
            computed = "v0=" + hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
            return hmac.compare_digest(computed, signature)
        except Exception:
            return False

    async def connect(self) -> None:
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
