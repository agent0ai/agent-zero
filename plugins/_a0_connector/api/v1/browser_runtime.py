"""POST /api/plugins/_a0_connector/v1/browser_runtime."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


_PRIVACY_NOTICE = (
    "For Browser model-use settings, visit Agent Zero WebUI > Browser settings to choose "
    "Local models only, Warn when using cloud, or Allow."
)


def _string(value: object) -> str:
    return str(value or "").strip()


def _normalize_requested_backend(value: object) -> str:
    normalized = _string(value).lower().replace("-", "_").replace(" ", "_")
    if normalized in {"container", "docker", "docker_container"}:
        return "container"
    if normalized in {"host", "host_required", "byob", "bring_your_own_browser"}:
        return "host_required"
    return ""


def _normalize_profile_mode(value: object) -> str:
    normalized = _string(value).lower().replace("-", "_").replace(" ", "_")
    if normalized in {"agent", "clean", "clean_agent", "a0", "dedicated"}:
        return "agent"
    if normalized in {"existing", "user", "personal", "current"}:
        return "existing"
    return ""


def _runtime_label(value: str) -> str:
    if value == "host_required":
        return "Bring Your Own Browser"
    return "Docker browser"


class BrowserRuntime(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = _string(input.get("action")).lower() or "get"
        if action not in {"get", "set"}:
            return Response(
                response='{"error":"Unsupported action"}',
                status=400,
                mimetype="application/json",
            )

        try:
            project_name = self._project_name_for_context(_string(input.get("context_id")))
        except LookupError:
            return Response(
                response='{"error":"Context not found"}',
                status=404,
                mimetype="application/json",
            )

        settings = self._load_browser_config(project_name)
        if action == "set":
            runtime_backend = _normalize_requested_backend(input.get("runtime_backend"))
            if not runtime_backend:
                return Response(
                    response='{"error":"runtime_backend must be host or container"}',
                    status=400,
                    mimetype="application/json",
                )
            settings["runtime_backend"] = runtime_backend
            if "host_browser_profile_mode" in input or "profile_mode" in input:
                profile_mode = _normalize_profile_mode(
                    input.get("host_browser_profile_mode", input.get("profile_mode"))
                )
                if not profile_mode:
                    return Response(
                        response='{"error":"host_browser_profile_mode must be existing or agent"}',
                        status=400,
                        mimetype="application/json",
                    )
                settings["host_browser_profile_mode"] = profile_mode
            settings["host_browser_profile_mode"] = (
                _normalize_profile_mode(settings.get("host_browser_profile_mode")) or "existing"
            )
            self._save_browser_config(project_name, settings)

        runtime_backend = settings.get("runtime_backend") or "container"
        profile_mode = _normalize_profile_mode(settings.get("host_browser_profile_mode")) or "existing"

        return {
            "ok": True,
            "runtime_backend": runtime_backend,
            "host_browser_profile_mode": profile_mode,
            "label": _runtime_label(runtime_backend),
            "project_name": project_name,
            "agent_profile": "",
            "privacy_notice": _PRIVACY_NOTICE,
        }

    def _project_name_for_context(self, context_id: str) -> str:
        if not context_id:
            return ""

        from agent import AgentContext
        from helpers import projects

        context = AgentContext.get(context_id)
        if context is None:
            raise LookupError(context_id)
        return projects.get_context_project_name(context) or ""

    def _load_browser_config(self, project_name: str) -> dict:
        from helpers import plugins
        from plugins._browser.helpers.config import PLUGIN_NAME, normalize_browser_config

        return normalize_browser_config(
            plugins.get_plugin_config(PLUGIN_NAME, project_name=project_name, agent_profile="")
            or {}
        )

    def _save_browser_config(self, project_name: str, settings: dict) -> None:
        from helpers import plugins
        from plugins._browser.helpers.config import PLUGIN_NAME

        plugins.save_plugin_config(PLUGIN_NAME, project_name, "", settings)
