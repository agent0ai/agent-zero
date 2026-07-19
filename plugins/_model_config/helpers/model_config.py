import os
from copy import deepcopy

import models
from helpers import plugins, files
from helpers import yaml as yaml_helper
from helpers.providers import get_provider_config, get_providers

PRESETS_FILE = "presets.yaml"
DEFAULT_PRESETS_FILE = "default_presets.yaml"
PROVIDER_METADATA_FILE = "provider_metadata.yaml"
PRESET_SCOPE_GLOBAL = "global"
PRESET_SCOPE_PROJECT = "project"
LOCAL_PROVIDERS = {"ollama", "lm_studio"}
LOCAL_EMBEDDING = {"huggingface"}
_PROVIDER_METADATA_CACHE: dict | None = None


def _get_provider_metadata_path() -> str:
    plugin_dir = plugins.find_plugin_dir("_model_config")
    return files.get_abs_path(plugin_dir, PROVIDER_METADATA_FILE) if plugin_dir else ""


def get_provider_metadata(model_type: str = "chat", provider: str = "") -> dict:
    """Get plugin-owned provider metadata that does not belong in conf/model_providers.yaml."""
    global _PROVIDER_METADATA_CACHE
    if _PROVIDER_METADATA_CACHE is None:
        path = _get_provider_metadata_path()
        if path and files.exists(path):
            data = yaml_helper.loads(files.read_file(path))
            _PROVIDER_METADATA_CACHE = data if isinstance(data, dict) else {}
        else:
            _PROVIDER_METADATA_CACHE = {}

    section = _PROVIDER_METADATA_CACHE.get(model_type, {})
    if not isinstance(section, dict):
        return {}
    meta = section.get(str(provider or "").strip().lower(), {})
    return meta if isinstance(meta, dict) else {}


def _model_type_for_label(label: str) -> str:
    return "embedding" if label == "Embedding Model" else "chat"


def provider_requires_api_key(provider: str, model_type: str = "chat") -> bool:
    provider_id = str(provider or "").strip().lower()
    if not provider_id:
        return False
    cfg = get_provider_config(model_type, provider_id) or get_provider_config("chat", provider_id) or {}
    meta = get_provider_metadata(model_type, provider_id) or get_provider_metadata("chat", provider_id)
    mode = str(meta.get("api_key_mode") or cfg.get("api_key_mode") or "required").strip().lower()
    return mode not in {"none", "optional", "oauth"}


def _get_presets_path(project_name: str | None = None) -> str:
    """Return the user-editable presets path for the requested scope."""
    if project_name:
        return plugins.determine_plugin_asset_path(
            "_model_config", project_name, "", PRESETS_FILE
        )
    return files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR, "_model_config", PRESETS_FILE)


def _get_default_presets_path() -> str:
    """Return the path to the default presets file shipped with the plugin."""
    plugin_dir = plugins.find_plugin_dir("_model_config")
    return files.get_abs_path(plugin_dir, DEFAULT_PRESETS_FILE) if plugin_dir else ""


def get_config(agent=None, project_name=None, agent_profile=None):
    """Get the full model config dict for the given agent/scope."""
    return plugins.get_plugin_config(
        "_model_config",
        agent=agent,
        project_name=project_name,
        agent_profile=agent_profile,
    ) or {}


def _load_presets_from_path(path: str) -> list | None:
    if files.exists(path):
        data = yaml_helper.loads(files.read_file(path))
        if isinstance(data, list):
            return data
    return None


def _strip_ui_fields(value: dict, *, strip_api_key: bool) -> dict:
    cleaned = deepcopy(value)
    for key in list(cleaned.keys()):
        if key.startswith("_"):
            cleaned.pop(key, None)
    if strip_api_key:
        cleaned.pop("api_key", None)
    return cleaned


def _clean_preset_for_file(preset: dict) -> dict:
    cleaned = {
        "name": str(preset.get("name", "") or ""),
    }
    for slot in ("chat", "utility"):
        slot_config = preset.get(slot)
        if isinstance(slot_config, dict):
            cleaned[slot] = _strip_ui_fields(slot_config, strip_api_key=False)
    return cleaned


def clean_presets_for_file(presets: list) -> list:
    """Return presets without API/UI metadata, preserving the plain YAML schema."""
    cleaned = []
    for preset in presets:
        if isinstance(preset, dict):
            cleaned.append(_clean_preset_for_file(preset))
    return cleaned


def normalize_config_for_save(config: dict) -> dict:
    """Remove UI-only fields and inline API keys before storing scoped config."""
    cleaned = deepcopy(config or {})
    for section_name in ("chat_model", "utility_model", "embedding_model"):
        section = cleaned.get(section_name)
        if isinstance(section, dict):
            cleaned[section_name] = _strip_ui_fields(section, strip_api_key=True)
    return cleaned


