from helpers import plugins
from helpers.extension import Extension


class ScopedTelegramBots(Extension):
    async def execute(self, **kwargs):
        # Globally disabled plugins do not contribute their own job-loop hook.
        if plugins.get_toggle_state("_telegram_integration") == "disabled":
            from importlib import import_module
            manager = import_module("plugins._telegram_integration.extensions.python.job_loop._10_telegram_bot")
            await manager.TelegramBotManager(agent=None).execute()
