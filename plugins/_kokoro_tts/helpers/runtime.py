from __future__ import annotations

import asyncio
import base64
import io
import math
import os
import re
import urllib.request
import warnings
from typing import Any

import soundfile as sf

from helpers import files, plugins
from helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from helpers.print_style import PrintStyle
from plugins._kokoro_tts.helpers import migration


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


PLUGIN_NAME = "_kokoro_tts"
DEFAULT_CONFIG = {
    "voice": "am_puck,am_onyx",
    "voice_weights": {},
    "speed": 1.1,
    "engine": "kokoro_py",       # kokoro_py | kokoro_onnx
    "lang": "en-us",             # espeak-ng language code: en-us, de, fr, es, it, etc.
    "onnx_hf_repo": "",          # HuggingFace repo ID for ONNX model download
    "onnx_model_file": "",       # filename in repo, e.g. kokoro-martin.onnx
    "onnx_voices_file": "",      # filename in repo, e.g. voices-martin.npz
    "onnx_mixed_lang": "en-us",  # secondary espeak-ng language for matched terms
    "onnx_mixed_lang_terms": "", # comma/newline-separated terms to phonemize with secondary language
}
VOICE_ID_PATTERN = re.compile(r"^[a-z]{2}_[a-z0-9_]+$")

# Map espeak-ng language codes to kokoro-py KPipeline lang_code
_ESPEAK_TO_KOKORO_LANG = {
    "en-us": "a",
    "en-gb": "b",
    "ja": "j",
    "zh": "z",
    "ko": "k",
}

_pipeline = None
_pipeline_lang_code: str | None = None
_onnx_pipeline = None
is_updating_model = False


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    normalized = {**DEFAULT_CONFIG, "voice_weights": {}}
    if not isinstance(config, dict):
        return normalized

    voice = str(config.get("voice", normalized["voice"]) or "").strip()
    if voice:
        normalized["voice"] = voice

    weights = config.get("voice_weights")
    if isinstance(weights, dict):
        for raw_voice, raw_weight in weights.items():
            voice_id = str(raw_voice or "").strip()
            if not VOICE_ID_PATTERN.fullmatch(voice_id):
                continue
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                continue
            if math.isfinite(weight) and weight > 0:
                normalized["voice_weights"][voice_id] = weight

    if normalized["voice_weights"]:
        normalized["voice"] = ",".join(normalized["voice_weights"])

    try:
        speed = float(config.get("speed", normalized["speed"]))
        if math.isfinite(speed) and speed > 0:
            normalized["speed"] = speed
    except (TypeError, ValueError):
        pass

    # Engine selection
    engine = str(config.get("engine", normalized["engine"]) or "").strip().lower()
    if engine in ("kokoro_py", "kokoro_onnx"):
        normalized["engine"] = engine

    # Language code (espeak-ng format)
    lang = str(config.get("lang", normalized["lang"]) or "").strip().lower()
    if lang:
        normalized["lang"] = lang

    # ONNX HuggingFace repo and filenames
    for key in ("onnx_hf_repo", "onnx_model_file", "onnx_voices_file"):
        val = str(config.get(key, normalized[key]) or "").strip()
        normalized[key] = val

    mixed_lang = str(config.get("onnx_mixed_lang", normalized["onnx_mixed_lang"]) or "").strip().lower()
    if mixed_lang:
        normalized["onnx_mixed_lang"] = mixed_lang
    normalized["onnx_mixed_lang_terms"] = str(
        config.get("onnx_mixed_lang_terms", normalized["onnx_mixed_lang_terms"]) or ""
    ).strip()

    return normalized


def get_config() -> dict[str, Any]:
    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    return normalize_config(config)


def is_globally_enabled() -> bool:
    migration.ensure_migrated()
    return plugins.determined_toggle_from_paths(
        True, reversed(plugins.get_plugin_roots(PLUGIN_NAME))
    )


async def preload(config: dict[str, Any] | None = None):
    cfg = normalize_config(config or get_config())
    if cfg["engine"] == "kokoro_onnx":
        return await _preload_onnx(cfg)
    return await _preload(cfg)


async def _preload(config: dict[str, Any] | None = None):
    global _pipeline, _pipeline_lang_code, is_updating_model

    cfg = normalize_config(config or get_config())
    lang_code = _ESPEAK_TO_KOKORO_LANG.get(
        cfg["lang"], cfg["lang"][0] if cfg["lang"] else "a"
    )

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if _pipeline is None or _pipeline_lang_code != lang_code:
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Loading Kokoro TTS model...",
                display_time=99,
                group="kokoro-preload",
            )
            PrintStyle.standard("Loading Kokoro TTS model...")
            from kokoro import KPipeline

            _pipeline = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")
            _pipeline_lang_code = lang_code
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Kokoro TTS model loaded.",
                display_time=2,
                group="kokoro-preload",
            )
    finally:
        is_updating_model = False


