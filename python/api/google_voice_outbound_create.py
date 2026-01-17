"""
Google Voice Outbound Create API
Creates a draft outbound SMS message for approval.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceOutboundCreate(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        to_number = (input.get("to_number") or "").strip()
        body = (input.get("body") or "").strip()
        auto_send = bool(input.get("auto_send", False))
        force_manual = bool(input.get("force_manual", False))
        if not to_number or not body:
            return {"success": False, "error": "to_number and body are required"}

        from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
        from python.helpers import settings as settings_helper

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        message = manager.draft_outbound(to_number, body)
        try:
            settings = settings_helper.get_settings()
            auto_send_setting = settings.get("google_voice_auto_send", False)
        except Exception:
            auto_send_setting = False
        if not force_manual and (auto_send or auto_send_setting):
            result = await manager.approve_and_send(message["id"])
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Auto-send failed")}
            return {"success": True, "message": result["message"]}
        return {"success": True, "message": message}
