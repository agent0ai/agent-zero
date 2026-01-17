from python.helpers import dotenv
from python.helpers.api import ApiHandler, Request, Response


class TelegramSettingsSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        settings = input.get("settings", {})
        if not isinstance(settings, dict):
            return {"success": False, "error": "settings must be an object"}

        mapping = {
            "bot_token": "TELEGRAM_BOT_TOKEN",
            "chat_id": "TELEGRAM_CHAT_ID",
            "webhook_url": "TELEGRAM_WEBHOOK_URL",
            "webhook_secret": "TELEGRAM_WEBHOOK_SECRET",
            "agent_context": "TELEGRAM_AGENT_CONTEXT",
        }

        for key, env_key in mapping.items():
            if key in settings:
                dotenv.save_dotenv_value(env_key, settings.get(key, ""))

        return {"success": True}
