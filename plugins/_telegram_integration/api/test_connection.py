from helpers.api import ApiHandler, Request
from helpers.errors import format_error


class TestConnection(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        bot_cfg = input.get("bot", {})
        token = bot_cfg.get("token", "")
        results: list[dict] = []

        if not token:
            results.append({
                "test": "Token",
                "ok": False,
                "message": "No bot token provided",
            })
            return {"success": False, "results": results}

        try:
            from plugins._telegram_integration.helpers.bot_manager import test_token
            ok, message = await test_token(token)
            results.append({
                "test": "Bot Token",
                "ok": ok,
                "message": message,
            })
        except Exception as e:
            results.append({
                "test": "Bot Token",
                "ok": False,
                "message": format_error(e),
            })

        return {"success": all(r["ok"] for r in results), "results": results}
