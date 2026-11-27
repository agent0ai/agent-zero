from __future__ import annotations

import asyncio
import base64
import io
import math
import re
import warnings
from pathlib import Path
from typing import Any


from helpers import plugins
from helpers.sandbox_worker import SandboxWorker
from helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from helpers.print_style import PrintStyle
from plugins._kokoro_tts.helpers import migration
from plugins._kokoro_tts.sandbox.voices import _resolve_voice


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


PLUGIN_NAME = "_kokoro_tts"
DEFAULT_CONFIG = {
    "voice": "paradee",
    "voice_weights": {},
    "speed": 1.1,
}
VOICE_ID_PATTERN = re.compile(r"^[a-z]{2}_[a-z0-9_]+$")

worker = SandboxWorker(PLUGIN_NAME)
_loaded_engines = set()
_model_generation = -1
package_versions = {}
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
    else:
        voices = [part.strip() for part in normalized["voice"].split(",")]
        if any(voice.lower() == "paradee" for voice in voices):
            normalized["voice"] = ",".join(
                voice for voice in voices if voice and voice.lower() != "paradee"
            ) or "paradee"

    try:
        speed = float(config.get("speed", normalized["speed"]))
        if math.isfinite(speed) and speed > 0:
            normalized["speed"] = speed
    except (TypeError, ValueError):
        pass

    return normalized


def get_config() -> dict[str, Any]:
    config = plugins.get_plugin_config(PLUGIN_NAME) or {}
    return normalize_config(config)


def is_globally_enabled() -> bool:
    migration.ensure_migrated()
    return plugins.determined_toggle_from_paths(
        True, reversed(plugins.get_plugin_roots(PLUGIN_NAME))
    )


async def _request(action, config, sentences=None):
    global is_updating_model, _model_generation
    cfg = normalize_config(config)
    engine = 'paradee' if cfg['voice'] == 'paradee' else 'kokoro'
    is_updating_model = True
    try:
        voice_files = {}
        if not cfg['voice_weights']:
            from helpers import files
            for voice in cfg['voice'].split(','):
                if voice.endswith('.pt'):
                    path = Path(files.fix_dev_path(voice))
                    if not path.is_absolute():
                        path = Path(files.get_abs_path(str(path)))
                    voice_files[voice] = base64.b64encode(path.read_bytes()).decode('ascii')
        result = await worker.acall({'action': action, 'config': cfg, 'sentences': sentences or [],
                                    'voice_files': voice_files}, timeout=600)
        if _model_generation != worker.generation:
            _loaded_engines.clear()
            _model_generation = worker.generation
        _loaded_engines.add(engine)
        package_versions[engine] = result['version']
        return result.get('audio', '')
    finally:
        is_updating_model = False


async def preload(config=None):
    return await _request('preload', config if config is not None else get_config())


async def is_downloading(config=None):
    return is_updating_model


async def is_downloaded(config=None):
    cfg = normalize_config(config if config is not None else get_config())
    engine = 'paradee' if cfg['voice'] == 'paradee' else 'kokoro'
    return worker.ready and _model_generation == worker.generation and engine in _loaded_engines


async def synthesize_sentences(sentences, config=None):
    return await _request('synthesize', config if config is not None else get_config(), sentences)
