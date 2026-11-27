from __future__ import annotations

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
        runtime.worker.stop()

    return normalized


def disable():
    runtime.worker.stop()


def uninstall():
    runtime.worker.stop()
    from helpers.sandbox import get_manager
    manager = get_manager()
    if (manager.config.instances_dir / runtime.worker.name / 'metadata.json').exists():
        manager.delete(runtime.worker.name)
