# api/synthesize.py - Unified TTS API supporting multiple engines

from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings as settings_helper, kokoro_tts, edge_tts

class Synthesize(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        text = input.get("text", "")
        ctxid = input.get("ctxid", "")

        if ctxid:
            context = self.use_context(ctxid)

        # Read TTS settings
        current_settings = settings_helper.get_settings()
        engine = current_settings.get("tts_engine", "kokoro")
        voice = current_settings.get("tts_voice", "")
        rate = current_settings.get("tts_rate", "+0%")

        try:
            if engine == "edge":
                audio = await edge_tts.synthesize(text, voice=voice or "en-US-AriaNeural", rate=rate)
            else:
                # kokoro engine (default)
                # Convert rate string like "+20%" to float speed multiplier
                speed = self._rate_to_speed(rate)
                audio = await kokoro_tts.synthesize_sentences([text], voice=voice, speed=speed)

            return {"audio": audio, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    @staticmethod
    def _rate_to_speed(rate: str) -> float:
        """Convert rate string (e.g. '+20%', '-10%') to kokoro speed float."""
        try:
            pct = int(rate.replace("%", "").replace("+", ""))
            return 1.0 + pct / 100.0
        except (ValueError, AttributeError):
            return 1.1