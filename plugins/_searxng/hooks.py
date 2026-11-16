"""Search dependencies are installed only on the first request."""
def install():
    return {'sandbox': True, 'installed_on_demand': True}


def disable():
    from plugins._searxng.helpers.searxng import worker
    worker.stop()


def uninstall():
    from plugins._searxng.helpers.searxng import worker
    from helpers.sandbox import get_manager
    worker.stop()
    get_manager().delete(worker.name, missing_ok=True)