def get_presets(project_name: str | None = None) -> list:
    """Get global model presets list (not scoped to project/agent)."""
    if project_name:
        return get_project_presets(project_name)

    path = _get_presets_path()
    presets = _load_presets_from_path(path)
    if presets is not None:
        return presets

    # Fall back to defaults bundled with the plugin
    default_path = _get_default_presets_path()
    default_presets = _load_presets_from_path(default_path) if default_path else None
    return default_presets or []


def get_project_presets(project_name: str) -> list:
    """Get presets stored beside the project-scoped _model_config config."""
    return _load_presets_from_path(_get_presets_path(project_name)) or []


def _with_preset_metadata(preset: dict, scope: str, project_name: str = "") -> dict:
    item = deepcopy(preset)
    item["scope"] = scope
    item["project_name"] = project_name if scope == PRESET_SCOPE_PROJECT else ""
    item["name"] = str(item.get("name", "") or "")
    return item


def get_combined_presets(project_name: str | None = None) -> list:
    """Get presets with explicit API metadata for unambiguous UI/API selection."""
    presets = [
        _with_preset_metadata(preset, PRESET_SCOPE_GLOBAL)
        for preset in get_presets()
        if isinstance(preset, dict)
    ]
    if project_name:
        presets.extend(
            _with_preset_metadata(preset, PRESET_SCOPE_PROJECT, project_name)
            for preset in get_project_presets(project_name)
            if isinstance(preset, dict)
        )
    return presets


def save_presets(presets: list, project_name: str | None = None) -> None:
    """Save the presets list for the requested scope."""
    path = _get_presets_path(project_name)
    files.write_file(path, yaml_helper.dumps(clean_presets_for_file(presets)))


def reset_presets(project_name: str | None = None) -> list:
    """Delete user presets for the scope. Global reset falls back to bundled defaults."""
    path = _get_presets_path(project_name)
    if os.path.exists(path):
        os.remove(path)
    return get_project_presets(project_name) if project_name else get_presets()


def resolve_preset(
    name: str,
    *,
    scope: str = PRESET_SCOPE_GLOBAL,
    project_name: str | None = None,
) -> dict | None:
    """Resolve a preset by explicit scope so same-name presets are unambiguous."""
    if scope == PRESET_SCOPE_PROJECT:
        if not project_name:
            return None
        presets = get_project_presets(project_name)
    else:
        presets = get_presets()

    for p in presets:
        if p.get("name") == name:
            return p
    return None


def resolve_preset_selection(selection: dict | str, project_name: str | None = None) -> dict | None:
    """Resolve a UI/API preset selection payload to a preset dict."""
    if isinstance(selection, str):
        return resolve_preset(selection)
    if not isinstance(selection, dict):
        return None

    scope = str(selection.get("scope") or PRESET_SCOPE_GLOBAL)
    if scope == "current":
        return None
    name = str(selection.get("name") or "")
    selected_project = str(selection.get("project_name") or project_name or "")
    return resolve_preset(name, scope=scope, project_name=selected_project or None)


def get_preset_by_name(
    name: str,
    *,
    scope: str = PRESET_SCOPE_GLOBAL,
    project_name: str | None = None,
) -> dict | None:
    """Find a preset by name. Defaults to global presets for legacy callers."""
    return resolve_preset(name, scope=scope, project_name=project_name)


def build_config_from_preset(preset: dict, base_config: dict) -> dict:
    """Copy chat/utility settings from a preset into a standalone model config."""
    config = normalize_config_for_save(base_config)

    chat = preset.get("chat") if isinstance(preset, dict) else None
    if isinstance(chat, dict):
        config["chat_model"] = _strip_ui_fields(chat, strip_api_key=True)

    utility = preset.get("utility") if isinstance(preset, dict) else None
    if isinstance(utility, dict) and (utility.get("provider") or utility.get("name")):
        config["utility_model"] = _strip_ui_fields(utility, strip_api_key=True)

    return config


def _resolve_override(agent) -> dict | None:
    """Resolve the active per-chat override config dict.
    Supports both raw override dicts and preset-based overrides.
    Returns None if no override is active or if override is not allowed."""
    if not agent:
        return None
    if not is_chat_override_allowed(agent):
        return None
    override = agent.context.get_data("chat_model_override")
    if not override:
        return None

    # If this is a preset reference, resolve it
    if "preset_name" in override:
        preset = get_preset_by_name(override["preset_name"])
        if not preset:
            return None
        return preset

    return override


def get_chat_model_config(agent=None) -> dict:
    """Get chat model config, with per-chat override if active."""
    override = _resolve_override(agent)
    if override:
        # Preset has a nested 'chat' key; raw override is flat
        chat_cfg = override.get("chat", override)
        if chat_cfg.get("provider") or chat_cfg.get("name"):
            return chat_cfg
    cfg = get_config(agent)
    return cfg.get("chat_model", {})


