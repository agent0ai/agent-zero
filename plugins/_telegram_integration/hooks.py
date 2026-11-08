from copy import deepcopy
from hashlib import sha256


def get_plugin_config(default=None, **kwargs):
    config = deepcopy(default or {})
    for bot in config.get("bots", []):
        bot["token"] = str(bot.get("token") or "").strip()
        if not str(bot.get("name") or "").strip() and bot["token"]:
            bot_id = bot["token"].split(":", 1)[0]
            bot["name"] = "bot_" + (bot_id if bot_id.isdigit() else sha256(bot["token"].encode()).hexdigest()[:12])
    return config


def save_plugin_config(settings=None, **kwargs):
    config = get_plugin_config(settings)
    names = [bot.get("name") for bot in config.get("bots", []) if bot.get("name")]
    if len(names) != len(set(names)):
        raise ValueError("Each Telegram bot must have a different name.")
    return config


def disable():
    from plugins._telegram_integration.helpers.bot_manager import get_all_bots
    from plugins._telegram_integration.helpers.sandbox import worker
    for instance in list(get_all_bots().values()):
        instance.webhook_active = False
        instance.webhook_secret = ''
        for task in list(instance.deliveries):
            task.get_loop().call_soon_threadsafe(task.cancel)
        if instance.task and not instance.task.done():
            instance.task.get_loop().call_soon_threadsafe(instance.task.cancel)
    get_all_bots().clear()
    worker.stop()
