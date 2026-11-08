import base64
import importlib.metadata
import numpy as np
import whisper

model = None
model_name = ''


def handle(payload):
    global model, model_name
    requested = payload['model']
    if requested not in whisper.available_models():
        raise ValueError('Unsupported Whisper model')
    if model is None or model_name != requested:
        model = whisper.load_model(requested, device='cpu', download_root='/var/lib/a0-models/whisper')
        model_name = requested
    result = {'version': importlib.metadata.version('openai-whisper')}
    if payload['action'] == 'transcribe':
        samples = np.frombuffer(base64.b64decode(payload['audio'], validate=True), dtype='<f4').copy()
        if not 0 < len(samples) <= 16000 * 120 or not np.isfinite(samples).all() or np.any(np.abs(samples) > 1):
            raise ValueError('Invalid PCM samples')
        result['transcript'] = model.transcribe(samples, fp16=False, language=payload.get('language'))
    return result
