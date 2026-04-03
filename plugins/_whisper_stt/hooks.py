from __future__ import annotations

from helpers.defer import DeferredTask
from plugins._whisper_stt.helpers import migration, runtime


def get_plugin_config(default=None, **kwargs):
    migration.ensure_config_seeded()
    return runtime.normalize_config(default or {})


def save_plugin_config(default=None, settings=None, **kwargs):
    migration.ensure_config_seeded()

    normalized = runtime.normalize_config(settings or default or {})
    previous = runtime.normalize_config(migration.read_saved_config())

    previous_model = str(previous.get("model_size") or "")
    next_model = str(normalized.get("model_size") or "")
    if next_model and next_model != previous_model:
        DeferredTask().start_task(runtime.preload, next_model)

    return normalized
