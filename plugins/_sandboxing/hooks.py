from __future__ import annotations

from plugins._sandboxing.helpers.runtime import normalize_config, reset_manager


def get_plugin_config(default=None, **kwargs):
    return normalize_config(default or {})


def save_plugin_config(settings=None, default=None, **kwargs):
    result = normalize_config(settings or default or {})
    reset_manager()
    return result
