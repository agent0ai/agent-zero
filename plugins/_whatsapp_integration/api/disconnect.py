"""Disconnect WhatsApp account by stopping bridge and clearing session."""

import os
import shutil

from helpers.api import ApiHandler, Request
from helpers.errors import format_error


class Disconnect(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        try:
            from plugins._whatsapp_integration.helpers import bridge_manager
            from plugins._whatsapp_integration.helpers.storage_paths import get_bridge_session_dir

            # Stop bridge first
            await bridge_manager.stop_bridge()

            # Delete session files
            session_dir = get_bridge_session_dir()
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)

            return {"success": True, "message": "Account disconnected"}
        except Exception as e:
            return {"success": False, "message": format_error(e)}
