"""Email channel adapter (IMAP/SMTP)."""

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
        return ChannelFactory.register("email")(cls)
    return cls


@_register
class EmailAdapter(ChannelBridge):
    """Adapter for Email via IMAP (receive) and SMTP (send)."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        return NormalizedMessage(
            id=raw_payload.get("message_id", ""),
            channel="email",
            sender_id=raw_payload.get("from", ""),
            sender_name=raw_payload.get("from_name", raw_payload.get("from", "")),
            text=raw_payload.get("body", raw_payload.get("text", "")),
            timestamp=float(raw_payload.get("date", time.time())),
            metadata={
                "subject": raw_payload.get("subject", ""),
                "to": raw_payload.get("to", ""),
                "cc": raw_payload.get("cc", ""),
                "in_reply_to": raw_payload.get("in_reply_to", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: connect to email_smtp_host, authenticate, send via smtplib
        subject = kwargs.get("subject", "Agent Jumbo Message")
        return {"to": target_id, "subject": subject, "body": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # Email does not use webhooks; IMAP polling is used instead.
        # If an inbound email webhook service is configured, validate here.
        return True

    async def connect(self) -> None:
        # TODO: test IMAP and SMTP connectivity with configured credentials
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        # TODO: close any open IMAP connections
        self.status = ChannelStatus.DISCONNECTED
