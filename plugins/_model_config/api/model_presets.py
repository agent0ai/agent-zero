import json

from helpers.api import ApiHandler, Request, Response
from helpers import defer, files, plugins
from helpers.extension import call_extensions_async
from helpers.persist_chat import _write_atomic, save_tmp_chat
from agent import AgentContext
from plugins._model_config.api.model_override import _notify_model_override_changed
from plugins._model_config.helpers import model_config


def _rename_preset_references(renames: object) -> None:
    if not isinstance(renames, list):
        return
    mapping = {
        str(item.get("from") or "").strip().casefold(): str(item.get("to") or "").strip()
        for item in renames
        if isinstance(item, dict)
        and str(item.get("from") or "").strip()
        and str(item.get("to") or "").strip()
    }
    mapping.pop(model_config.DEFAULT_PRESET_NAME.casefold(), None)
    if not mapping:
        return

    assets = plugins.find_plugin_assets(
        plugins.CONFIG_FILE_NAME,
        plugin_name="_model_config",
        project_name="*",
        agent_profile="*",
        only_first=False,
    )
    for asset in assets:
        path = str(asset.get("path") or "")
        try:
            config = json.loads(files.read_file(path))
        except Exception:
            continue
        if not isinstance(config, dict):
            continue
        selected = str(config.get(model_config.MODEL_PRESET_CONFIG_KEY) or "").strip()
        replacement = mapping.get(selected.casefold())
        if replacement:
            config[model_config.MODEL_PRESET_CONFIG_KEY] = replacement
            files.write_file(path, json.dumps(config))

    # Chats are lazy-loaded, so update durable references as well as live
    # AgentContext objects. Otherwise renaming a preset would silently send an
    # unopened chat back to Default the next time it is loaded.
    loaded_context_ids = {str(context.id) for context in AgentContext.all()}
    chat_paths = files.find_existing_paths_by_pattern(
        files.get_abs_path("usr", "chats", "*", "chat.json")
    )
    for path in chat_paths:
        chat_id = files.basename(files.dirname(path))
        if chat_id in loaded_context_ids:
            continue
        try:
            chat = json.loads(files.read_file(path))
        except Exception:
            continue
        data = chat.get("data") if isinstance(chat, dict) else None
        override = data.get("chat_model_override") if isinstance(data, dict) else None
        selected = str(override.get("preset_name") or "").strip() if isinstance(override, dict) else ""
        replacement = mapping.get(selected.casefold())
        if not replacement:
            continue
        data["chat_model_override"] = {"preset_name": replacement}
        _write_atomic(path, json.dumps(chat, ensure_ascii=False))

    for context in AgentContext.all():
        override = context.get_data("chat_model_override")
        if not isinstance(override, dict):
            continue
        selected = str(override.get("preset_name") or "").strip()
        replacement = mapping.get(selected.casefold())
        if not replacement:
            continue
        context.set_data("chat_model_override", {"preset_name": replacement})
        save_tmp_chat(context)
        _notify_model_override_changed(context)


def _retired_preset_references(
    previous_names: set[str],
    saved_names: set[str],
) -> list[dict[str, str]]:
    saved_by_casefold = {name.casefold(): name for name in saved_names}
    return [
        {
            "from": name,
            "to": saved_by_casefold.get(
                name.casefold(),
                model_config.DEFAULT_PRESET_NAME,
            ),
        }
        for name in previous_names - saved_names
    ]


def _embedding_signature(preset: dict | None):
    if not isinstance(preset, dict):
        return {}
    default = model_config.resolve_preset(model_config.DEFAULT_PRESET_NAME) or {}
    config = model_config.preset_to_config(default)
    if str(preset.get("name") or "") != model_config.DEFAULT_PRESET_NAME:
        config = model_config.build_config_from_preset(
            preset,
            config,
            strip_api_key=False,
        )
    embedding = config.get("embedding_model")
    return embedding if isinstance(embedding, dict) else {}


