from helpers.api import ApiHandler, Request, Response
from helpers import settings
from helpers.chat_model_override import get_override
from helpers.providers import get_providers
from helpers.settings import _dict_to_env


class ChatModelGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")

        global_settings = settings.get_settings()

        # Try to get existing context (may not exist for new chats)
        context = None
        if ctxid:
            try:
                context = self.use_context(ctxid, create_if_not_exists=False)
            except Exception:
                pass

        # Default: use global settings as base
        model_settings = {
            "chat_model_provider": global_settings["chat_model_provider"],
            "chat_model_name": global_settings["chat_model_name"],
            "chat_model_api_base": global_settings["chat_model_api_base"],
            "chat_model_ctx_length": global_settings["chat_model_ctx_length"],
            "chat_model_ctx_history": global_settings["chat_model_ctx_history"],
            "chat_model_vision": global_settings["chat_model_vision"],
            "chat_model_rl_requests": global_settings["chat_model_rl_requests"],
            "chat_model_rl_input": global_settings["chat_model_rl_input"],
            "chat_model_rl_output": global_settings["chat_model_rl_output"],
            "chat_model_kwargs": global_settings.get("chat_model_kwargs", {}),
        }

        is_custom = False
        if context:
            override = get_override(context)
            if override:
                is_custom = True
                model_settings.update(override)

        # Convert kwargs dict to .env string format for frontend
        if isinstance(model_settings["chat_model_kwargs"], dict):
            model_settings["chat_model_kwargs"] = _dict_to_env(model_settings["chat_model_kwargs"])

        providers = get_providers("chat")

        return {
            "context": ctxid,
            "is_custom": is_custom,
            "settings": model_settings,
            "providers": providers,
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
