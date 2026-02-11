from python.helpers import settings, whisper
from python.helpers.api import ApiHandler, Request, Response


class Transcribe(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        audio = input.get("audio")
        ctxid = input.get("ctxid", "")

        if ctxid:
            _context = self.use_context(ctxid)

        # if not await whisper.is_downloaded():
        #     context.log.log(type="info", content="Whisper STT model is currently being initialized, please wait...")

        set = settings.get_settings()
        result = await whisper.transcribe(set["stt_model_size"], audio)  # type: ignore
        return result
