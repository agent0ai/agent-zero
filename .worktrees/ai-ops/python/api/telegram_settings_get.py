import json
import urllib.request

from python.helpers import dotenv
from python.helpers.api import ApiHandler, Request, Response


class TelegramSettingsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        token = dotenv.get_dotenv_value("TELEGRAM_BOT_TOKEN", "")
        webhook_info = None
        if token:
            try:
                endpoint = f"https://api.telegram.org/bot{token}/getWebhookInfo"
                with urllib.request.urlopen(endpoint, timeout=15) as response:
                    webhook_info = json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                webhook_info = {"ok": False, "error": str(exc)}

        return {
            "settings": {
                "bot_token": token,
                "chat_id": dotenv.get_dotenv_value("TELEGRAM_CHAT_ID", ""),
                "webhook_url": dotenv.get_dotenv_value("TELEGRAM_WEBHOOK_URL", ""),
                "webhook_secret": dotenv.get_dotenv_value("TELEGRAM_WEBHOOK_SECRET", ""),
                "agent_context": dotenv.get_dotenv_value("TELEGRAM_AGENT_CONTEXT", ""),
            },
            "webhook_info": webhook_info,
        }
