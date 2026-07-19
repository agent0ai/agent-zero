from __future__ import annotations

import secrets

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers import codex
from plugins._oauth.helpers.config import codex_config
from plugins._oauth.helpers.state import put_device_attempt


class StartDeviceLogin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        cfg = codex_config()
        if not cfg["enabled"]:
            return {"ok": False, "error": "Codex/ChatGPT account connection is disabled."}

        try:
            device = codex.request_device_code()
            attempt_id = secrets.token_urlsafe(24)
            attempt = put_device_attempt(
                attempt_id,
                device["device_auth_id"],
                device["user_code"],
                device["interval"],
                device["expires_at"],
            )
            return {
                "ok": True,
                "attempt_id": attempt.attempt_id,
                "verification_url": device["verification_url"],
                "user_code": attempt.user_code,
                "interval": attempt.interval,
                "expires_at": attempt.expires_at,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
