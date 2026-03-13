import yaml
from helpers import files, cache
from typing import List, Dict, Optional, TypedDict, Literal

ModelType = Literal["chat", "embedding"]

PROVIDER_MANAGER_CACHE_AREA = "model_providers(plugins)"
PROVIDER_MANAGER_CACHE_KEY = "manager"

# Type alias for UI option items
class FieldOption(TypedDict):
    value: str
    label: str

class ProviderManager:
    _raw: Optional[Dict[str, List[Dict[str, str]]]] = None  # full provider data
    _options: Optional[Dict[str, List[FieldOption]]] = None  # UI-friendly list

    @classmethod
    def get_instance(cls):
        instance = cache.get(PROVIDER_MANAGER_CACHE_AREA, PROVIDER_MANAGER_CACHE_KEY)
        if instance is None:
            instance = cls()
            cache.add(PROVIDER_MANAGER_CACHE_AREA, PROVIDER_MANAGER_CACHE_KEY, instance)
        return instance

    @classmethod
    def reload(cls):
        """Force reload of all provider configs (call after plugin changes)."""
        cache.remove(PROVIDER_MANAGER_CACHE_AREA, PROVIDER_MANAGER_CACHE_KEY)
        inst = cls.get_instance()
        inst._load_providers()

    def __init__(self):
        if self._raw is None or self._options is None:
            self._load_providers()

    @staticmethod
    def _load_yaml(path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    @staticmethod
    def _normalise_yaml(raw_yaml: dict) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Normalise YAML into {type: {id: config}} mapping format."""
        result: Dict[str, Dict[str, Dict[str, str]]] = {}
        for p_type, providers in (raw_yaml or {}).items():
            entries: Dict[str, Dict[str, str]] = {}
            if isinstance(providers, dict):
                for pid, cfg in providers.items():
                    entries[pid] = cfg or {}
            elif isinstance(providers, list):
                for p in (providers or []):
                    pid = (p.get("id") or p.get("value") or "").lower()
                    if pid:
                        entries[pid] = {k: v for k, v in p.items() if k not in ("id", "value")}
            result[p_type] = entries
        return result

    def _load_providers(self):
        """Loads provider configs from main YAML and enabled plugins, then merges."""
        # Load base config
        base_path = files.get_abs_path("conf/model_providers.yaml")
        merged = self._normalise_yaml(self._load_yaml(base_path))

        # Merge plugin provider configs (enabled plugins only)
        from helpers.plugins import get_enabled_plugin_paths
        plugin_yamls = get_enabled_plugin_paths(None, "conf", "model_providers.yaml")
        for plugin_yaml_path in plugin_yamls:
            plugin_data = self._normalise_yaml(self._load_yaml(plugin_yaml_path))
            for p_type, providers in plugin_data.items():
                if p_type not in merged:
                    merged[p_type] = {}
                # Overwrite matching keys, append new ones
                merged[p_type].update(providers)

        # Convert merged {type: {id: config}} to normalised list format,
        # sorted by name with "other" always last.
        normalised: Dict[str, List[Dict[str, str]]] = {}
        for p_type, providers in merged.items():
            items: List[Dict[str, str]] = []
            for pid, cfg in providers.items():
                entry = {"id": pid, **cfg}
                items.append(entry)
            items.sort(key=lambda p: (
                p.get("id") == "other",  # False (0) first, True (1) last
                (p.get("name") or p.get("id") or "").lower(),
            ))
            normalised[p_type] = items

        # Save raw
        self._raw = normalised

        # Build UI-friendly option list (value / label)
        self._options = {}
        for p_type, providers in normalised.items():
            opts: List[FieldOption] = []
            for p in providers:
                pid = (p.get("id") or p.get("value") or "").lower()
                name = p.get("name") or p.get("label") or pid
                if pid:
                    opts.append({"value": pid, "label": name})
            self._options[p_type] = opts

    def get_providers(self, provider_type: ModelType) -> List[FieldOption]:
        """Returns a list of providers for a given type (e.g., 'chat', 'embedding')."""
        return self._options.get(provider_type, []) if self._options else []

    def get_raw_providers(self, provider_type: ModelType) -> List[Dict[str, str]]:
        """Return raw provider dictionaries for advanced use-cases."""
        return self._raw.get(provider_type, []) if self._raw else []

    def get_provider_config(self, provider_type: ModelType, provider_id: str) -> Optional[Dict[str, str]]:
        """Return the metadata dict for a single provider id (case-insensitive)."""
        provider_id_low = provider_id.lower()
        for p in self.get_raw_providers(provider_type):
            if (p.get("id") or p.get("value", "")).lower() == provider_id_low:
                return p
        return None


def get_providers(provider_type: ModelType) -> List[FieldOption]:
    """Convenience function to get providers of a specific type."""
    return ProviderManager.get_instance().get_providers(provider_type)


def get_raw_providers(provider_type: ModelType) -> List[Dict[str, str]]:
    """Return full metadata for providers of a given type."""
    return ProviderManager.get_instance().get_raw_providers(provider_type)


def get_provider_config(provider_type: ModelType, provider_id: str) -> Optional[Dict[str, str]]:
    """Return metadata for a single provider (None if not found)."""
    return ProviderManager.get_instance().get_provider_config(provider_type, provider_id)


def reload_providers():
    """Re-merge base + plugin provider configs. Call after plugin changes."""
    ProviderManager.reload()