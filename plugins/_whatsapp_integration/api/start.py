"""Start WhatsApp bridge immediately."""

from helpers.api import ApiHandler, Request
from helpers.errors import format_error
from helpers import files, plugins


PLUGIN_NAME = "_whatsapp_integration"


class Start(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        port = int(config.get("bridge_port", 3100))
        session_dir = files.get_abs_path("usr/whatsapp/sessions")
        cache_dir = files.get_abs_path("usr/whatsapp/media")
        allowed_numbers = config.get("allowed_numbers") or []
        mode = config.get("mode", "dedicated")

        from plugins._whatsapp_integration.helpers.bridge_manager import (
            ensure_bridge_http_up,
            is_process_alive,
        )

        if is_process_alive():
            return {"success": True, "message": "Bridge already running"}

        try:
            ok = await ensure_bridge_http_up(
                port, session_dir, cache_dir, allowed_numbers, mode=mode,
            )
            if ok:
                return {"success": True, "message": "Bridge started"}
            return {"success": False, "message": "Failed to start bridge"}
        except Exception as e:
            return {"success": False, "message": format_error(e)}
