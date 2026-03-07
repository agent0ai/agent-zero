"""
Google Voice Session Start API
Launches a visible Playwright browser session.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class GoogleVoiceSessionStart(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        try:
            from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
        except ModuleNotFoundError:
            return {
                "success": False,
                "error": "Google Voice integration is not installed (missing instruments.custom.google_voice).",
            }

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        result = await manager.start_session()
        return {"success": True, **result}
