"""POST /api/plugins/_a0_connector/v1/model_presets."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class ModelPresets(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from plugins._model_config.helpers import model_config

        action = str(input.get("action", "get")).strip() or "get"
        project_name = str(input.get("project_name") or "").strip()
        scope = str(input.get("scope") or "").strip()

        if action == "get":
            if scope == "project":
                presets = model_config.get_project_presets(project_name) if project_name else []
                return {"ok": True, "presets": presets}
            if scope == "combined" or project_name:
                return {
                    "ok": True,
                    "presets": model_config.get_combined_presets(project_name or None),
                    "global_presets": model_config.get_presets(),
                    "project_presets": (
                        model_config.get_project_presets(project_name)
                        if project_name
                        else []
                    ),
                }
            return {"ok": True, "presets": model_config.get_presets()}

        if action == "save":
            presets = input.get("presets")
            if not isinstance(presets, list):
                return Response(status=400, response="presets must be an array")
            model_config.save_presets(
                presets,
                project_name=project_name if scope == "project" or project_name else None,
            )
            return {"ok": True, "presets": model_config.clean_presets_for_file(presets)}

        if action == "reset":
            presets = model_config.reset_presets(
                project_name=project_name if scope == "project" or project_name else None
            )
            return {"ok": True, "presets": presets}

        if action == "resolve":
            name = str(input.get("name") or "").strip()
            if not name:
                return Response(status=400, response="Missing preset name")
            resolved = model_config.resolve_preset(
                name,
                scope=scope or "global",
                project_name=project_name or None,
            )
            if not resolved:
                return Response(status=404, response=f"Preset '{name}' not found")
            return {
                "ok": True,
                "preset": {
                    **resolved,
                    "scope": scope or "global",
                    "project_name": project_name if scope == "project" else "",
                },
            }

        return Response(status=400, response=f"Unknown action: {action}")
