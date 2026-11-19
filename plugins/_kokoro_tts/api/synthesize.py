import asyncio
import json

from helpers.api import ApiHandler, Request, Response
from plugins._kokoro_tts.helpers import runtime


class Synthesize(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not runtime.is_globally_enabled():
            return Response(status=409, response="Local TTS plugin is disabled")

        text = str(input.get("text") or "").strip()
        if not text:
            return Response(status=400, response="Missing text")

        try:
            config = runtime.get_config()
            initializing = input.get("report_initialization") and not await runtime.is_downloaded(config)
        except Exception as e:
            return {"success": False, "error": str(e)}

        async def synthesize():
            try:
                audio = await runtime.synthesize_sentences([text], config)
                return {"success": True, "audio": audio, "mime_type": "audio/wav"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if initializing:
            def body():
                # Flush the cold-start header before the WSGI thread waits for the audio.
                yield b" "
                yield json.dumps(asyncio.run(synthesize())).encode()

            return Response(
                body(), mimetype="application/json",
                headers={"X-A0-Speech-Initializing": "1", "X-Accel-Buffering": "no"},
            )

        return await synthesize()
