from helpers.api import ApiHandler, Request
from helpers.errors import format_error


class TestConnection(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        bot_cfg = input.get("bot", {})
        token = bot_cfg.get("token", "")
        results: list[dict] = []

        if not token:
            results.append({
                "test": "Bot token",
                "ok": False,
                "message": "Add your bot token first.",
            })
            return {"success": False, "results": results}

        try:
            from plugins._telegram_integration.helpers.bot_manager import test_token
            ok, message = await test_token(token)
            results.append({
                "test": "Telegram bot",
                "ok": ok,
                "message": "Telegram accepted the bot token." if ok else message,
            })
        except Exception as e:
            results.append({
                "test": "Telegram bot",
                "ok": False,
                "message": f"Could not validate the bot token: {format_error(e)}",
            })

        return {"success": all(r["ok"] for r in results), "results": results}