def _notify_embedding_changed() -> None:
    defer.DeferredTask().start_task(call_extensions_async, "embedding_model_changed")


class ModelPresets(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
        project_name = str(input.get("project_name") or "").strip()
        agent_profile = str(input.get("agent_profile") or "").strip()
        context_id = str(input.get("context_id") or "").strip()
        scope = str(input.get("scope") or "").strip()

        if action == "get":
            if scope == "project":
                return {"ok": True, "presets": []}
            presets = model_config.get_presets()
            context = AgentContext.get(context_id) if context_id else None
            if context:
                configured = model_config.get_configured_preset_name(agent=context.agent0)
                selected = model_config.get_effective_preset_name(context.agent0)
            else:
                configured = model_config.get_configured_preset_name(
                    project_name=project_name or None,
                    agent_profile=agent_profile or None,
                )
                selected = configured
            return {
                "ok": True,
                "presets": presets,
                "global_presets": presets,
                "project_presets": [],
                "configured_preset": configured,
                "selected_preset": selected,
            }

        elif action == "save":
            presets = input.get("presets")
            if not isinstance(presets, list):
                return Response(status=400, response="presets must be an array")
            if scope == "project" or project_name:
                return Response(
                    status=400,
                    response="Preset definitions are global; select a global preset for this project.",
                )
            previous_names = {
                str(preset.get("name") or "") for preset in model_config.get_presets()
            }
            previous_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in model_config.get_presets()
            }
            try:
                model_config.save_presets(presets)
            except ValueError as exc:
                return Response(status=400, response=str(exc))
            saved_names = {
                str(preset.get("name") or "") for preset in model_config.get_presets()
            }
            retired = _retired_preset_references(previous_names, saved_names)
            renames = input.get("renames") if isinstance(input.get("renames"), list) else []
            _rename_preset_references([*retired, *renames])
            saved_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in model_config.get_presets()
            }
            if previous_embeddings != saved_embeddings:
                _notify_embedding_changed()
            return {"ok": True, "presets": model_config.get_presets()}

        elif action == "reset":
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
            retired = _retired_preset_references(previous_names, saved_names)
            _rename_preset_references(retired)
            current_embeddings = {
                str(preset.get("name") or ""): _embedding_signature(preset)
                for preset in presets
            }
            if previous_embeddings != current_embeddings:
                _notify_embedding_changed()
            return {"ok": True, "presets": presets}

        elif action == "select":
            name = str(input.get("name") or "").strip()
            preset = model_config.resolve_preset(name)
            if not preset:
                return Response(status=404, response=f"Preset '{name}' not found")
            canonical_name = str(preset.get("name") or model_config.DEFAULT_PRESET_NAME)
            context = AgentContext.get(context_id) if context_id else None
            previous_embedding = (
                model_config.get_embedding_model_config(context.agent0)
                if context
                else None
            )
            previous_name = (
                model_config.get_effective_preset_name(context.agent0)
                if context
                else model_config.get_configured_preset_name(
                    project_name=project_name or None,
                    agent_profile=agent_profile or None,
                )
            )
            previous = model_config.resolve_preset(previous_name)
            plugins.save_plugin_config(
                "_model_config",
                project_name,
                agent_profile,
                {model_config.MODEL_PRESET_CONFIG_KEY: canonical_name},
            )

            if context:
                context.set_data("chat_model_override", {"preset_name": canonical_name})
                save_tmp_chat(context)
                _notify_model_override_changed(context)
            current_embedding = (
                model_config.get_embedding_model_config(context.agent0)
                if context
                else _embedding_signature(preset)
            )
            if (previous_embedding or _embedding_signature(previous)) != current_embedding:
                _notify_embedding_changed()
            return {"ok": True, "selected_preset": canonical_name}

        elif action == "resolve":
            name = str(input.get("name") or "").strip()
            if not name:
                return Response(status=400, response="Missing preset name")
            resolved = model_config.resolve_preset(name)
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
