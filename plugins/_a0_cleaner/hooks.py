from plugins._a0_cleaner.helpers import runtime


def run_scheduled_task(task, cancel_event):
    return runtime.run_scheduled(cancel_event)


def save_plugin_config(settings, **kwargs):
    cleaner = runtime.service(config=settings)
    cleaner.areas(validate_custom=True)
    return cleaner.config
