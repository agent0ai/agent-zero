import base64
import importlib.metadata
import io
import hashlib
from pathlib import Path
import numpy as np
import soundfile as sf

from plugins._kokoro_tts.sandbox import paradee
from plugins._kokoro_tts.sandbox.voices import _resolve_voice

pipeline = None


def handle(payload):
    global pipeline
    config = payload['config']
    for voice, encoded in payload.get('voice_files', {}).items():
        content = base64.b64decode(encoded, validate=True)
        path = Path('/var/lib/a0-models/voices') / (hashlib.sha256(content).hexdigest() + '.pt')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        config['voice'] = ','.join(str(path) if item == voice else item for item in config['voice'].split(','))
    if config['voice'] == 'paradee' and not config['voice_weights']:
        paradee.preload()
        result = {'version': importlib.metadata.version('onnxruntime')}
        if payload['action'] == 'synthesize':
            result['audio'] = paradee.synthesize('\n'.join(payload['sentences']), config['speed'])
        return result
    if pipeline is None:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    result = {'version': importlib.metadata.version('kokoro')}
    if payload['action'] == 'synthesize':
        voice = _resolve_voice(pipeline, config['voice'], config['voice_weights'])
        parts = []
        for sentence in payload['sentences']:
            if sentence.strip():
                for segment in pipeline(sentence.strip(), voice=voice, speed=config['speed']):
                    parts.append(segment.audio.detach().cpu().numpy())
        if parts:
            buffer = io.BytesIO()
            sf.write(buffer, np.concatenate(parts), 24000, format='WAV')
            result['audio'] = base64.b64encode(buffer.getvalue()).decode('ascii')
        else:
            result['audio'] = ''
    return result
