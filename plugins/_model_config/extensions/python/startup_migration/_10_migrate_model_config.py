import json
import os
from helpers.extension import Extension
from helpers import settings as settings_helper, files, plugins
from helpers.print_style import PrintStyle


class MigrateModelConfig(Extension):
    """
    One-time migration: copy legacy model settings into _model_config plugin config.
    Runs during initialize_migration. Only migrates if no global plugin config exists yet
    and the settings file contains legacy model fields.
    """

    LEGACY_FIELDS = [
        "chat_model_provider", "chat_model_name", "chat_model_api_base",
        "chat_model_kwargs", "chat_model_ctx_length", "chat_model_vision",
        "chat_model_rl_requests", "chat_model_rl_input", "chat_model_rl_output",
        "chat_model_ctx_history",
        "util_model_provider", "util_model_name", "util_model_api_base",
        "util_model_kwargs", "util_model_ctx_length",
        "util_model_rl_requests", "util_model_rl_input", "util_model_rl_output",
        "util_model_ctx_input",
        "embed_model_provider", "embed_model_name", "embed_model_api_base",
        "embed_model_kwargs", "embed_model_rl_requests", "embed_model_rl_input",
        "browser_model_provider", "browser_model_name", "browser_model_api_base",
        "browser_model_vision", "browser_model_rl_requests", "browser_model_rl_input",
        "browser_model_rl_output", "browser_model_kwargs", "browser_http_headers",
    ]

    def execute(self, **kwargs):
        # Check if global plugin config already exists
        global_config_path = files.get_abs_path("plugins/_model_config/config.json")
        if os.path.exists(global_config_path):
            return  # already migrated or manually configured

        # Read raw settings file to check for legacy model fields
        settings_file = files.get_abs_path("usr/settings.json")
        if not os.path.exists(settings_file):
            return

        try:
            raw = json.loads(files.read_file(settings_file))
        except Exception:
            return

        # Check if any legacy model field exists in the raw settings
        has_legacy = any(field in raw for field in self.LEGACY_FIELDS)
        if not has_legacy:
            return

        # Build plugin config from legacy settings
        plugin_config = {
            "allow_chat_override": False,
            "chat_model": {
                "provider": raw.get("chat_model_provider", "openrouter"),
                "name": raw.get("chat_model_name", ""),
                "api_base": raw.get("chat_model_api_base", ""),
                "ctx_length": raw.get("chat_model_ctx_length", 128000),
                "ctx_history": raw.get("chat_model_ctx_history", 0.7),
                "vision": raw.get("chat_model_vision", True),
                "rl_requests": raw.get("chat_model_rl_requests", 0),
                "rl_input": raw.get("chat_model_rl_input", 0),
                "rl_output": raw.get("chat_model_rl_output", 0),
                "kwargs": raw.get("chat_model_kwargs", {}),
            },
            "utility_model": {
                "provider": raw.get("util_model_provider", "openrouter"),
                "name": raw.get("util_model_name", ""),
                "api_base": raw.get("util_model_api_base", ""),
                "ctx_length": raw.get("util_model_ctx_length", 128000),
                "ctx_input": raw.get("util_model_ctx_input", 0.7),
                "rl_requests": raw.get("util_model_rl_requests", 0),
                "rl_input": raw.get("util_model_rl_input", 0),
                "rl_output": raw.get("util_model_rl_output", 0),
                "kwargs": raw.get("util_model_kwargs", {}),
            },
            "embedding_model": {
                "provider": raw.get("embed_model_provider", "huggingface"),
                "name": raw.get("embed_model_name", "sentence-transformers/all-MiniLM-L6-v2"),
                "api_base": raw.get("embed_model_api_base", ""),
                "rl_requests": raw.get("embed_model_rl_requests", 0),
                "rl_input": raw.get("embed_model_rl_input", 0),
                "kwargs": raw.get("embed_model_kwargs", {}),
            },
        }

        # Ensure kwargs are dicts (might be strings from .env format)
        for section in ["chat_model", "utility_model", "embedding_model"]:
            kw = plugin_config[section].get("kwargs")
            if isinstance(kw, str):
                plugin_config[section]["kwargs"] = {}

        # Save as global plugin config
        plugins.save_plugin_config("_model_config", "", "", plugin_config)
        PrintStyle(background_color="#6734C3", font_color="white", padding=True).print(
            "Migrated legacy model settings to _model_config plugin config."
        )
