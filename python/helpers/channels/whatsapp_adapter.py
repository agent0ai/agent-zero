"""WhatsApp Cloud API channel adapter.

Uses Meta's WhatsApp Cloud API for sending messages and HMAC-SHA256
signature verification for incoming webhooks:
https://developers.facebook.com/docs/whatsapp/cloud-api
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.request
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelClient


class WhatsAppBridge(ChannelBridge):
    """WhatsApp-specific state and routing."""

    def __init__(self) -> None:
        super().__init__(channel_name="whatsapp", state_dir="data")

    def required_env_vars(self) -> list[str]:
        return [
            "WHATSAPP_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
            "WHATSAPP_VERIFY_TOKEN",
        ]


class WhatsAppClient(ChannelClient):
    """Sends messages via the WhatsApp Cloud API."""

    GRAPH_API = "https://graph.facebook.com/v18.0"

    def __init__(self) -> None:
        self._token = os.getenv("WHATSAPP_TOKEN", "")
        self._phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self._app_secret = os.getenv("WHATSAPP_APP_SECRET", "")

    async def send_message(self, recipient_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        token = self._token or os.getenv("WHATSAPP_TOKEN", "")
        phone_id = self._phone_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        if not token or not phone_id:
            return {"error": "WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID not set"}

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.GRAPH_API}/{phone_id}/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
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
        """Verify Meta webhook HMAC-SHA256 signature.

        Parameters
        ----------
        payload : bytes
            Raw request body.
        signature : str
            Value of ``X-Hub-Signature-256`` header (e.g. ``sha256=abc...``).
        """
        secret = self._app_secret or os.getenv("WHATSAPP_APP_SECRET", "")
        if not secret:
            return False

        if not signature.startswith("sha256="):
            return False

        expected_sig = signature[len("sha256=") :]
        computed = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, expected_sig)

    def verify_subscription(self, mode: str, token: str, challenge: str) -> str | None:
        """Handle Meta webhook verification GET request.

        Returns the challenge string if valid, None otherwise.
        """
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        if mode == "subscribe" and hmac.compare_digest(token, verify_token):
            return challenge
        return None
