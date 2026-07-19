"""POST /api/plugins/_a0_connector/v1/installed_plugins."""
from __future__ import annotations

from typing import Any, Mapping

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


_PROTECTED_PLUGIN_REASONS = {
    "_a0_connector": "The A0 Connector plugin keeps this CLI session connected.",
}


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _plugin_mapping(plugin: object) -> dict[str, Any]:
    if isinstance(plugin, Mapping):
        return dict(plugin)

    model_dump = getattr(plugin, "model_dump", None)
    if callable(model_dump):
        data = model_dump(mode="json")
        return data if isinstance(data, dict) else {}

    result: dict[str, Any] = {}
    for key in (
        "name",
        "display_name",
        "description",
        "version",
        "author",
        "repo",
        "always_enabled",
        "is_custom",
        "has_main_screen",
        "has_config_screen",
        "toggle_state",
    ):
        if hasattr(plugin, key):
            result[key] = getattr(plugin, key)
    return result


def _plugin_payload(plugin: object) -> dict[str, Any]:
    data = _plugin_mapping(plugin)
    name = _clean_text(data.get("name"))
    display_name = _clean_text(data.get("display_name")) or name
    toggle_state = _clean_text(data.get("toggle_state")).lower()
    always_enabled = bool(data.get("always_enabled"))
    enabled = always_enabled or toggle_state == "enabled"
    protected_reason = _PROTECTED_PLUGIN_REASONS.get(name, "")
    if always_enabled and not protected_reason:
        protected_reason = "Agent Zero marks this plugin as always enabled."

    return {
        "name": name,
        "display_name": display_name,
        "description": _clean_text(data.get("description")),
        "version": _clean_text(data.get("version")),
        "author": _clean_text(data.get("author")),
        "repo": _clean_text(data.get("repo")),
        "source": "custom" if bool(data.get("is_custom")) else "builtin",
        "is_custom": bool(data.get("is_custom")),
        "always_enabled": always_enabled,
        "enabled": enabled,
        "toggle_state": "enabled" if enabled else "disabled",
        "toggleable": not bool(protected_reason),
        "protected_reason": protected_reason,
        "has_main_screen": bool(data.get("has_main_screen")),
        "has_config_screen": bool(data.get("has_config_screen")),
    }


def _installed_plugin_payloads() -> list[dict[str, Any]]:
    from helpers import plugins

    items = plugins.get_enhanced_plugins_list(custom=True, builtin=True)
    payloads = [_plugin_payload(item) for item in items]
    return [payload for payload in payloads if payload["name"]]


def _find_installed_plugin(plugin_name: str) -> dict[str, Any] | None:
    normalized = plugin_name.strip()
    if not normalized:
        return None
    for payload in _installed_plugin_payloads():
        if payload["name"] == normalized:
            return payload
    return None


def _parse_enabled(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "enable", "enabled"}:
            return True
        if normalized in {"0", "false", "no", "off", "disable", "disabled"}:
            return False
    return None


class InstalledPlugins(connector_base.ProtectedConnectorApiHandler):
    """List and toggle already-installed Agent Zero Core plugins only."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        del request

        action = _clean_text(input.get("action") or "list").lower()
        if action == "list":
            plugins = _installed_plugin_payloads()
            enabled_count = sum(1 for plugin in plugins if plugin["enabled"])
            return {
                "ok": True,
                "plugins": plugins,
                "installed_count": len(plugins),
                "enabled_count": enabled_count,
            }

        if action != "set_enabled":
            return Response(status=400, response=f"Unknown action: {action}")

        plugin_name = _clean_text(input.get("plugin_name"))
        if not plugin_name:
            return Response(status=400, response="Missing plugin_name")

        enabled = _parse_enabled(input.get("enabled"))
        if enabled is None:
            return Response(status=400, response="Missing or invalid enabled state")

        plugin = _find_installed_plugin(plugin_name)
        if plugin is None:
            return Response(status=404, response="Plugin not found")

        if not plugin["toggleable"]:
            return Response(
                status=400,
                response=plugin["protected_reason"] or "Plugin cannot be toggled.",
            )

        from helpers import plugins as plugin_helpers

        plugin_helpers.toggle_plugin(
            plugin_name,
            enabled,
            project_name="",
            agent_profile="",
            clear_overrides=False,
        )
        updated = _find_installed_plugin(plugin_name) or plugin
        return {
            "ok": True,
            "plugin": updated,
            "plugins": _installed_plugin_payloads(),
        }
