from helpers.api import ApiHandler, Input, Output, Request
from plugins._context_window.helpers.usage import (
    latest_provider_usage,
    usage_snapshot,
)
from plugins._model_config.helpers.model_config import get_chat_model_config


class ContextWindow(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        context = self.use_context(str(input.get("context") or ""))
        agent = context.streaming_agent or context.agent0
        window = agent.get_data(agent.DATA_NAME_CTX_WINDOW)
        window = window if isinstance(window, dict) else {}
        config = get_chat_model_config(agent)

        return {
            "tokens": max(int(window.get("tokens") or 0), 0),
            "context_window": max(int(config.get("ctx_length") or 0), 0),
            "usage": usage_snapshot(window.get("usage")),
            "provider_usage": latest_provider_usage(agent),
        }
