"""Stop the child worker on plugin disable without deleting login state."""
def disable():
    from plugins._whatsapp_integration.helpers.bridge_manager import worker, _bridge_config
    worker.stop()
    _bridge_config.clear()


def uninstall():
    disable()
