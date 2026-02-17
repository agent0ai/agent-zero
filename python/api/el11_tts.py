from python.helpers.api import ApiHandler, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os
from python.helpers import runtime

class El11Tts(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response:
        text = input.get("text", "")
        if not text:
            return {"error": "No text provided", "success": False}
        profile = input.get("profile")
        if not profile:
            return {"error": "No profile provided", "success": False}
        try:
            voice_id = (await runtime.read_file(f'agents/{profile}/voice_id.txt')).strip()
        except FileNotFoundError:
            return {"error": f'Voice ID file missing: agents/{profile}/voice_id.txt', "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
        api_key = os.getenv("EL11_API_KEY")
        if not api_key:
            return {"error": "EL11_API_KEY missing", "success": False}
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {'xi-api-key': api_key, 'Content-Type': 'application/json'}
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=data, stream=True)
            if resp.status_code != 200:
                return {"error": f'EL11 API error {resp.status_code}: {await resp.aread()[:500]}', "success": False}
            return StreamingResponse(resp.aiter_bytes(), media_type='audio/mpeg')
