import time

from helpers.api import ApiHandler, Request, Response
from helpers import defer
from helpers.extension import call_extensions_async
from helpers.persist_chat import save_tmp_chat
from agent import AgentContext
from plugins._model_config.helpers import model_config

_MODEL_OVERRIDE_REVISION_KEY = "_model_config_override_revision"


def _notify_model_override_changed(ctx: AgentContext) -> None:
    ctx.set_output_data(_MODEL_OVERRIDE_REVISION_KEY, time.time())

    try:
        from helpers.state_monitor_integration import mark_dirty_for_context

        mark_dirty_for_context(ctx.id, reason="model_config.model_override")
    except Exception:
        pass


def _notify_embedding_if_changed(before: dict, after: dict) -> None:
    if before != after:
        defer.DeferredTask().start_task(call_extensions_async, "embedding_model_changed")


class ModelOverride(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = input.get("context_id", "")
        action = input.get("action", "get")  # get | set | set_preset | clear

        if not context_id:
            return Response(status=400, response="Missing context_id")

        ctx = AgentContext.get(context_id)
        if not ctx:
            return Response(status=404, response="Context not found")

        if action == "get":
            override = ctx.get_data("chat_model_override")
            allowed = model_config.is_chat_override_allowed(ctx.agent0)
            return {
                "override": override,
                "allowed": allowed,
                "configured_preset": model_config.get_configured_preset_name(agent=ctx.agent0),
                "effective_preset": model_config.get_effective_preset_name(ctx.agent0),
            }

        elif action == "set":
            if not model_config.is_chat_override_allowed(ctx.agent0):
                return Response(status=403, response="Per-chat override is disabled")
            override_config = input.get("override")
            if not override_config or not isinstance(override_config, dict):
                return Response(status=400, response="Missing or invalid override config")
            previous_embedding = model_config.get_embedding_model_config(ctx.agent0)
            ctx.set_data("chat_model_override", override_config)
            save_tmp_chat(ctx)
            _notify_model_override_changed(ctx)
            _notify_embedding_if_changed(
                previous_embedding,
                model_config.get_embedding_model_config(ctx.agent0),
            )
            return {"ok": True, "override": override_config}

        elif action == "set_preset":
            if not model_config.is_chat_override_allowed(ctx.agent0):
                return Response(status=403, response="Per-chat override is disabled")
            preset_name = input.get("preset_name", "")
            if not preset_name:
                return Response(status=400, response="Missing preset_name")
            previous_embedding = model_config.get_embedding_model_config(ctx.agent0)
            # Verify preset exists
            preset = model_config.get_preset_by_name(preset_name)
            if not preset:
                return Response(status=404, response=f"Preset '{preset_name}' not found")
            # Store as a preset reference
            canonical_name = str(preset.get("name") or preset_name)
            override_value = {"preset_name": canonical_name}
            ctx.set_data("chat_model_override", override_value)
            save_tmp_chat(ctx)
            _notify_model_override_changed(ctx)
            _notify_embedding_if_changed(
                previous_embedding,
                model_config.get_embedding_model_config(ctx.agent0),
            )
            return {"ok": True, "preset_name": canonical_name}

        elif action == "clear":
            previous_embedding = model_config.get_embedding_model_config(ctx.agent0)
            ctx.set_data("chat_model_override", None)
            save_tmp_chat(ctx)
            _notify_model_override_changed(ctx)
            _notify_embedding_if_changed(
                previous_embedding,
                model_config.get_embedding_model_config(ctx.agent0),
            )
            return {
                "ok": True,
                "override": None,
                "effective_preset": model_config.get_configured_preset_name(agent=ctx.agent0),
            }

        return Response(status=400, response=f"Unknown action: {action}")
