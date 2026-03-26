def save_plugin_config(result=None, settings=None, **kwargs):
    if settings and isinstance(settings, dict):
        # Remove transient UI-only fields before persisting
        for section in ("chat_model", "utility_model", "embedding_model"):
            if section in settings and isinstance(settings[section], dict):
                settings[section].pop("_kwargs_text", None)
                settings[section].pop("api_key", None)
    return settings
