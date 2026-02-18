from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from flask import Request, Response

from python.helpers.api import ApiHandler
from python.helpers import settings


class El11Tts(ApiHandler):
    """Proxy TTS requests to ElevenLabs and stream back audio."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        text = (input.get("text") or "").strip()
        if not text:
            return {"success": False, "error": "No text provided"}

        # Prefer explicit profile in request; fall back to active agent profile.
        profile = (
            (input.get("profile") or "").strip()
            or settings.get_settings().get("agent_profile", "agent0")
        )

        cfg_path = Path(f"/a0/agents/{profile}/elevenlabs_voice.json")
        if not cfg_path.exists():
            cfg_path = Path("/a0/agents/agent0/elevenlabs_voice.json")

        try:
            config = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read ElevenLabs config from {cfg_path}: {e}",
            }

        voice_id = (config.get("voice_id") or "").strip()
        model_id = (config.get("model") or "eleven_turbo_v2_5").strip()
        stability = float(config.get("stability", 0.3))
        similarity_boost = float(config.get("similarity_boost", 0.75))
        style = float(config.get("style", 0.3))

        if not voice_id:
            return {"success": False, "error": "voice_id missing in elevenlabs_voice.json"}

        api_key = (os.getenv("EL11_API_KEY") or "").strip()
        if not api_key:
            return {"success": False, "error": "EL11_API_KEY missing"}

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
            },
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)

            if resp.status_code != 200:
                err = resp.text[:1000]
                return {
                    "success": False,
                    "error": f"ElevenLabs API error {resp.status_code}: {err}",
                }

            return Response(resp.content, mimetype="audio/mpeg", status=200)

        except Exception as e:
            return {"success": False, "error": f"ElevenLabs request failed: {e}"}
