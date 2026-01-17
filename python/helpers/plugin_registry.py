import json
import os
from typing import Any


class PluginRegistry:
    def __init__(self, manifest_dir: str):
        self.manifest_dir = manifest_dir
        self._plugins: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        self._plugins = {}
        if not os.path.isdir(self.manifest_dir):
            return
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

    def list_plugins(self) -> list[dict[str, Any]]:
        return list(self._plugins.values())

    def get_plugin(self, plugin_id: str) -> dict[str, Any] | None:
        return self._plugins.get(plugin_id)
