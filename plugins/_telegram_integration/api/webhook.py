import secrets

from helpers.api import ApiHandler, Request, Response
from helpers.print_style import PrintStyle
from plugins._telegram_integration.helpers.dependencies import ensure_dependencies


class TelegramWebhook(ApiHandler):
    """Receives Telegram updates authenticated by the webhook secret header."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        ensure_dependencies()
        from aiogram.types import Update

        from plugins._telegram_integration.helpers.bot_manager import get_bot

        # Identify which bot this update is for
        bot_name = request.args.get("bot", "")
        if not bot_name:
            return Response("Missing ?bot= parameter", 400)

        instance = get_bot(bot_name)
        if not instance:
            return Response(f"Bot not found: {bot_name}", 404)

        # Polling and incompletely configured bots must never accept HTTP updates.
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if (
            not instance.webhook_active
            or not instance.webhook_secret
            or not secrets.compare_digest(secret_header.encode(), instance.webhook_secret.encode())
        ):
            return Response("Invalid secret token", 403)

        # Parse and feed the update to aiogram
        try:
            update = Update.model_validate(input, context={"bot": instance.bot})
            await instance.dispatcher.feed_update(instance.bot, update)
        except Exception as e:
            PrintStyle.error(f"Telegram webhook ({bot_name}): {e}")
            return Response("Internal error", 500)

        return {"ok": True}
