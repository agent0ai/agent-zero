from plugins._kokoro_tts.helpers import migration, runtime


def install():
    return True


def ensure_dependencies(raise_on_error=True):
    return True


def get_plugin_config(default=None, **kwargs):
    migration.ensure_migrated()
    return runtime.normalize_config(default or {})


def save_plugin_config(default=None, settings=None, **kwargs):
    return runtime.normalize_config(settings or default or {})


def disable():
    runtime.worker.stop()


def uninstall():
    runtime.worker.stop()
    from helpers.sandbox import get_manager
    manager = get_manager()
    if (manager.config.instances_dir / runtime.worker.name / 'metadata.json').exists():
        manager.delete(runtime.worker.name)
