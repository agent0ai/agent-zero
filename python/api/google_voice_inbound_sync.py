"""
Google Voice Inbound Sync API
Fetches inbox messages via Playwright and stores them locally.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceInboundSync(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        limit = int(input.get("limit", 10))

        try:
            from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
        except ModuleNotFoundError:
            return {
                "success": False,
                "error": "Google Voice integration is not installed (missing instruments.custom.google_voice).",
            }

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        result = await manager.sync_inbound(limit=limit)
        return {"success": True, **result}
