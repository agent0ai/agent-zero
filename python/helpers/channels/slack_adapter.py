"""Slack channel adapter.

Uses the Slack Web API (chat.postMessage) for sending and HMAC-SHA256
request signing for webhook verification per Slack's v0 signing spec:
https://api.slack.com/authentication/verifying-requests-from-slack
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.request
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelClient


class SlackBridge(ChannelBridge):
    """Slack-specific state and routing."""

    def __init__(self) -> None:
        super().__init__(channel_name="slack", state_dir="data")

    def required_env_vars(self) -> list[str]:
        return ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]


class SlackClient(ChannelClient):
    """Sends messages via the Slack Web API."""

    SLACK_API = "https://slack.com/api"

    def __init__(self) -> None:
        self._token = os.getenv("SLACK_BOT_TOKEN", "")
        self._signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")

    async def send_message(self, recipient_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        token = self._token or os.getenv("SLACK_BOT_TOKEN", "")
        if not token:
            return {"error": "SLACK_BOT_TOKEN not set"}

        payload = {
            "channel": recipient_id,
            "text": text,
        }
        # Optional thread_ts for threading
        thread_ts = kwargs.get("thread_ts")
        if thread_ts:
            payload["thread_ts"] = thread_ts

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.SLACK_API}/chat.postMessage",
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="ignore")
        return json.loads(raw)

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any,
    ) -> bool:
        """Verify Slack request signature (v0).

        Parameters
        ----------
        payload : bytes
            Raw request body.
        signature : str
            Value of ``X-Slack-Signature`` header (e.g. ``v0=abc123...``).
        kwargs :
            Must include ``timestamp`` (str) from ``X-Slack-Request-Timestamp``.
        """
        secret = self._signing_secret or os.getenv("SLACK_SIGNING_SECRET", "")
        if not secret:
            return False

        timestamp = kwargs.get("timestamp", "")
        if not timestamp:
            return False

        # Guard against replay attacks (5-minute window)
        try:
            if abs(time.time() - float(timestamp)) > 300:
                return False
        except (ValueError, TypeError):
            return False

        sig_basestring = f"v0:{timestamp}:{payload.decode('utf-8', errors='ignore')}"
        computed = (
            "v0="
            + hmac.new(
                secret.encode("utf-8"),
                sig_basestring.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        )
        return hmac.compare_digest(computed, signature)
