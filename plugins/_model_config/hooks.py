from plugins._model_config.helpers import model_config


def get_plugin_config(default=None, **kwargs):
    """Expose the legacy complete config shape to runtime callers."""
    return model_config.resolve_config_settings(default)


def save_plugin_config(result=None, settings=None, **kwargs):
    """Persist only the scoped preset selection."""
    raw = settings if isinstance(settings, dict) else {}
    name = str(
        raw.get(model_config.MODEL_PRESET_CONFIG_KEY)
        or model_config.DEFAULT_PRESET_NAME
    ).strip()
    preset = model_config.resolve_preset(name)
    return {
        model_config.MODEL_PRESET_CONFIG_KEY: (
            str(preset.get("name"))
            if preset
            else model_config.DEFAULT_PRESET_NAME
        )
    }
