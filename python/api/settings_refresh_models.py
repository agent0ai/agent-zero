from typing import Any

import models as models_module
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.model_discovery import (
    get_models_for_provider,
    clear_cache,
)

# Placeholder used for masked API keys in UI
API_KEY_PLACEHOLDER = "************"


class RefreshModels(ApiHandler):
    """
    API endpoint to dynamically fetch model options from provider APIs.

    Called when:
    - User changes the provider dropdown
    - User enters/updates an API key
    - User explicitly requests a refresh

    Input:
        model_type: "chat" or "embedding"
        provider: Provider ID (e.g., "openai", "anthropic", "openrouter")
        api_keys: Dictionary of API keys (may contain placeholders)
        api_base: Optional custom API base URL for OpenAI-compatible providers
        force_refresh: Optional, if True bypasses cache
        clear_cache: Optional, if True clears all cache first

    Returns:
        models: List of {value, label} options fetched from the provider's API
    """

    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        model_type = input.get("model_type", "chat")
        provider = input.get("provider", "")
        api_keys_input = input.get("api_keys", {})
        api_base = input.get("api_base", "")
        force_refresh = input.get("force_refresh", False)
        should_clear_cache = input.get("clear_cache", False)

        # Handle cache clear request
        if should_clear_cache:
            clear_cache()

        if not provider:
            return {"models": [{"value": "__custom__", "label": "Custom (enter manually)"}]}

        # Resolve actual API keys from environment when placeholders are passed
        api_keys = {}
        for prov, key in api_keys_input.items():
            if key == API_KEY_PLACEHOLDER or not key:
                # Get actual key from environment
                actual_key = models_module.get_api_key(prov)
                if actual_key and actual_key != "None":
                    api_keys[prov] = actual_key
            else:
                # Use the provided key (user may have just entered a new one)
                api_keys[prov] = key

        # Fetch models dynamically from provider API
        models = await get_models_for_provider(
            model_type=model_type,
            provider=provider,
            api_keys=api_keys,
            api_base=api_base if api_base else None,
            force_refresh=force_refresh,
        )

        return {"models": models}
