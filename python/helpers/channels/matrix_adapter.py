"""Matrix channel adapter."""

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
        return ChannelFactory.register("matrix")(cls)
    return cls


@_register
class MatrixAdapter(ChannelBridge):
    """Adapter for Matrix via Client-Server API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        content = raw_payload.get("content", {})
        return NormalizedMessage(
            id=raw_payload.get("event_id", ""),
            channel="matrix",
            sender_id=raw_payload.get("sender", ""),
            sender_name=raw_payload.get("sender", ""),
            text=content.get("body", ""),
            timestamp=float(raw_payload.get("origin_server_ts", time.time() * 1000)) / 1000.0,
            metadata={
                "room_id": raw_payload.get("room_id", ""),
                "event_type": raw_payload.get("type", ""),
                "msgtype": content.get("msgtype", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: PUT to /_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txnId}
        return {"room_id": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # Matrix Application Services use hs_token for authentication
        hs_token = self.config.get("matrix_hs_token", "")
        if not hs_token:
            return True
        auth = headers.get("Authorization", "")
        return auth == f"Bearer {hs_token}"

    async def connect(self) -> None:
        # TODO: verify access token against matrix_homeserver_url
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
