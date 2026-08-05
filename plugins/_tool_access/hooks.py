from helpers.tool_policy import normalize_policy


def get_plugin_config(default=None, **kwargs):
    return normalize_policy(default)


def save_plugin_config(settings=None, **kwargs):
    return normalize_policy(settings)
