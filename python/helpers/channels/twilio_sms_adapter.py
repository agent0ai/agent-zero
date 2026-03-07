"""Twilio SMS channel adapter."""

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
        return ChannelFactory.register("twilio_sms")(cls)
    return cls


@_register
class TwilioSmsAdapter(ChannelBridge):
    """Adapter for Twilio SMS via REST API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        return NormalizedMessage(
            id=raw_payload.get("MessageSid", ""),
            channel="twilio_sms",
            sender_id=raw_payload.get("From", ""),
            sender_name=raw_payload.get("From", ""),
            text=raw_payload.get("Body", ""),
            timestamp=time.time(),
            metadata={
                "to": raw_payload.get("To", ""),
                "num_media": raw_payload.get("NumMedia", "0"),
                "sms_status": raw_payload.get("SmsStatus", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json
        return {"to": target_id, "body": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        auth_token = self.config.get("twilio_auth_token", "")
        signature = headers.get("X-Twilio-Signature", "")
        # TODO: reconstruct URL + sorted POST params, HMAC-SHA1, base64 compare
        return bool(auth_token and signature)

    async def connect(self) -> None:
        # TODO: verify twilio_account_sid / twilio_auth_token credentials
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
