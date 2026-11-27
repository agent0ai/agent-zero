"""Search dependencies are installed only on the first CLI request."""
def install():
    return {'sandbox': True, 'installed_on_demand': True}


def disable():
    from plugins._searxng.search import NAME, get_manager, locked
    manager = get_manager()
    with locked(manager):
        if (manager.config.instances_dir / NAME / 'metadata.json').is_file():
            manager.stop(NAME)


def uninstall():
    from plugins._searxng.search import NAME, get_manager, locked
    manager = get_manager()
    with locked(manager):
        manager.delete(NAME, missing_ok=True)
