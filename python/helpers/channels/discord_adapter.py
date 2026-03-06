"""Discord channel adapter.

Uses the Discord REST API for sending messages and Ed25519 signature
verification for incoming interaction webhooks per Discord's security model:
https://discord.com/developers/docs/interactions/receiving-and-responding
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelClient


class DiscordBridge(ChannelBridge):
    """Discord-specific state and routing."""

    def __init__(self) -> None:
        super().__init__(channel_name="discord", state_dir="data")

    def required_env_vars(self) -> list[str]:
        return ["DISCORD_BOT_TOKEN", "DISCORD_PUBLIC_KEY"]


class DiscordClient(ChannelClient):
    """Sends messages via the Discord REST API."""

    DISCORD_API = "https://discord.com/api/v10"

    def __init__(self) -> None:
        self._token = os.getenv("DISCORD_BOT_TOKEN", "")
        self._public_key = os.getenv("DISCORD_PUBLIC_KEY", "")

    async def send_message(self, recipient_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        token = self._token or os.getenv("DISCORD_BOT_TOKEN", "")
        if not token:
            return {"error": "DISCORD_BOT_TOKEN not set"}

        # Truncate to Discord's 2000-char limit
        if len(text) > 2000:
            text = text[:1997] + "..."

        payload = {"content": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.DISCORD_API}/channels/{recipient_id}/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bot {token}",
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
        """Verify Discord Ed25519 interaction signature.

        Parameters
        ----------
        payload : bytes
            ``timestamp + body`` concatenated bytes.
        signature : str
            Value of ``X-Signature-Ed25519`` header.
        kwargs :
            ``timestamp`` from ``X-Signature-Timestamp`` header.
        """
        public_key = self._public_key or os.getenv("DISCORD_PUBLIC_KEY", "")
        if not public_key:
            return False

        timestamp = kwargs.get("timestamp", "")
        if not timestamp:
            return False

        try:
            # Use PyNaCl if available (preferred), otherwise reject
            from nacl.exceptions import BadSignatureError
            from nacl.signing import VerifyKey

            verify_key = VerifyKey(bytes.fromhex(public_key))
            message = timestamp.encode("utf-8") + payload
            verify_key.verify(message, bytes.fromhex(signature))
            return True
        except ImportError:
            # PyNaCl not installed — fall back to standard-lib Ed25519
            # (Python 3.12+ has it, but not universally available)
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                    Ed25519PublicKey,
                )

                key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))
                message = timestamp.encode("utf-8") + payload
                key.verify(bytes.fromhex(signature), message)
                return True
            except Exception:
                return False
        except (BadSignatureError, Exception):
            return False