def _detect_hf_files(hf_repo: str) -> tuple[str, str]:
    """Auto-detect ONNX model and voices filenames from a HuggingFace repo.

    Returns ``(model_file, voices_file)``.  Raises :class:`ValueError` if
    either file cannot be found.
    """
    import json

    url = f"https://huggingface.co/api/models/{hf_repo}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())

    files = [s["rfilename"] for s in data.get("siblings", [])]

    # Find model: prefer full-precision .onnx
    onnx_files = [f for f in files if f.endswith(".onnx")]
    if not onnx_files:
        raise ValueError(f"No .onnx file found in {hf_repo}")
    model_file = next(
        (
            f
            for f in onnx_files
            if not any(q in f.lower() for q in ("int8", "quantized", "fp16", "q8"))
        ),
        onnx_files[0],
    )

    # Find voices: .npz or .bin (but not .onnx)
    voices_files = [
        f
        for f in files
        if f.endswith(".npz") or (f.endswith(".bin") and not f.endswith(".onnx"))
    ]
    if not voices_files:
        raise ValueError(f"No voices file (.npz or .bin) found in {hf_repo}")
    # Prefer .npz over .bin
    npz = [f for f in voices_files if f.endswith(".npz")]
    voices_file = npz[0] if npz else voices_files[0]

    return model_file, voices_file


async def _ensure_onnx_model(cfg: dict[str, Any]) -> tuple[str, str]:
    """Ensure ONNX model and voices files are available locally.

    Downloads from HuggingFace if ``onnx_hf_repo`` is set and files are not yet cached.
    Returns ``(model_path, voices_path)``. Returns empty strings if ``onnx_hf_repo``
    is empty (files must exist locally in that case).
    """
    hf_repo = cfg.get("onnx_hf_repo", "")
    model_file = cfg.get("onnx_model_file", "")
    voices_file = cfg.get("onnx_voices_file", "")

    if not hf_repo:
        return "", ""

    if hf_repo and (not model_file or not voices_file):
        detected_model, detected_voices = _detect_hf_files(hf_repo)
        if not model_file:
            model_file = detected_model
        if not voices_file:
            voices_file = detected_voices

    sanitized = hf_repo.replace("/", "_")
    cache_dir = files.get_abs_path("usr/models", sanitized)
    model_path = os.path.join(cache_dir, model_file) if model_file else ""
    voices_path = os.path.join(cache_dir, voices_file) if voices_file else ""

    model_ok = bool(model_path) and os.path.isfile(model_path)
    voices_ok = bool(voices_path) and os.path.isfile(voices_path)

    if model_ok and voices_ok:
        return model_path, voices_path

    os.makedirs(cache_dir, exist_ok=True)

    if not model_ok and model_file:
        url = f"https://huggingface.co/{hf_repo}/resolve/main/{model_file}"
        PrintStyle.standard(f"Downloading ONNX model: {url}")
        NotificationManager.send_notification(
            NotificationType.INFO,
            NotificationPriority.NORMAL,
            "Downloading ONNX model from HuggingFace...",
            display_time=99,
            group="kokoro-onnx-download",
        )
        urllib.request.urlretrieve(url, model_path)

    if not voices_ok and voices_file:
        url = f"https://huggingface.co/{hf_repo}/resolve/main/{voices_file}"
        PrintStyle.standard(f"Downloading ONNX voices: {url}")
        urllib.request.urlretrieve(url, voices_path)

    NotificationManager.send_notification(
        NotificationType.INFO,
        NotificationPriority.NORMAL,
        "ONNX model download complete.",
        display_time=2,
        group="kokoro-onnx-download",
    )

    return model_path, voices_path


async def _preload_onnx(config: dict[str, Any]):
    global _onnx_pipeline, is_updating_model

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _onnx_pipeline:
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Loading Kokoro ONNX TTS model...",
                display_time=99,
                group="kokoro-onnx-preload",
            )
            PrintStyle.standard("Loading Kokoro ONNX TTS model...")

            model_path, voices_path = await _ensure_onnx_model(config)

            if not model_path or not voices_path:
                raise ValueError(
                    "ONNX engine requires onnx_hf_repo, onnx_model_file, and "
                    "onnx_voices_file to be configured, or model files to exist locally."
                )

            from kokoro_onnx import Kokoro

            _onnx_pipeline = Kokoro(model_path, voices_path)

            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Kokoro ONNX TTS model loaded.",
                display_time=2,
                group="kokoro-onnx-preload",
            )
    finally:
        is_updating_model = False


async def is_downloading() -> bool:
    return is_updating_model


