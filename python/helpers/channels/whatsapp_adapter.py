"""WhatsApp channel adapter."""

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
        return ChannelFactory.register("whatsapp")(cls)
    return cls


@_register
class WhatsAppAdapter(ChannelBridge):
    """Adapter for the WhatsApp Business API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        entry = (raw_payload.get("entry", [{}]) or [{}])[0]
        changes = (entry.get("changes", [{}]) or [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [{}])
        msg = messages[0] if messages else {}
        contacts = value.get("contacts", [{}])
        contact = contacts[0] if contacts else {}

        return NormalizedMessage(
            id=msg.get("id", ""),
            channel="whatsapp",
            sender_id=msg.get("from", ""),
            sender_name=contact.get("profile", {}).get("name", ""),
            text=msg.get("text", {}).get("body", "") if isinstance(msg.get("text"), dict) else msg.get("text", ""),
            timestamp=float(msg.get("timestamp", time.time())),
            metadata={
                "phone_number_id": value.get("metadata", {}).get("phone_number_id", ""),
                "message_type": msg.get("type", "text"),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        return {"to": target_id, "text": text, "sent": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        app_secret = self.config.get("app_secret", "")
        signature = headers.get("X-Hub-Signature-256", "")
        if not all([app_secret, signature]):
            return False
        try:
            expected = "sha256=" + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False

    async def connect(self) -> None:
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
