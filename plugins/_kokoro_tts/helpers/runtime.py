from __future__ import annotations

import asyncio
import base64
import io
import warnings
from typing import Any

import aiohttp
import soundfile as sf

from helpers import plugins
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
    "speed": 1.1,
    "remote_url": "",
    "response_format": "mp3",
}

VALID_FORMATS = {"wav", "mp3", "opus", "flac"}
MIME_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "opus": "audio/opus",
    "flac": "audio/flac",
}

_pipeline = None
is_updating_model = False


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(DEFAULT_CONFIG)
    if not isinstance(config, dict):
        return normalized

    voice = str(config.get("voice", normalized["voice"]) or "").strip()
    if voice:
        normalized["voice"] = voice

    try:
        speed = float(config.get("speed", normalized["speed"]))
        if speed > 0:
            normalized["speed"] = speed
    except (TypeError, ValueError):
        pass

    remote_url = str(config.get("remote_url", normalized["remote_url"]) or "").strip()
    if remote_url:
        normalized["remote_url"] = remote_url.rstrip("/")

    response_format = str(config.get("response_format", normalized["response_format"]) or "").strip().lower()
    if response_format in VALID_FORMATS:
        normalized["response_format"] = response_format

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
    return await _preload()


async def _preload():
    global _pipeline, is_updating_model

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _pipeline:
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Loading Kokoro TTS model...",
                display_time=99,
                group="kokoro-preload",
            )
            PrintStyle.standard("Loading Kokoro TTS model...")
            from kokoro import KPipeline

            _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Kokoro TTS model loaded.",
                display_time=2,
                group="kokoro-preload",
            )
    finally:
        is_updating_model = False


async def is_downloading() -> bool:
    return is_updating_model


async def is_downloaded() -> bool:
    return _pipeline is not None


async def is_remote_healthy() -> tuple[bool, str]:
    """Check if the remote Kokoro-FastAPI server is reachable.

    Returns (healthy, error_message). If no remote_url is configured,
    returns (False, "Not configured").
    """
    cfg = get_config()
    remote_url = cfg.get("remote_url", "")
    if not remote_url:
        return False, "Not configured"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{remote_url}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    return True, ""
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)


async def synthesize_sentences(
    sentences: list[str], config: dict[str, Any] | None = None
) -> tuple[str, str]:
    cfg = normalize_config(config or get_config())
    remote_url = str(cfg.get("remote_url", ""))

    if remote_url:
        return await _synthesize_remote(
            sentences,
            voice=str(cfg["voice"]),
            speed=float(cfg["speed"]),
            remote_url=remote_url,
            response_format=str(cfg["response_format"]),
        )

    return await _synthesize_local(
        sentences,
        voice=str(cfg["voice"]),
        speed=float(cfg["speed"]),
    )


async def _synthesize_remote(
    sentences: list[str],
    *,
    voice: str,
    speed: float,
    remote_url: str,
    response_format: str,
) -> tuple[str, str]:
    text = " ".join(s.strip() for s in sentences if s.strip())
    if not text:
        return "", MIME_TYPES.get(response_format, "audio/mpeg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{remote_url}/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": text,
                    "voice": voice,
                    "response_format": response_format,
                    "speed": speed,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                audio_bytes = await resp.read()
                mime_type = MIME_TYPES.get(response_format, "audio/mpeg")
                return base64.b64encode(audio_bytes).decode("utf-8"), mime_type
    except Exception as e:
        PrintStyle.error(f"Error in remote Kokoro TTS synthesis: {e}")
        raise


async def _synthesize_local(
    sentences: list[str], *, voice: str, speed: float
) -> tuple[str, str]:
    await _preload()

    combined_audio: list[float] = []

    try:
        for sentence in sentences:
            if not sentence.strip():
                continue

            segments = _pipeline(sentence.strip(), voice=voice, speed=speed)  # type: ignore[misc]
            for segment in list(segments):
                audio_tensor = segment.audio
                audio_numpy = audio_tensor.detach().cpu().numpy()  # type: ignore[union-attr]
                combined_audio.extend(audio_numpy.tolist())

        if not combined_audio:
            return "", "audio/wav"

        buffer = io.BytesIO()
        sf.write(buffer, combined_audio, 24000, format="WAV")
        return base64.b64encode(buffer.getvalue()).decode("utf-8"), "audio/wav"
    except Exception as e:
        PrintStyle.error(f"Error in local Kokoro TTS synthesis: {e}")
        raise
