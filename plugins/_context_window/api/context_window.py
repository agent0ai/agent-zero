import re

from helpers.api import ApiHandler, Input, Output, Request
from helpers import plugins
from plugins._context_window.helpers.currency import get_exchange_rate
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
        display = plugins.get_plugin_config("_context_window") or {}
        provider_usage = latest_provider_usage(agent)
        currency = str(display.get("price_currency") or "USD").upper()
        if not re.fullmatch(r"[A-Z]{3}", currency):
            currency = "USD"
        price_currency = {"code": "USD", "rate": 1, "date": ""}
        if currency != "USD" and display.get("show_price") is not False and "cost" in provider_usage:
            if provider_usage["cost"] == 0:
                price_currency = {"code": currency, "rate": None, "date": ""}
            else:
                price_currency = await get_exchange_rate(currency) or {
                    "code": "USD", "rate": 1, "date": "", "requested": currency,
                }

        return {
            "tokens": max(int(window.get("tokens") or 0), 0),
            "context_window": max(int(config.get("ctx_length") or 0), 0),
            "usage": usage_snapshot(window.get("usage")),
            "provider_usage": provider_usage,
            "price_currency": price_currency,
            "display": {
                key: display.get(key, True) is not False
                for key in ("show_breakdown", "show_price", "show_cache_hit", "show_tokens")
            },
        }
