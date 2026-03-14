import json
import urllib.request

from python.helpers.api import ApiHandler, Request, Response


class TelegramWebhookTest(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        url = input.get("url", "")
        secret = input.get("secret", "")
        if not url:
            return {"success": False, "error": "url is required"}

        payload = {
            "update_id": 0,
            "message": {
                "message_id": 0,
                "chat": {"id": 0, "type": "private"},
                "text": "Webhook test from Agent Jumbo",
            },
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["X-Telegram-Bot-Api-Secret-Token"] = secret

        request_obj = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request_obj, timeout=15) as response:  # nosec B310
                raw = response.read().decode("utf-8", errors="ignore")
            return {"success": True, "response": raw}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
