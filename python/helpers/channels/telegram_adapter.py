"""Telegram channel adapter.

Refactored from telegram_bridge.py / telegram_client.py to conform to the
ChannelBridge / ChannelClient interfaces while keeping backward compatibility
with existing TELEGRAM_* environment variables.
"""

from __future__ import annotations

import hmac
import json
import os
import urllib.request
from typing import Any

from python.helpers.channel_bridge import ChannelBridge, ChannelClient


class TelegramBridge(ChannelBridge):
    """Telegram-specific state and routing."""

    def __init__(self) -> None:
        state_dir = os.getenv("TELEGRAM_STATE_DIR", "data")
        super().__init__(channel_name="telegram", state_dir=state_dir)

    def required_env_vars(self) -> list[str]:
        return ["TELEGRAM_BOT_TOKEN"]


class TelegramClient(ChannelClient):
    """Sends messages via the Telegram Bot API."""

    def __init__(self) -> None:
        self._token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    async def send_message(self, recipient_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        token = self._token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            return {"error": "TELEGRAM_BOT_TOKEN not set"}

        parse_mode = kwargs.get("parse_mode", "Markdown")
        payload = {
            "chat_id": recipient_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310
            raw = resp.read().decode("utf-8", errors="ignore")
        return {"raw": raw}

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any,
    ) -> bool:
        """Telegram uses a simple secret-token header comparison.

        ``signature`` is the value of X-Telegram-Bot-Api-Secret-Token.
        """
        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        if not secret:
            # No secret configured — accept all (backward-compat)
            return True
        return hmac.compare_digest(signature, secret)
