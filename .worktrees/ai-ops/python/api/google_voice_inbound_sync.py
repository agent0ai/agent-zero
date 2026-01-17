"""
Google Voice Inbound Sync API
Fetches inbox messages via Playwright and stores them locally.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceInboundSync(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        limit = int(input.get("limit", 10))

        from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        result = await manager.sync_inbound(limit=limit)
        return {"success": True, **result}
