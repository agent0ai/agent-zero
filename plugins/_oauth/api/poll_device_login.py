from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers import codex
from plugins._oauth.helpers.state import get_device_attempt, pop_device_attempt


class PollDeviceLogin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        attempt_id = str(input.get("attempt_id") or "").strip()
        if not attempt_id:
            return {"ok": False, "error": "Missing device authorization attempt."}

        attempt = get_device_attempt(attempt_id)
        if attempt is None:
            return {"ok": False, "expired": True, "error": "Device authorization expired."}

        try:
            result = codex.poll_device_authorization(
                attempt.device_auth_id,
                attempt.user_code,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        if result.get("completed"):
            pop_device_attempt(attempt_id)
            return {"ok": True, "completed": True, "account_id": result.get("account_id", "")}

        return {
            "ok": True,
            "completed": False,
            "interval": attempt.interval,
            "expires_at": attempt.expires_at,
        }
