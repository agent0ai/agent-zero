from helpers.api import ApiHandler, Request, Response
from helpers import settings
from helpers import persist_chat
from helpers.chat_model_override import set_override, apply_override
from initialize import initialize_agent


class ChatModelSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        is_custom = input.get("is_custom", False)
        new_settings = input.get("settings", {})

        if not ctxid:
            return Response('{"error": "context required"}', status=400, mimetype="application/json")

        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return Response('{"error": "Context not found"}', status=404, mimetype="application/json")

        def _as_int(value, default):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def _as_float(value, default):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def _as_bool(value, default):
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in ("1", "true", "yes", "on"):
                    return True
                if normalized in ("0", "false", "no", "off"):
                    return False
            return default

        if is_custom:
            # Convert kwargs string to dict for storage
            from helpers.settings import _env_to_dict
            kwargs = new_settings.get("chat_model_kwargs", "")
            if isinstance(kwargs, str):
                new_settings["chat_model_kwargs"] = _env_to_dict(kwargs)

            current = context.config.chat_model
            global_settings = settings.get_settings()
            override = {
                "chat_model_provider": (new_settings.get("chat_model_provider", "") or current.provider).strip(),
                "chat_model_name": (new_settings.get("chat_model_name", "") or current.name).strip(),
                "chat_model_api_base": str(new_settings.get("chat_model_api_base", current.api_base) or ""),
                "chat_model_ctx_length": _as_int(new_settings.get("chat_model_ctx_length"), current.ctx_length),
                "chat_model_ctx_history": _as_float(
                    new_settings.get("chat_model_ctx_history"),
                    global_settings["chat_model_ctx_history"],
                ),
                "chat_model_vision": _as_bool(new_settings.get("chat_model_vision"), current.vision),
                "chat_model_rl_requests": _as_int(new_settings.get("chat_model_rl_requests"), current.limit_requests),
                "chat_model_rl_input": _as_int(new_settings.get("chat_model_rl_input"), current.limit_input),
                "chat_model_rl_output": _as_int(new_settings.get("chat_model_rl_output"), current.limit_output),
                "chat_model_kwargs": new_settings.get("chat_model_kwargs", current.kwargs),
            }
            set_override(context, override)
            apply_override(context)
        else:
            # Remove override, reset to global settings
            set_override(context, None)
            global_config = initialize_agent()
            context.config.chat_model = global_config.chat_model

        # Persist the change
        persist_chat.save_tmp_chat(context)

        return {"ok": True, "is_custom": is_custom}
