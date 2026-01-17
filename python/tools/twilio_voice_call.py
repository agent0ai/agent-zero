"""Twilio Voice call tool."""

from python.helpers import files
from python.helpers.tool import Response, Tool


class TwilioVoiceCall(Tool):
    """Initiate a Twilio voice call."""

    async def execute(self, **kwargs):
        to_number = (self.args.get("to_number") or "").strip()
        message = (self.args.get("message") or "").strip() or None
        from_number = (self.args.get("from_number") or "").strip() or None
        mock = bool(self.args.get("mock", False))

        if not to_number:
            return Response(message="Error: to_number is required", break_loop=False)

        from instruments.custom.twilio_voice.twilio_voice_manager import TwilioVoiceManager

        db_path = files.get_abs_path("./instruments/custom/twilio_voice/data/twilio_voice.db")
        manager = TwilioVoiceManager(db_path)
        result = await manager.create_call(
            to_number=to_number,
            message=message,
            from_number=from_number,
            mock=mock,
        )
        if not result.get("success"):
            return Response(
                message=f"Twilio voice call failed: {result.get('error')}",
                break_loop=False,
            )
        return Response(message=f"Twilio voice call queued: {result}", break_loop=False)
