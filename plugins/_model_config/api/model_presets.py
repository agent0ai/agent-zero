from helpers.api import ApiHandler, Request, Response
from plugins._model_config.helpers import model_config


class ModelPresets(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
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

            presets = model_config.get_presets()
            return {"ok": True, "presets": presets}

        elif action == "save":
            presets = input.get("presets")
            if not isinstance(presets, list):
                return Response(status=400, response="presets must be an array")
            model_config.save_presets(
                presets,
                project_name=project_name if scope == "project" or project_name else None,
            )
            return {"ok": True, "presets": model_config.clean_presets_for_file(presets)}

        elif action == "reset":
            presets = model_config.reset_presets(
                project_name=project_name if scope == "project" or project_name else None
            )
            return {"ok": True, "presets": presets}

        elif action == "resolve":
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