def get_utility_model_config(agent=None) -> dict:
    """Get utility model config, with per-chat override if active."""
    override = _resolve_override(agent)
    if override:
        util_cfg = override.get("utility", {})
        if util_cfg.get("provider") or util_cfg.get("name"):
            return util_cfg
    cfg = get_config(agent)
    return cfg.get("utility_model", {})


def get_embedding_model_config(agent=None) -> dict:
    """Get embedding model config."""
    cfg = get_config(agent)
    return cfg.get("embedding_model", {})

def is_chat_override_allowed(agent=None) -> bool:
    """Check if per-chat model override is enabled."""
    cfg = get_config(agent)
    return bool(cfg.get("allow_chat_override", False))


def get_ctx_history(agent=None) -> float:
    """Get the chat model context history ratio."""
    cfg = get_chat_model_config(agent)
    return float(cfg.get("ctx_history", 0.7))


def get_ctx_input(agent=None) -> float:
    """Get the utility model context input ratio."""
    cfg = get_utility_model_config(agent)
    return float(cfg.get("ctx_input", 0.7))


def _normalize_kwargs(kwargs: dict) -> dict:
    """Convert string values that are valid numbers to numeric types."""
    result = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            try:
                result[key] = int(value)
            except ValueError:
                try:
                    result[key] = float(value)
                except ValueError:
                    result[key] = value
        else:
            result[key] = value
    return result


def build_model_config(cfg: dict, model_type: models.ModelType) -> models.ModelConfig:
    """Build a ModelConfig from a config dict section."""
    return models.ModelConfig(
        type=model_type,
        provider=cfg.get("provider", ""),
        name=cfg.get("name", ""),
        api_key=cfg.get("api_key", ""),
        api_base=cfg.get("api_base", ""),
        ctx_length=int(cfg.get("ctx_length", 0)),
        vision=bool(cfg.get("vision", False)),
        limit_requests=int(cfg.get("rl_requests", 0)),
        limit_input=int(cfg.get("rl_input", 0)),
        limit_output=int(cfg.get("rl_output", 0)),
        kwargs=_normalize_kwargs(cfg.get("kwargs", {})),
    )


def build_chat_model(agent=None):
    """Build and return a LiteLLMChatWrapper from config."""
    cfg = get_chat_model_config(agent)
    mc = build_model_config(cfg, models.ModelType.CHAT)
    return models.get_chat_model(
        mc.provider, mc.name, model_config=mc, **mc.build_kwargs()
    )


def build_utility_model(agent=None):
    """Build and return a LiteLLMChatWrapper for utility tasks."""
    cfg = get_utility_model_config(agent)
    mc = build_model_config(cfg, models.ModelType.CHAT)
    return models.get_chat_model(
        mc.provider, mc.name, model_config=mc, **mc.build_kwargs()
    )


def build_embedding_model(agent=None):
    """Build and return an embedding model wrapper."""
    cfg = get_embedding_model_config(agent)
    mc = build_model_config(cfg, models.ModelType.EMBEDDING)
    return models.get_embedding_model(
        mc.provider, mc.name, model_config=mc, **mc.build_kwargs()
    )


def get_embedding_model_config_object(agent=None) -> models.ModelConfig:
    """Get a ModelConfig object for embeddings (needed by memory plugin)."""
    cfg = get_embedding_model_config(agent)
    return build_model_config(cfg, models.ModelType.EMBEDDING)


def get_chat_providers():
    """Get list of chat providers for UI dropdowns."""
    return get_providers("chat")


def get_embedding_providers():
    """Get list of embedding providers for UI dropdowns."""
    return get_providers("embedding")


def has_provider_api_key(provider: str, configured_api_key: str = "", model_type: str = "chat") -> bool:
    if not provider_requires_api_key(provider, model_type):
        return True
    configured_value = (configured_api_key or "").strip()
    if configured_value and configured_value != "None":
        return True

    api_key = models.get_api_key(provider.lower())
    return bool(api_key and api_key.strip() and api_key != "None")


def get_missing_api_key_providers(agent=None) -> list[dict]:
    """Check which configured providers are missing API keys."""
    cfg = get_config(agent)
    missing = []

    checks = [
        ("Chat Model", cfg.get("chat_model", {})),
        ("Utility Model", cfg.get("utility_model", {})),
        ("Embedding Model", cfg.get("embedding_model", {})),
    ]

    for label, model_cfg in checks:
        provider = model_cfg.get("provider", "")
        if not provider:
            continue
        provider_lower = provider.lower()
        if provider_lower in LOCAL_PROVIDERS:
            continue
        if label == "Embedding Model" and provider_lower in LOCAL_EMBEDDING:
            continue

        if not has_provider_api_key(provider_lower, model_cfg.get("api_key", ""), _model_type_for_label(label)):
            missing.append({"model_type": label, "provider": provider})

    return missing
