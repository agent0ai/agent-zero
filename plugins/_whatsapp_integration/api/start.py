"""Start WhatsApp bridge immediately."""

from helpers.api import ApiHandler, Request
from helpers.errors import format_error
from helpers import plugins


PLUGIN_NAME = "_whatsapp_integration"


class Start(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        port = int(config.get("bridge_port", 3100))
        mode = config.get("mode", "self-chat")

        from plugins._whatsapp_integration.helpers.bridge_manager import (
            ensure_bridge_http_up,
            is_process_alive,
        )
        from plugins._whatsapp_integration.helpers.storage_paths import (
            get_bridge_media_dir,
            get_bridge_session_dir,
        )

        session_dir = get_bridge_session_dir()
        cache_dir = get_bridge_media_dir()

        if is_process_alive():
            return {"success": True, "message": "Bridge already running"}

        try:
            ok = await ensure_bridge_http_up(
                port, session_dir, cache_dir, mode=mode,
            )
            if ok:
                return {"success": True, "message": "Bridge started"}
            return {"success": False, "message": "Failed to start bridge"}
        except Exception as e:
            return {"success": False, "message": format_error(e)}
