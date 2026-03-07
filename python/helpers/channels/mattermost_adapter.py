"""Mattermost channel adapter."""

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
        return ChannelFactory.register("mattermost")(cls)
    return cls


@_register
class MattermostAdapter(ChannelBridge):
    """Adapter for Mattermost via REST API."""

    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        post = raw_payload.get("post", raw_payload)
        if isinstance(post, str):
            import json

            try:
                post = json.loads(post)
            except (json.JSONDecodeError, TypeError):
                post = raw_payload
        return NormalizedMessage(
            id=post.get("id", ""),
            channel="mattermost",
            sender_id=post.get("user_id", ""),
            sender_name=raw_payload.get("user_name", post.get("user_id", "")),
            text=post.get("message", ""),
            timestamp=float(post.get("create_at", time.time() * 1000)) / 1000.0,
            metadata={
                "channel_id": post.get("channel_id", ""),
                "team_id": raw_payload.get("team_id", ""),
                "trigger_word": raw_payload.get("trigger_word", ""),
            },
            raw=raw_payload,
        )

    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        # TODO: POST to {mattermost_url}/api/v4/posts
        return {"channel_id": target_id, "message": text, "ok": True}

    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        token = self.config.get("mattermost_webhook_token", "")
        if not token:
            return True
        # Mattermost outgoing webhooks include a token field in the payload
        import json

        try:
            payload = json.loads(body)
            return hmac.compare_digest(token, payload.get("token", ""))
        except Exception:
            return False

    async def connect(self) -> None:
        # TODO: verify mattermost_token against {mattermost_url}/api/v4/users/me
        self.status = ChannelStatus.CONNECTED

    async def disconnect(self) -> None:
        self.status = ChannelStatus.DISCONNECTED
