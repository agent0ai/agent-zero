import json
import urllib.request

from python.helpers import dotenv
from python.helpers.api import ApiHandler, Request, Response


class TelegramWebhookSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        token = dotenv.get_dotenv_value("TELEGRAM_BOT_TOKEN", "")
        if not token:
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN is not set"}

        url = input.get("url") or dotenv.get_dotenv_value("TELEGRAM_WEBHOOK_URL", "")
        secret = input.get("secret") or dotenv.get_dotenv_value("TELEGRAM_WEBHOOK_SECRET", "")
        if not url:
            return {"success": False, "error": "Webhook URL is required"}

        payload = {"url": url}
        if secret:
            payload["secret_token"] = secret

        data = json.dumps(payload).encode("utf-8")
        endpoint = f"https://api.telegram.org/bot{token}/setWebhook"
        request_obj = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request_obj, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="ignore")
        return {"success": True, "response": raw}
