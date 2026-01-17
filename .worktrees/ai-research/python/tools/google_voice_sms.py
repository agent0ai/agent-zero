"""Google Voice SMS tool."""

from python.helpers import files
from python.helpers.tool import Response, Tool


class GoogleVoiceSms(Tool):
    """Create a Google Voice SMS draft (manual approval by default)."""

    async def execute(self, **kwargs):
        to_number = (self.args.get("to_number") or "").strip()
        body = (self.args.get("body") or "").strip()
        auto_send = bool(self.args.get("auto_send", False))

        if not to_number or not body:
            return Response(message="Error: to_number and body are required", break_loop=False)

        from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
        from python.helpers import settings as settings_helper

        db_path = files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db")
        manager = GoogleVoiceManager(db_path)
        draft = manager.draft_outbound(to_number, body)
        if auto_send or settings_helper.get_settings().get("google_voice_auto_send", False):
            result = await manager.approve_and_send(draft["id"])
            if not result.get("success"):
                return Response(message=f"Google Voice send failed: {result.get('error')}", break_loop=False)
            return Response(message=f"Google Voice sent: {result['message']}", break_loop=False)

        return Response(message=f"Google Voice draft created: {draft}", break_loop=False)
