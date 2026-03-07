"""Mastodon channel adapter."""

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
        return ChannelFactory.register("mastodon")(cls)
    return cls


@_register
class MastodonAdapter(ChannelBridge):
    """Adapter for Mastodon via Mastodon.py / REST API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        account = raw_payload.get("account", {})
        return NormalizedMessage(
            id=str(raw_payload.get("id", "")),
            channel="mastodon",
            sender_id=str(account.get("id", "")),
            sender_name=account.get("username", account.get("acct", "")),
            text=raw_payload.get("content", ""),
            timestamp=float(raw_payload.get("created_at_epoch", time.time())),
            metadata={
                "visibility": raw_payload.get("visibility", ""),
                "in_reply_to_id": raw_payload.get("in_reply_to_id", ""),
                "url": raw_payload.get("url", ""),
                "spoiler_text": raw_payload.get("spoiler_text", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to {mastodon_instance_url}/api/v1/statuses
        visibility = kwargs.get("visibility", "direct")
        return {"in_reply_to_id": target_id, "status": text, "visibility": visibility, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        # Mastodon streaming uses WebSockets; webhook verification is optional.
        secret = self.config.get("mastodon_webhook_secret", "")
        if not secret:
            return True
        signature = headers.get("X-Hub-Signature", "")
        if not signature:
            return False
        computed = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    async def connect(self) -> None:
        # TODO: verify mastodon_access_token against /api/v1/accounts/verify_credentials
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
