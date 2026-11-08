"""Retain mailbox UID state and attachments when stopping the guest."""
def disable():
    from plugins._email_integration.helpers.sandbox import worker
    from plugins._email_integration.helpers.handler import _poll_tasks
    for task in list(_poll_tasks.values()):
        if not task.done():
            task.get_loop().call_soon_threadsafe(task.cancel)
    _poll_tasks.clear()
    worker.stop()


def uninstall():
    disable()
