"""POST /api/plugins/_a0_connector/v1/model_presets."""
from __future__ import annotations

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base


class ModelPresets(connector_base.ProtectedConnectorApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        from plugins._model_config.helpers import model_config
        from plugins._model_config.api.model_presets import (
            _embedding_signature,
            _notify_embedding_changed,
            _rename_preset_references,
            _retired_preset_references,
        )

        action = str(input.get("action", "get")).strip() or "get"
        project_name = str(input.get("project_name") or "").strip()
        scope = str(input.get("scope") or "").strip()

        if action == "get":
            if scope == "project":
                return {"ok": True, "presets": []}
            if scope == "combined" or project_name:
                return {
                    "ok": True,
                    "presets": model_config.get_combined_presets(project_name or None),
                    "global_presets": model_config.get_presets(),
                    "project_presets": [],
                }
            return {"ok": True, "presets": model_config.get_presets()}

        if action == "save":
            presets = input.get("presets")
            if not isinstance(presets, list):
                return Response(status=400, response="presets must be an array")
            if scope == "project" or project_name:
                return Response(
                    status=400,
                    response="Preset definitions are global; select a global preset for this project.",
                )
            previous = model_config.get_presets()
            previous_names = {str(preset.get("name") or "") for preset in previous}
            previous_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in previous
            }
            try:
                model_config.save_presets(presets)
            except ValueError as exc:
                return Response(status=400, response=str(exc))
            saved = model_config.get_presets()
            saved_names = {str(preset.get("name") or "") for preset in saved}
            retired = _retired_preset_references(previous_names, saved_names)
            renames = input.get("renames") if isinstance(input.get("renames"), list) else []
            _rename_preset_references([*retired, *renames])
            saved_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in saved
            }
            if previous_embeddings != saved_embeddings:
                _notify_embedding_changed()
            return {"ok": True, "presets": saved}

        if action == "reset":
            if scope == "project" or project_name:
                return Response(status=400, response="Project presets cannot be reset.")
            previous = model_config.get_presets()
            previous_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in previous
            }
            presets = model_config.reset_presets()
            saved_names = {str(preset.get("name") or "") for preset in presets}
            previous_names = {str(preset.get("name") or "") for preset in previous}
            _rename_preset_references(
                _retired_preset_references(previous_names, saved_names)
            )
            current_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in presets
            }
            if previous_embeddings != current_embeddings:
                _notify_embedding_changed()
            return {"ok": True, "presets": presets}

        if action == "resolve":
            name = str(input.get("name") or "").strip()
            if not name:
                return Response(status=400, response="Missing preset name")
            resolved = model_config.resolve_preset(
                name,
                scope="global",
            )
            if not resolved:
                return Response(status=404, response=f"Preset '{name}' not found")
            return {
                "ok": True,
                "preset": {
                    **resolved,
                    "scope": "global",
                    "project_name": "",
                },
            }

        return Response(status=400, response=f"Unknown action: {action}")
