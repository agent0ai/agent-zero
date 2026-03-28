"""Disconnect WhatsApp account by stopping bridge and clearing session."""

import shutil

from helpers.api import ApiHandler, Request
from helpers.errors import format_error
from helpers import files


class Disconnect(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        try:
            from plugins._whatsapp_integration.helpers import bridge_manager

            # Stop bridge first
            await bridge_manager.stop_bridge()

            # Delete session files
            session_dir = files.get_abs_path("usr/whatsapp/sessions")
            if files.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)

            return {"success": True, "message": "Account disconnected"}
        except Exception as e:
            return {"success": False, "message": format_error(e)}
