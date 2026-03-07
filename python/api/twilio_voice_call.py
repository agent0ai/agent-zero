"""
Twilio Voice Call API
Initiates an outbound voice call via Twilio.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class TwilioVoiceCall(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        to_number = (input.get("to_number") or "").strip()
        message = (input.get("message") or "").strip() or None
        from_number = (input.get("from_number") or "").strip() or None
        mock = bool(input.get("mock", False))
        if not to_number:
            return {"success": False, "error": "to_number is required"}

        try:
            from instruments.custom.twilio_voice.twilio_voice_manager import TwilioVoiceManager
        except ModuleNotFoundError:
            return {
                "success": False,
                "error": "Twilio Voice integration is not installed (missing instruments.custom.twilio_voice).",
            }

        db_path = files.get_abs_path("./instruments/custom/twilio_voice/data/twilio_voice.db")
        manager = TwilioVoiceManager(db_path)
        result = await manager.create_call(
            to_number=to_number,
            message=message,
            from_number=from_number,
            mock=mock,
        )
        return result
