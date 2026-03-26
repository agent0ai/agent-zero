"""
Start the Telegram bridge on agent initialisation.

Singleton-guarded: only the first agent_init invocation starts the bot.
Subsequent calls (new agent instantiations) are no-ops.

TEMPORARY: When the Plugin Lifecycle Manager lands (Phase 2 roadmap),
this extension becomes a fallback.
"""

import os

from python.helpers.extension import Extension
from python.helpers.print_style import PrintStyle


class TelegramStart(Extension):
    async def execute(self, **kwargs) -> None:
        # Only start from the main agent (A0), not subordinates
        if self.agent.number != 0:
            return

        from python.helpers import settings as a0_settings

        s = a0_settings.get_settings()
        enabled_in_settings = s.get("telegram_enabled", False)

        from python.helpers.secrets import get_default_secrets_manager

        secrets = get_default_secrets_manager().load_secrets()
        has_token = bool(
            secrets.get("TELEGRAM_BOT_TOKEN", "")
            or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        )

        if not (enabled_in_settings and has_token):
            return  # Telegram not configured, skip silently

        from plugins.telegram.helpers.telegram_bridge import TelegramBridge

        bridge = TelegramBridge.get_instance()

        if bridge.is_running:
            return  # Already started by a previous agent_init

        try:
            await bridge.start()
            PrintStyle(
                font_color="white",
                background_color="#0088cc",
                bold=True,
                padding=True,
            ).print("Telegram bridge started")
        except Exception as e:
            PrintStyle.error(f"Failed to start Telegram bridge: {e}")
