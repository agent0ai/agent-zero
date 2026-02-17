import sys
import os
sys.path.insert(0, "/a0/python")

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__ )

try:
    from helpers.api import ApiHandler, Request, Response
    from flask import Response
    import httpx
    import json
except ImportError as e:
    log.error(f"Import failed: {e}")
    class ApiHandler(object): pass
    class Request(object):
        def json(self):
            return {}
    class Response(object): pass
    class El11Tts(ApiHandler): pass
    raise

class El11Tts(ApiHandler):
    def post(self, request):
        try:
            data = request.json()
            log.info("EL11 TTS post received")
        except Exception as e:
            log.error(f"JSON parse error: {e}")
            return {"error": "Invalid JSON", "success": False}

        text = data.get("text", "")
        if not text:
            return {"error": "No text provided", "success": False}

        profile = data.get("profile", "agent0")
        json_path = f"/a0/agents/{profile}/elevenlabs_voice.json"
        try:
            with open(json_path, "r") as f:
                config_str = f.read()
            config = json.loads(config_str)
            voice_id = config.get("voice_id")
            if not voice_id:
                raise ValueError("voice_id missing in config")
            model_id = config.get("model", "eleven_turbo_v2_5")
            stability = config.get("stability", 0.3)
            similarity_boost = config.get("similarity_boost", 0.75)
            style = config.get("style", 0.3)
            clarity_boost = config.get("clarity_boost", 0.2)
            log.info(f"Loaded config for {profile}: voice_id={voice_id}")
        except Exception as e:
            log.error(f"Config error for {profile}: {str(e)}")
            return {"error": f"Config error for {profile}: {str(e)}", "success": False}

        api_key = os.getenv("EL11_API_KEY") or "sk_d97720987169e8b8ea1cc13a6dbc2fb1a16aae6268663882"
        if not api_key:
            log.error("EL11_API_KEY missing")
            return {"error": "EL11_API_KEY missing", "success": False}

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "clarity_boost": clarity_boost
            }
        }
        try:
            resp = httpx.post(url, headers=headers, json=payload, stream=True)
            if resp.status_code != 200:
                error_body = resp.text[:500]
                log.error(f"EL11 API error {resp.status_code}: {error_body}")
                return {"error": f"EL11 API error {resp.status_code}: {error_body}", "success": False}
            log.info("EL11 TTS stream success")

            def generate():
                for chunk in resp.iter_bytes(chunk_size=8192):
                    yield chunk
            return Response(generate(), mimetype="audio/mpeg")
        except Exception as e:
            log.error(f"TTS request error: {e}")
            return {"error": f"TTS request error: {str(e)}", "success": False}