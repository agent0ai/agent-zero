from helpers import plugins
from helpers.api import ApiHandler, Request


class Status(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        config = plugins.get_plugin_config("_telegram_integration") or {}
        try:
            from plugins._telegram_integration.helpers.bot_manager import get_all_bots
            running = get_all_bots()
        except Exception:
            running = {}

        bots = []
        for index, bot_cfg in enumerate(config.get("bots") or []):
            name = str(bot_cfg.get("name") or f"Bot {index + 1}")
            instance = running.get(name)
            task = getattr(instance, "task", None)
            active = bool(instance and (getattr(instance, "webhook_active", False) or (task and not task.done())))
            info = getattr(instance, "bot_info", None)
            if not bot_cfg.get("token"):
                state = "Needs token"
            elif not bot_cfg.get("enabled"):
                state = "Disabled"
            elif active:
                state = "Running"
            else:
                state = "Ready"
            bots.append({
                "name": name,
                "enabled": bool(bot_cfg.get("enabled")),
                "configured": bool(bot_cfg.get("token")),
                "running": active,
                "state": state,
                "mode": "Webhook" if getattr(instance, "webhook_active", False) else str(bot_cfg.get("mode") or "polling").title(),
                "username": f"@{info.username}" if getattr(info, "username", None) else "",
                "access": f"{len(bot_cfg.get('allowed_users') or [])} allowed" if bot_cfg.get("allowed_users") else "Open access",
                "project": str(bot_cfg.get("default_project") or "No project"),
            })

        return {
            "ok": True,
            "configured": sum(bot["configured"] for bot in bots),
            "running": sum(bot["running"] for bot in bots),
            "bots": bots,
        }
