from __future__ import annotations

import json
from typing import Any

from helpers import files, plugins


PLUGIN_NAME = "_whisper_stt"
LEGACY_SETTINGS_FILE = files.get_abs_path("usr/settings.json")
DEFAULT_CONFIG = {
    "model_size": "base",
    "language": "en",
    "silence_threshold": 0.3,
    "silence_duration": 1000,
    "waiting_timeout": 2000,
}


def ensure_config_seeded() -> bool:
    config_path = get_config_path()
    if files.exists(config_path):
        return False

    config = build_seed_config(_read_legacy_settings())
    files.write_file(config_path, json.dumps(config, indent=2))
    return True


def get_config_path() -> str:
    return plugins.determine_plugin_asset_path(
        PLUGIN_NAME, "", "", plugins.CONFIG_FILE_NAME
    )


def read_saved_config() -> dict[str, Any]:
    config_path = get_config_path()
    if not files.exists(config_path):
        return {}

    try:
        return json.loads(files.read_file(config_path))
    except Exception:
        return {}


def build_seed_config(legacy_settings: dict[str, Any]) -> dict[str, Any]:
    seeded = dict(DEFAULT_CONFIG)

    model_size = str(
        legacy_settings.get("stt_model_size", seeded["model_size"]) or ""
    ).strip()
    if model_size:
        seeded["model_size"] = model_size

    language = str(legacy_settings.get("stt_language", seeded["language"]) or "").strip()
    if language:
        seeded["language"] = language

    seeded["silence_threshold"] = _coerce_float(
        legacy_settings.get("stt_silence_threshold"),
        seeded["silence_threshold"],
    )
    seeded["silence_duration"] = _coerce_int(
        legacy_settings.get("stt_silence_duration"),
        seeded["silence_duration"],
    )
    seeded["waiting_timeout"] = _coerce_int(
        legacy_settings.get("stt_waiting_timeout"),
        seeded["waiting_timeout"],
    )

    return seeded


def _read_legacy_settings() -> dict[str, Any]:
    if not files.exists(LEGACY_SETTINGS_FILE):
        return {}

    try:
        return json.loads(files.read_file(LEGACY_SETTINGS_FILE))
    except Exception:
        return {}


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
