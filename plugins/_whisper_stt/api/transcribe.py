from helpers.api import ApiHandler, Request, Response
from plugins._whisper_stt.helpers import runtime


class Transcribe(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not runtime.is_globally_enabled():
            return Response(status=409, response="Whisper STT plugin is disabled")

        audio = str(input.get("audio") or "").strip()
        if not audio:
            return Response(status=400, response="Missing audio")

        ctxid = str(input.get("ctxid") or "").strip()
        if ctxid:
            self.use_context(ctxid)

        try:
            result = await runtime.transcribe(audio)
            return {
                "success": True,
                "text": str(result.get("text") or "").strip(),
                "language": str(result.get("language") or "").strip(),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "text": ""}
