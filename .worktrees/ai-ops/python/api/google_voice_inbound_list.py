"""
Google Voice Inbound List API
Returns inbound SMS messages.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceInboundList(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        limit = int(input.get("limit", 50))

        from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        messages = manager.list_inbound(limit=limit)
        return {"success": True, "messages": messages}
