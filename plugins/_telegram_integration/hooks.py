from copy import deepcopy
from hashlib import sha256


def get_plugin_config(default=None, **kwargs):
    config = deepcopy(default or {})
    if not isinstance(config, dict) or not isinstance(config.get("bots", []), list):
        raise ValueError("Telegram configuration must contain a bot list.")
    for bot in config.get("bots", []):
        if not isinstance(bot, dict) or not isinstance(bot.get("enabled", False), bool):
            raise ValueError("Each Telegram bot must have a boolean enabled setting.")
        for field in ("allowed_users", "admin_users"):
            if not isinstance(bot.get(field, []), list):
                raise ValueError(f"Telegram {field} must be a list.")
        if bot.get("group_mode", "mention") not in {"off", "mention", "all"}:
            raise ValueError("Telegram group mode must be off, mention or all.")
        if bot.get("mode", "polling") not in {"polling", "webhook"}:
            raise ValueError("Telegram delivery mode must be polling or webhook.")
        bot["token"] = str(bot.get("token") or "").strip()
        if not str(bot.get("name") or "").strip() and bot["token"]:
            bot_id = bot["token"].split(":", 1)[0]
            bot["name"] = "bot_" + (bot_id if bot_id.isdigit() else sha256(bot["token"].encode()).hexdigest()[:12])
    return config


def save_plugin_config(settings=None, project_name="", agent_profile="", **kwargs):
    config = get_plugin_config(settings)
    names = [bot.get("name") for bot in config.get("bots", []) if bot.get("name")]
    if len(names) != len(set(names)):
        raise ValueError("Each Telegram bot must have a different name.")
    from plugins._telegram_integration.helpers.scopes import bot_identity, configured_bots, is_safe_name
    if any(not is_safe_name(name) for name in names):
        raise ValueError("Bot names must contain 1–128 characters without path separators or control characters.")
    identities = [bot_identity(bot) for bot in config.get("bots", []) if bot.get("token")]
    other_ids = {bot_identity(bot.config) for bot in configured_bots()
                 if (bot.project, bot.profile) != (project_name, agent_profile)}
    if len(identities) != len(set(identities)) or other_ids.intersection(identities):
        raise ValueError("Each configured scope needs a separate Telegram bot. Create one with @BotFather and use its token; do not copy an existing bot token.")
    if project_name:
        for bot in config.get("bots", []):
            targets = [bot.get("default_project")] + list((bot.get("user_projects") or {}).values())
            if any(target and target != project_name for target in targets):
                raise ValueError("A project-scoped Telegram bot can only route to its own project.")
    return config
