import json
import os

from python.helpers.plugin_registry import PluginRegistry


def test_plugin_registry_loads_valid_manifests(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    manifest_path = plugin_dir / "calendar_hub.json"
    manifest_path.write_text(
        json.dumps(
            {
                "id": "calendar_hub",
                "version": "0.1.0",
                "ui": {"dashboard_card": "dashboards/calendar/calendar-dashboard.html"},
                "tools": ["calendar_hub"],
                "events": ["calendar.event_created"],
            }
        ),
        encoding="utf-8",
    )

    registry = PluginRegistry(str(plugin_dir))
    registry.load()

    plugin = registry.get_plugin("calendar_hub")
    assert plugin["id"] == "calendar_hub"
    assert plugin["version"] == "0.1.0"


def test_plugin_registry_skips_invalid_manifest(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    invalid_path = plugin_dir / "invalid.json"
    invalid_path.write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    registry = PluginRegistry(str(plugin_dir))
    registry.load()

    assert registry.list_plugins() == []
