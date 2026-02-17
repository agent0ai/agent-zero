from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import os
import requests

router = APIRouter()

@router.post('/')
def el11_tts(request: dict):
    profile = request.get('profile', 'evetz')
    text = request.get('text')
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Missing or empty 'text'")

    voice_id_path = os.path.join(os.path.dirname(__file__), '..', '..', 'agents', profile, 'voice_id.txt')
    try:
        with open(voice_id_path, 'r') as f:
            voice_id = f.read().strip()
        if not voice_id:
            raise ValueError('Empty voice_id')
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Voice ID config error for {profile}: {{str(exc)}}")

    api_key = os.getenv('EL11_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='EL11_API_KEY not configured')

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{{voice_id}}/stream'
    data = {
        'text': text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.5,
        }
    }

    resp = requests.post(url, headers={'xi-api-key': api_key, 'Content-Type': 'application/json'}, json=data, stream=True)
    resp.raise_for_status()

    def generate():
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    return StreamingResponse(generate(), media_type='audio/mpeg')
