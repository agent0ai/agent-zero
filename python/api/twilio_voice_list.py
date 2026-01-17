"""
Twilio Voice List API
Returns recent outbound calls.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class TwilioVoiceList(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        limit = int(input.get("limit", 50))

        from instruments.custom.twilio_voice.twilio_voice_manager import TwilioVoiceManager

        db_path = files.get_abs_path("./instruments/custom/twilio_voice/data/twilio_voice.db")
        manager = TwilioVoiceManager(db_path)
        calls = manager.list_calls(limit=limit)
        return {"success": True, "calls": calls}
