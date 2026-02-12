# api/tts_voices.py - Returns available voices for the selected TTS engine

from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings as settings_helper


# Built-in Kokoro voice list
KOKORO_VOICES = [
    {"id": "af_heart", "name": "Heart (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_alloy", "name": "Alloy (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_aoede", "name": "Aoede (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_bella", "name": "Bella (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_jessica", "name": "Jessica (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_kore", "name": "Kore (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_nicole", "name": "Nicole (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_nova", "name": "Nova (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_river", "name": "River (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_sarah", "name": "Sarah (Female)", "language": "en-US", "gender": "Female"},
    {"id": "af_sky", "name": "Sky (Female)", "language": "en-US", "gender": "Female"},
    {"id": "am_adam", "name": "Adam (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_echo", "name": "Echo (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_eric", "name": "Eric (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_liam", "name": "Liam (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_michael", "name": "Michael (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_onyx", "name": "Onyx (Male)", "language": "en-US", "gender": "Male"},
    {"id": "am_puck", "name": "Puck (Male)", "language": "en-US", "gender": "Male"},
    {"id": "bf_emma", "name": "Emma (Female)", "language": "en-GB", "gender": "Female"},
    {"id": "bf_isabella", "name": "Isabella (Female)", "language": "en-GB", "gender": "Female"},
    {"id": "bm_daniel", "name": "Daniel (Male)", "language": "en-GB", "gender": "Male"},
    {"id": "bm_fable", "name": "Fable (Male)", "language": "en-GB", "gender": "Male"},
    {"id": "bm_george", "name": "George (Male)", "language": "en-GB", "gender": "Male"},
    {"id": "bm_lewis", "name": "Lewis (Male)", "language": "en-GB", "gender": "Male"},
]


class TtsVoices(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        engine = input.get("engine", "")

        try:
            if engine == "edge":
                from python.helpers import edge_tts
                voices = await edge_tts.get_voices()
            elif engine == "kokoro":
                voices = KOKORO_VOICES
            else:
                voices = []

            return {"voices": voices, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
