"""Signal channel adapter."""

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
        return ChannelFactory.register("signal")(cls)
    return cls


@_register
class SignalAdapter(ChannelBridge):
    """Adapter for the Signal messaging platform via signal-cli REST API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        envelope = raw_payload.get("envelope", raw_payload)
        data_msg = envelope.get("dataMessage", {})
        return NormalizedMessage(
            id=str(data_msg.get("timestamp", "")),
            channel="signal",
            sender_id=envelope.get("source", ""),
            sender_name=envelope.get("sourceName", envelope.get("source", "")),
            text=data_msg.get("message", ""),
            timestamp=float(data_msg.get("timestamp", time.time())) / 1000.0,
            metadata={
                "group_id": data_msg.get("groupInfo", {}).get("groupId", ""),
                "source_device": envelope.get("sourceDevice", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to {signal_api_url}/v2/send with JSON body
        return {"recipient": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # signal-cli REST API does not natively sign webhooks;
        # rely on network-level auth or a shared token header.
        secret = self.config.get("signal_webhook_secret", "")
        if not secret:
            return True
        header_token = headers.get("X-Signal-Secret", "")
        return hmac.compare_digest(secret, header_token)

    async def connect(self) -> None:
        # TODO: verify signal_api_url reachability and phone registration
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
