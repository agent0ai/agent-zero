import asyncio
from types import SimpleNamespace

from helpers import plugins, projects
from helpers.api import ApiHandler, Request
from plugins._browser.helpers.config import (
    AUTOFOCUS_ACTIVE_PAGE_KEY,
    ANNOTATION_SCREENSHOTS_KEY,
    DEFAULT_HOMEPAGE_KEY,
    MODEL_PRESET_KEY,
    PLUGIN_NAME,
    RUNTIME_BACKEND_KEY,
    RUNTIME_BACKENDS,
    get_browser_config,
    get_browser_main_model_summary,
    get_browser_model_preset_options,
)
from plugins._browser.helpers.extension_manager import (
    get_extensions_root,
    install_chrome_web_store_extension,
    list_browser_extensions,
    set_browser_extension_enabled,
    uninstall_browser_extension,
)


class Extensions(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "list")
        agent = self._agent_from_input(input)

        if action == "list":
            return self._browser_extension_payload(agent=agent)

        if action == "set_runtime_backend":
            backend = input.get(RUNTIME_BACKEND_KEY)
            if not isinstance(backend, str) or backend not in RUNTIME_BACKENDS:
                return {"ok": False, "error": "Choose Host or Container browser."}
            if input.get("context_id") and agent is None:
                return {"ok": False, "error": "The selected chat is no longer available."}
            config = get_browser_config(agent=agent)
            config[RUNTIME_BACKEND_KEY] = backend
            project_name = projects.get_context_project_name(agent.context) if agent else ""
            plugins.save_plugin_config(PLUGIN_NAME, project_name or "", "", config)
            return self._browser_extension_payload(agent=agent)

        if action == "install_web_store":
            try:
                result = await asyncio.to_thread(
                    install_chrome_web_store_extension,
                    str(input.get("url", "")),
                )
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            return {
                **self._browser_extension_payload(agent=agent),
                **result,
            }

        if action == "set_extension_enabled":
            try:
                set_browser_extension_enabled(
                    str(input.get("path", "")),
                    bool(input.get("enabled", False)),
                )
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            return self._browser_extension_payload(agent=agent)

        if action == "uninstall_extension":
            try:
                result = uninstall_browser_extension(str(input.get("path", "")))
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            return {
                **self._browser_extension_payload(agent=agent),
                **result,
            }

        if action == "set_model_preset":
            preset_name = str(input.get(MODEL_PRESET_KEY, "") or "").strip()
            available_presets = {
                option["name"]
                for option in get_browser_model_preset_options(agent=agent)
                if option.get("name") and not option.get("missing")
            }
            if preset_name and preset_name not in available_presets:
                return {"ok": False, "error": "Choose an available browser model preset."}

            config = get_browser_config()
            config[MODEL_PRESET_KEY] = preset_name
            plugins.save_plugin_config(PLUGIN_NAME, "", "", config)
            return self._browser_extension_payload(agent=agent)

        return {"ok": False, "error": f"Unknown action: {action}"}

    def _agent_from_input(self, input: dict):
        context_id = str(input.get("context_id", "") or "").strip()
        if not context_id:
            return None
        try:
            context = self.use_context(context_id, create_if_not_exists=False)
        except Exception:
            return None
        config = getattr(context, "config", None)
        if config is None:
            return None
        return SimpleNamespace(context=context, config=config)

    def _browser_extension_payload(self, agent=None) -> dict:
        config = get_browser_config()
        scoped_config = get_browser_config(agent=agent)
        return {
            "ok": True,
            "root": str(get_extensions_root()),
            "extensions": list_browser_extensions(),
            "extension_paths": config["extension_paths"],
            DEFAULT_HOMEPAGE_KEY: config[DEFAULT_HOMEPAGE_KEY],
            AUTOFOCUS_ACTIVE_PAGE_KEY: config[AUTOFOCUS_ACTIVE_PAGE_KEY],
            ANNOTATION_SCREENSHOTS_KEY: scoped_config[ANNOTATION_SCREENSHOTS_KEY],
            RUNTIME_BACKEND_KEY: scoped_config[RUNTIME_BACKEND_KEY],
            "settings_project_name": projects.get_context_project_name(agent.context) if agent else "",
            MODEL_PRESET_KEY: config[MODEL_PRESET_KEY],
            "main_model_summary": get_browser_main_model_summary(agent=agent),
            "model_preset_options": get_browser_model_preset_options(agent=agent, settings=config),
        }
