from __future__ import annotations

import base64
import io
import json
import re
import threading
from pathlib import Path

import numpy as np
import soundfile as sf

from helpers import files

MODEL_REPO = "sahilmahendrakar/Paradee-8M-v1.0"
MODEL_REVISION = "v1.0"
SAMPLE_RATE = 24000
MAX_PHONEMES = 510

_model = None
_loading = False
_lock = threading.Lock()


def model_status() -> dict:
    return {"ready": _model is not None, "loading": _loading}


def preload():
    with _lock:
        return _load_model()


def _load_model():
    global _model, _loading
    if _model is not None:
        return _model
    _loading = True
    try:
        _model = _initialize_model()
        return _model
    finally:
        _loading = False


def _initialize_model():
    import onnxruntime as ort
    import spacy
    from huggingface_hub import hf_hub_download
    from misaki import en, espeak

    if not spacy.util.is_package("en_core_web_sm"):
        raise RuntimeError("The English phonemizer model is missing. Re-enable Local TTS to retry dependency setup.")

    model_dir = Path(files.get_abs_path("usr/plugins/_kokoro_tts/paradee"))
    for filename in ("config.json", "onnx/paradee_int8.onnx"):
        if not (model_dir / filename).is_file():
            hf_hub_download(
                MODEL_REPO, filename, revision=MODEL_REVISION,
                local_dir=str(model_dir),
            )

    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    if config.get("sample_rate") != SAMPLE_RATE:
        raise ValueError("Unexpected Paradee model sample rate.")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(model_dir / "onnx/paradee_int8.onnx"), options,
        providers=["CPUExecutionProvider"],
    )
    g2p = en.G2P(
        trf=False, british=False,
        fallback=espeak.EspeakFallback(british=False), unk="",
    )
    return session, g2p, config["vocab"]


def _phoneme_chunks(text, g2p):
    for sentence in re.split(r"(?<=[.!?…])\s+|\n+", text.strip()):
        if not sentence.strip():
            continue
        phonemes, _ = g2p(sentence)
        while len(phonemes) > MAX_PHONEMES:
            cut = phonemes.rfind(" ", 0, MAX_PHONEMES)
            cut = cut if cut > 0 else MAX_PHONEMES
            yield phonemes[:cut]
            phonemes = phonemes[cut:].lstrip()
        if phonemes:
            yield phonemes


def synthesize(text: str, speed: float) -> str:
    with _lock:
        session, g2p, vocab = _load_model()
        parts = []
        for phonemes in _phoneme_chunks(text, g2p):
            ids = [vocab[c] for c in phonemes if c in vocab]
            if not ids:
                continue
            waveform = session.run(None, {
                "input_ids": np.array([[0, *ids, 0]], dtype=np.int64),
                "speed": np.array([speed], dtype=np.float32),
            })[0][0]
            parts.append(waveform)
        if not parts:
            raise ValueError("Text contains no speakable English content.")
        audio = np.concatenate(parts)
        if not audio.size or not np.isfinite(audio).all():
            raise ValueError("Paradee returned invalid audio.")
        buffer = io.BytesIO()
        sf.write(buffer, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
