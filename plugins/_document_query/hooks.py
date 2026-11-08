"""Dependencies are installed only when the sandbox is first used."""
def install():
    return True


def ensure_dependencies(raise_on_error=True):
    return True


def disable():
    from plugins._document_query.helpers.sandbox import worker
    worker.stop()


def uninstall():
    from plugins._document_query.helpers.sandbox import worker
    worker.stop()
    from helpers.sandbox import get_manager
    manager = get_manager()
    if (manager.config.instances_dir / worker.name / 'metadata.json').exists():
        manager.delete(worker.name)
