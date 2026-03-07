"""
Twilio Voice Status API
Updates call status from Twilio webhook.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class TwilioVoiceStatus(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        call_sid = (input.get("call_sid") or "").strip()
        status = (input.get("status") or "").strip()
        if not call_sid or not status:
            return {"success": False, "error": "call_sid and status are required"}

        try:
            from instruments.custom.twilio_voice.twilio_voice_manager import TwilioVoiceManager
        except ModuleNotFoundError:
            return {
                "success": False,
                "error": "Twilio Voice integration is not installed (missing instruments.custom.twilio_voice).",
            }

        db_path = files.get_abs_path("./instruments/custom/twilio_voice/data/twilio_voice.db")
        manager = TwilioVoiceManager(db_path)
        await manager.update_status(call_sid, status)
        return {"success": True}
