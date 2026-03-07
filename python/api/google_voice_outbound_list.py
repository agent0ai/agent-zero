"""
Google Voice Outbound List API
Returns outbound SMS drafts and history.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceOutboundList(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        status = input.get("status")

        try:
            from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
        except ModuleNotFoundError:
            return {
                "success": False,
                "error": "Google Voice integration is not installed (missing instruments.custom.google_voice).",
            }

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        messages = manager.list_outbound(status=status)
        return {"success": True, "messages": messages}
