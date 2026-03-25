"""WhatsApp poll loop — start bridge and poll for incoming messages."""

import asyncio
from typing import Any

from helpers.extension import Extension
from helpers.errors import format_error
from helpers.print_style import PrintStyle
from helpers import files, plugins


PLUGIN_NAME: str = "_whatsapp_integration"
DEFAULT_INTERVAL: int = 3
MIN_INTERVAL: int = 2


# ------------------------------------------------------------------
# Extension entry point
# ------------------------------------------------------------------

class WhatsAppAutoPoll(Extension):

    async def execute(self, **kwargs: Any) -> None:
        import plugins._whatsapp_integration.helpers.handler as handler_mod

        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        enabled = config.get("enabled", False)

        if not enabled:
            if handler_mod._poll_task and not handler_mod._poll_task.done():
                handler_mod._poll_task.cancel()
                handler_mod._poll_task = None
            return

        if not handler_mod._poll_task or handler_mod._poll_task.done():
            handler_mod._poll_task = asyncio.create_task(_poll_loop())


# ------------------------------------------------------------------
# Poll loop
# ------------------------------------------------------------------

async def _poll_loop() -> None:
    from plugins._whatsapp_integration.helpers import bridge_manager
    from plugins._whatsapp_integration.helpers.handler import poll_messages

    bridge_started = False

    while True:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        if not config.get("enabled", False):
            break

        port = int(config.get("bridge_port", 3100))
        session_dir = files.get_abs_path("usr/whatsapp/sessions")
        cache_dir = files.get_abs_path("usr/whatsapp/media")
        allowed_users = config.get("allowed_users") or []
        mode = config.get("mode", "dedicated")

        # Detect config changes that require bridge restart
        desired = {"port": port, "mode": mode, "allowed_users": sorted(allowed_users)}
        running = bridge_manager.get_running_config()
        if bridge_started and bridge_manager.is_process_alive() and running and running != desired:
            PrintStyle.info(f"WhatsApp: config changed, restarting bridge")
            await bridge_manager.stop_bridge()
            bridge_started = False

        # Start bridge if needed
        if not bridge_started or not bridge_manager.is_process_alive():
            try:
                bridge_started = await bridge_manager.start_bridge(
                    port, session_dir, cache_dir, allowed_users, mode=mode,
                )
            except Exception as e:
                PrintStyle.error(f"WhatsApp bridge start error: {format_error(e)}")
                await asyncio.sleep(10)
                continue

        try:
            await poll_messages(config)
        except Exception as e:
            PrintStyle.error(f"WhatsApp poll error: {format_error(e)}")

        sleep_sec = max(config.get("poll_interval_seconds", DEFAULT_INTERVAL), MIN_INTERVAL)
        await asyncio.sleep(sleep_sec)
