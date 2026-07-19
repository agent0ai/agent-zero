from __future__ import annotations

from plugins._kokoro_tts.helpers import migration, runtime


def get_plugin_config(default=None, **kwargs):
    migration.ensure_migrated()
    return runtime.normalize_config(default or {})


def save_plugin_config(default=None, settings=None, **kwargs):
    return runtime.normalize_config(settings or default or {})
