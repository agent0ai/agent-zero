from python.helpers.api import ApiHandler, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os
import json
from python.helpers import runtime

class El11Tts(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response:
        text = input.get("text", "")
        if not text:
            return {"error": "No text provided", "success": False}
        profile = input.get("profile")
        if not profile:
            return {"error": "No profile provided", "success": False}
        json_path = f'agents/{profile}/elevenlabs_voice.json'
        try:
            config_str = await runtime.read_file(json_path)
            config = json.loads(config_str)
            voice_id = config.get("voice_id")
            if not voice_id:
                raise ValueError("voice_id missing in config")
            model_id = config.get("model", "eleven_turbo_v2_5")
            stability = config.get("stability", 0.3)
            similarity_boost = config.get("similarity_boost", 0.75)
            style = config.get("style", 0.3)
            clarity_boost = config.get("clarity_boost", 0.2)
        except Exception as e:
            return {"error": f"Config error for {profile}: {str(e)}", "success": False}
        api_key = os.getenv("EL11_API_KEY")
        if not api_key:
            return {"error": "EL11_API_KEY missing", "success": False}
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {'xi-api-key': api_key, 'Content-Type': 'application/json'}
                data = {
            'text': text,
            'model_id': model_id,
            'voice_settings': {
                'stability': stability,
                'similarity_boost': similarity_boost,
                'style': style,
                'clarity_boost': clarity_boost
            }
        }
            'clarity_boost': clarity_boost
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=data, stream=True)
            if resp.status_code != 200:
                error_body = await resp.aread()
                return {"error": f'EL11 API error {resp.status_code}: {error_body[:500]}', "success": False}
            return StreamingResponse(resp.aiter_bytes(), media_type='audio/mpeg')
