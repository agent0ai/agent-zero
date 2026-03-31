"""WhatsApp poll loop — start bridge and poll for incoming messages."""

import asyncio
from typing import Any

from helpers.extension import Extension
from helpers.errors import format_error
from helpers.print_style import PrintStyle
from helpers import plugins


PLUGIN_NAME: str = "_whatsapp_integration"
DEFAULT_INTERVAL: int = 3
MIN_INTERVAL: int = 2
MAX_CONSECUTIVE_FAILURES: int = 5


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
    from plugins._whatsapp_integration.helpers.storage_paths import (
        get_bridge_media_dir,
        get_bridge_session_dir,
    )

    bridge_started = False
    consecutive_failures = 0

    try:
        while True:
            config = plugins.get_plugin_config(PLUGIN_NAME) or {}
            if not config.get("enabled", False):
                break
            if PLUGIN_NAME not in plugins.get_enabled_plugins(None):
                break

            port = int(config.get("bridge_port", 3100))
            session_dir = get_bridge_session_dir()
            cache_dir = get_bridge_media_dir()
            mode = config.get("mode", "self-chat")

            # Detect config changes that require bridge restart
            desired = {"port": port, "mode": mode}
            running = bridge_manager.get_running_config()
            if bridge_started and bridge_manager.is_process_alive() and running != desired:
                PrintStyle.info(f"WhatsApp: config changed, restarting bridge")
                await bridge_manager.stop_bridge()
                bridge_started = False
                consecutive_failures = 0

            # Start bridge if needed
            if not bridge_started or not bridge_manager.is_process_alive():
                try:
                    bridge_started = await bridge_manager.start_bridge(
                        port, session_dir, cache_dir, mode=mode,
                    )
                    if bridge_started:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                except FileNotFoundError:
                    PrintStyle.error(
                        "WhatsApp: Node.js is not installed. "
                        "Stopping poll loop — install Node.js and re-enable the plugin."
                    )
                    break
                except Exception as e:
                    consecutive_failures += 1
                    PrintStyle.error(f"WhatsApp bridge start error: {format_error(e)}")

                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    PrintStyle.error(
                        f"WhatsApp: bridge failed {consecutive_failures} times in a row, "
                        f"stopping poll loop. Disable and re-enable the plugin to retry."
                    )
                    break

                if not bridge_started:
                    await asyncio.sleep(10)
                    continue

            try:
                await poll_messages(config)
            except Exception as e:
                PrintStyle.error(f"WhatsApp poll error: {format_error(e)}")

            sleep_sec = max(config.get("poll_interval_seconds", DEFAULT_INTERVAL), MIN_INTERVAL)
            await asyncio.sleep(sleep_sec)
    finally:
        # Ensure bridge stops when poll loop exits (plugin disabled or task cancelled)
        try:
            if bridge_manager.is_process_alive():
                await bridge_manager.stop_bridge()
        except Exception:
            pass
