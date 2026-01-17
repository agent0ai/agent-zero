"""
Google Voice Outbound Approve API
Approves and sends a draft outbound SMS message.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceOutboundApprove(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        message_id = input.get("message_id")
        if not message_id:
            return {"success": False, "error": "message_id is required"}

        from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        result = await manager.approve_and_send(int(message_id))
        return result