async def is_downloaded() -> bool:
    cfg = get_config()
    if cfg.get("engine") == "kokoro_onnx":
        return _onnx_pipeline is not None
    return _pipeline is not None


async def synthesize_sentences(
    sentences: list[str], config: dict[str, Any] | None = None
) -> str:
    cfg = normalize_config(config or get_config())
    return await _synthesize_sentences(sentences, cfg=cfg)


def _resolve_voice(
    pipeline: Any, voice: str, voice_weights: dict[str, float]
) -> Any:
    if not voice_weights:
        return voice

    total = sum(voice_weights.values())
    if not math.isfinite(total) or total <= 0:
        return voice
    blend = None
    for voice_id, weight in voice_weights.items():
        weighted_pack = pipeline.load_single_voice(voice_id) * (weight / total)
        blend = weighted_pack if blend is None else blend + weighted_pack
    return blend


async def _synthesize_sentences(
    sentences: list[str], *, cfg: dict[str, Any]
) -> str:
    if cfg["engine"] == "kokoro_onnx":
        return await _synthesize_onnx(sentences, cfg=cfg)
    return await _synthesize_kokoro_py(sentences, cfg=cfg)


async def _synthesize_kokoro_py(
    sentences: list[str], *, cfg: dict[str, Any]
) -> str:
    await _preload(cfg)

    voice = str(cfg["voice"])
    voice_weights = dict(cfg["voice_weights"])
    speed = float(cfg["speed"])

    combined_audio: list[float] = []
    resolved_voice = _resolve_voice(_pipeline, voice, voice_weights)

    try:
        for sentence in sentences:
            if not sentence.strip():
                continue

            segments = _pipeline(  # type: ignore[misc]
                sentence.strip(), voice=resolved_voice, speed=speed
            )
            for segment in list(segments):
                audio_tensor = segment.audio
                audio_numpy = audio_tensor.detach().cpu().numpy()  # type: ignore[union-attr]
                combined_audio.extend(audio_numpy.tolist())

        if not combined_audio:
            return ""

        return _encode_wav_base64(combined_audio)
    except Exception as e:
        PrintStyle.error(f"Error in Kokoro TTS synthesis: {e}")
        raise


def _encode_wav_base64(samples: list[float]) -> str:
    buffer = io.BytesIO()
    sf.write(buffer, samples, 24000, format="WAV")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _parse_mixed_lang_terms(raw_terms: str) -> list[str]:
    terms = [term.strip() for term in re.split(r"[,\n]", raw_terms) if term.strip()]
    return sorted(dict.fromkeys(terms), key=len, reverse=True)


def _mixed_lang_phonemes(
    pipeline: Any, text: str, *, primary_lang: str, mixed_lang: str, terms: list[str]
) -> str:
    if not terms:
        return pipeline.tokenizer.phonemize(text, primary_lang)

    pattern = re.compile(
        r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(term) for term in terms) + r")(?![A-Za-z0-9_])",
        re.IGNORECASE,
    )
    phoneme_parts: list[str] = []
    last_end = 0
    for match in pattern.finditer(text):
        if match.start() > last_end:
            phoneme_parts.append(
                pipeline.tokenizer.phonemize(text[last_end : match.start()], primary_lang)
            )
        phoneme_parts.append(pipeline.tokenizer.phonemize(match.group(0), mixed_lang))
        last_end = match.end()
    if last_end < len(text):
        phoneme_parts.append(pipeline.tokenizer.phonemize(text[last_end:], primary_lang))
    return " ".join(part for part in phoneme_parts if part)


async def _synthesize_onnx(
    sentences: list[str], *, cfg: dict[str, Any]
) -> str:
    await _preload_onnx(cfg)

    voice = str(cfg["voice"])
    speed = float(cfg["speed"])
    lang = str(cfg["lang"])
    mixed_lang = str(cfg["onnx_mixed_lang"])
    mixed_terms = _parse_mixed_lang_terms(str(cfg["onnx_mixed_lang_terms"]))

    combined_audio: list[float] = []

    try:
        for sentence in sentences:
            text = sentence.strip()
            if not text:
                continue

            if mixed_terms:
                text = _mixed_lang_phonemes(
                    _onnx_pipeline,
                    text,
                    primary_lang=lang,
                    mixed_lang=mixed_lang,
                    terms=mixed_terms,
                )
                samples, sample_rate = _onnx_pipeline.create(
                    text, voice=voice, speed=speed, lang=lang, is_phonemes=True
                )
            else:
                samples, sample_rate = _onnx_pipeline.create(
                    text, voice=voice, speed=speed, lang=lang
                )
            combined_audio.extend(samples.tolist())

        if not combined_audio:
            return ""

        return _encode_wav_base64(combined_audio)
    except Exception as e:
        PrintStyle.error(f"Error in Kokoro ONNX TTS synthesis: {e}")
        raise
