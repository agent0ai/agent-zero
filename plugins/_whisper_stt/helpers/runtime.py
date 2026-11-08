from __future__ import annotations

import asyncio
import base64
import warnings
from typing import Any

import numpy as np

from helpers import plugins
from helpers.sandbox_worker import SandboxWorker
from helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from helpers.print_style import PrintStyle
from plugins._whisper_stt.helpers import migration

warnings.filterwarnings("ignore", category=FutureWarning)


PLUGIN_NAME = "_whisper_stt"
DEFAULT_CONFIG = {
    "model_size": "base",
    "language": "en",
    "message_mode": "send",
    "silence_threshold": 0.3,
    "silence_duration": 1000,
    "waiting_timeout": 2000,
}
VALID_MODEL_SIZES = {"tiny", "base", "small", "medium", "large", "turbo"}
VALID_MESSAGE_MODES = {"send", "draft"}

AUDIO_WIRE_VERSION = 1
AUDIO_SAMPLE_RATE = 16_000
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_FORMAT = "f32le"
AUDIO_MAX_DURATION_SECONDS = 120
AUDIO_MAX_FRAMES = AUDIO_SAMPLE_RATE * AUDIO_MAX_DURATION_SECONDS
AUDIO_BYTES_PER_SAMPLE = 4
AUDIO_MAX_BYTES = AUDIO_MAX_FRAMES * AUDIO_BYTES_PER_SAMPLE
AUDIO_MAX_BASE64_CHARS = ((AUDIO_MAX_BYTES + 2) // 3) * 4

worker = SandboxWorker(PLUGIN_NAME)
package_version = ""
_model_name = ""
is_updating_model = False


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(DEFAULT_CONFIG)
    if not isinstance(config, dict):
        return normalized

    model_size = str(config.get("model_size", normalized["model_size"]) or "").strip()
    if model_size in VALID_MODEL_SIZES:
        normalized["model_size"] = model_size

    language = str(config.get("language", normalized["language"]) or "").strip()
    if language:
        normalized["language"] = language

    message_mode = (
        str(config.get("message_mode", normalized["message_mode"]) or "")
        .strip()
        .lower()
    )
    if message_mode in VALID_MESSAGE_MODES:
        normalized["message_mode"] = message_mode

    try:
        silence_threshold = float(
            config.get("silence_threshold", normalized["silence_threshold"])
        )
        normalized["silence_threshold"] = min(max(silence_threshold, 0.0), 1.0)
    except (TypeError, ValueError):
        pass

    try:
        silence_duration = int(
            config.get("silence_duration", normalized["silence_duration"])
        )
        if silence_duration > 0:
            normalized["silence_duration"] = silence_duration
    except (TypeError, ValueError):
        pass

    try:
        waiting_timeout = int(
            config.get("waiting_timeout", normalized["waiting_timeout"])
        )
        if waiting_timeout > 0:
            normalized["waiting_timeout"] = waiting_timeout
    except (TypeError, ValueError):
        pass

    return normalized


def get_config() -> dict[str, Any]:
    migration.ensure_config_seeded()
    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    return normalize_config(config)


def get_loaded_model_name() -> str:
    return _model_name if worker.ready else ""


def is_globally_enabled() -> bool:
    return plugins.determined_toggle_from_paths(
        True, reversed(plugins.get_plugin_roots(PLUGIN_NAME))
    )


async def preload(model_name: str | None = None):
    cfg = get_config()
    resolved_model = str(model_name or cfg["model_size"])
    return await _preload(resolved_model)


async def _preload(model_name: str):
    global _model_name, is_updating_model, package_version
    is_updating_model = True
    try:
        result = await worker.acall({'action': 'preload', 'model': model_name}, timeout=600)
        _model_name = model_name
        package_version = result['version']
    finally:
        is_updating_model = False


async def is_downloading() -> bool:
    return is_updating_model


async def is_downloaded() -> bool:
    return worker.ready and bool(_model_name)


async def transcribe(
    audio_payload: dict[str, Any], config: dict[str, Any] | None = None
) -> dict[str, Any]:
    cfg = normalize_config(config or get_config())
    audio_samples = decode_audio_payload(audio_payload)
    return await _transcribe(
        str(cfg["model_size"]),
        audio_samples,
        language=_resolve_language(str(cfg["language"])),
    )


async def _transcribe(
    model_name: str, audio_samples: np.ndarray, *, language: str | None = None
) -> dict[str, Any]:
    global _model_name, is_updating_model, package_version
    is_updating_model = True
    try:
        result = await worker.acall({
            'action': 'transcribe', 'model': model_name, 'language': language,
            'audio': base64.b64encode(audio_samples.astype('<f4').tobytes()).decode('ascii'),
        }, timeout=600)
        _model_name = model_name
        package_version = result['version']
        return result['transcript']
    finally:
        is_updating_model = False


class AudioPayloadError(ValueError):
    """Raised when the bounded PCM wire contract is invalid."""


def decode_audio_payload(payload: dict[str, Any]) -> np.ndarray:
    """Validate PCM v1 and return Whisper-ready mono float32 samples."""

    if not isinstance(payload, dict):
        raise AudioPayloadError("Audio payload must be an object")
    if payload.get("version") != AUDIO_WIRE_VERSION:
        raise AudioPayloadError("Unsupported audio payload version")
    if payload.get("sample_rate") != AUDIO_SAMPLE_RATE:
        raise AudioPayloadError("Unsupported audio sample rate")
    if payload.get("channels") != AUDIO_CHANNELS:
        raise AudioPayloadError("Unsupported audio channel count")
    if payload.get("sample_format") != AUDIO_SAMPLE_FORMAT:
        raise AudioPayloadError("Unsupported audio sample format")

    frame_count = payload.get("frame_count")
    if isinstance(frame_count, bool) or not isinstance(frame_count, int):
        raise AudioPayloadError("Audio frame count must be an integer")
    if frame_count <= 0:
        raise AudioPayloadError("Audio payload is empty")
    if frame_count > AUDIO_MAX_FRAMES:
        raise AudioPayloadError("Audio duration exceeds 120 seconds")

    encoded = payload.get("data")
    if not isinstance(encoded, str) or not encoded:
        raise AudioPayloadError("Audio data must be base64 text")
    if len(encoded) > AUDIO_MAX_BASE64_CHARS:
        raise AudioPayloadError("Audio payload exceeds the byte limit")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise AudioPayloadError("Audio data is not valid base64") from exc

    expected_bytes = frame_count * AUDIO_BYTES_PER_SAMPLE
    if len(raw) != expected_bytes:
        raise AudioPayloadError("Audio data length does not match frame count")
    if len(raw) > AUDIO_MAX_BYTES:
        raise AudioPayloadError("Audio payload exceeds the byte limit")

    samples = np.frombuffer(raw, dtype="<f4")
    if not np.isfinite(samples).all():
        raise AudioPayloadError("Audio samples must be finite")
    if np.any(np.abs(samples) > 1.0):
        raise AudioPayloadError("Audio samples must be normalized")

    # Whisper accepts a 16 kHz mono float32 ndarray and therefore skips load_audio,
    # the only path in openai-whisper that launches ffmpeg.
    return np.array(samples, dtype=np.float32, copy=True, order="C")


def _resolve_language(language: str) -> str | None:
    value = language.strip().lower()
    if not value or value == "auto":
        return None
    return value
