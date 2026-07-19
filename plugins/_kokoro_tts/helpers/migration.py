from __future__ import annotations

import json

from helpers import files, plugins


PLUGIN_NAME = "_kokoro_tts"
LEGACY_SETTINGS_FILE = files.get_abs_path("usr/settings.json")


def ensure_migrated() -> bool:
    legacy_settings = _read_legacy_settings()
    legacy_enabled = _coerce_bool(legacy_settings.get("tts_kokoro"), default=True)
    if legacy_enabled or _has_explicit_toggle():
        return False

    disabled_path = plugins.determine_plugin_asset_path(
        PLUGIN_NAME, "", "", plugins.DISABLED_FILE_NAME
    )
    files.write_file(disabled_path, "")
    plugins.clear_plugin_cache([PLUGIN_NAME])
    return True


def _has_explicit_toggle() -> bool:
    for root in plugins.get_plugin_roots(PLUGIN_NAME):
        if files.exists(files.get_abs_path(root, plugins.ENABLED_FILE_NAME)):
            return True
        if files.exists(files.get_abs_path(root, plugins.DISABLED_FILE_NAME)):
            return True
    return False


def _read_legacy_settings() -> dict:
    if not files.exists(LEGACY_SETTINGS_FILE):
        return {}

    try:
        return json.loads(files.read_file(LEGACY_SETTINGS_FILE))
    except Exception:
        return {}


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return default
