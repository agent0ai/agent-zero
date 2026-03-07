"""Microsoft Teams channel adapter."""

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
        return ChannelFactory.register("teams")(cls)
    return cls


@_register
class TeamsAdapter(ChannelBridge):
    """Adapter for Microsoft Teams via Bot Framework."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        from_user = raw_payload.get("from", {})
        conversation = raw_payload.get("conversation", {})
        return NormalizedMessage(
            id=raw_payload.get("id", ""),
            channel="teams",
            sender_id=from_user.get("id", ""),
            sender_name=from_user.get("name", ""),
            text=raw_payload.get("text", ""),
            timestamp=float(raw_payload.get("timestamp", time.time())),
            metadata={
                "conversation_id": conversation.get("id", ""),
                "tenant_id": conversation.get("tenantId", ""),
                "activity_type": raw_payload.get("type", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to Bot Framework /v3/conversations/{id}/activities
        return {"conversation_id": target_id, "text": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # TODO: validate JWT Bearer token from Bot Framework
        auth_header = headers.get("Authorization", "")
        # In production, validate the JWT against Microsoft's OpenID metadata
        return auth_header.startswith("Bearer ")

    async def connect(self) -> None:
        # TODO: acquire OAuth token using teams_app_id / teams_app_password
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
