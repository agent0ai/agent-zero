import json
import os
from pathlib import Path
from typing import Any

from python.helpers.skill_registry import get_registry


class PluginRegistry:
    def __init__(self, manifest_dir: str):
        self.manifest_dir = manifest_dir
        self._plugins: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        self._plugins = {}
        if not os.path.isdir(self.manifest_dir):
            return

        # --- JSON manifests (original behaviour) ---
        for entry in os.listdir(self.manifest_dir):
            if not entry.endswith(".json"):
                continue
            path = os.path.join(self.manifest_dir, entry)
            try:
                with open(path, encoding="utf-8") as handle:
                    manifest = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if not manifest.get("id") or not manifest.get("version"):
                continue
            manifest["__path__"] = path
            self._plugins[manifest["id"]] = manifest

        # --- SKILL.md manifests (delegate to SkillRegistry) ---
        registry = get_registry()
        registry.scan_directory(Path(self.manifest_dir))

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return all plugins, including SKILL.md-based skills."""
        combined: list[dict[str, Any]] = list(self._plugins.values())
        registry = get_registry()
        for skill in registry.list():
            # Avoid duplicates: use skill name as the key
            if skill.name not in self._plugins:
                combined.append(skill.to_dict())
        return combined

    def get_plugin(self, plugin_id: str) -> dict[str, Any] | None:
        # Check JSON plugins first, then fall back to skill registry
        result = self._plugins.get(plugin_id)
        if result is not None:
            return result
        registry = get_registry()
        skill = registry.get(plugin_id)
        if skill is not None:
            return skill.to_dict()
        return None
