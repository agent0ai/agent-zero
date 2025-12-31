"""
Dynamic Model Discovery Service for Agent Zero

Fetches available models DIRECTLY from each provider's API based on
which API keys the user has configured. No hardcoded model lists.

Supported Providers:
- OpenAI: GET https://api.openai.com/v1/models
- Anthropic: GET https://api.anthropic.com/v1/models
- Google Gemini: GET https://generativelanguage.googleapis.com/v1beta/models
- Groq: GET https://api.groq.com/openai/v1/models
- Mistral: GET https://api.mistral.ai/v1/models
- DeepSeek: GET https://api.deepseek.com/models
- xAI: GET https://api.x.ai/v1/models
- OpenRouter: GET https://openrouter.ai/api/v1/models
- SambaNova: GET https://api.sambanova.ai/v1/models
- And any OpenAI-compatible provider with api_base set
"""

import json
import os
import time
from typing import Any

from python.helpers import files
from python.helpers.print_style import PrintStyle
from python.helpers.providers import FieldOption

# Cache configuration
CACHE_FILE = "tmp/model_cache.json"
CACHE_TTL_SECONDS = 1 * 60 * 60  # 1 hour (more frequent than before since we want fresh data)

# Provider API endpoints
PROVIDER_ENDPOINTS = {
    "openai": {
        "url": "https://api.openai.com/v1/models",
        "auth_type": "bearer",
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/models",
        "auth_type": "anthropic",
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "auth_type": "query_key",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "auth_type": "bearer",
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/models",
        "auth_type": "bearer",
    },
    "deepseek": {
        "url": "https://api.deepseek.com/models",
        "auth_type": "bearer",
    },
    "xai": {
        "url": "https://api.x.ai/v1/models",
        "auth_type": "bearer",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "auth_type": "bearer",
        "extra_headers": {
            "HTTP-Referer": "https://agent-zero.ai/",
            "X-Title": "Agent Zero",
        },
    },
    "sambanova": {
        "url": "https://api.sambanova.ai/v1/models",
        "auth_type": "bearer",
    },
}

# Providers that are OpenAI-compatible and can use custom api_base
OPENAI_COMPATIBLE_PROVIDERS = {
    "lm_studio",
    "ollama",
    "venice",
    "a0_venice",
    "azure",
    "other",
    "zai",
    "zai_coding",
}


def _load_cache() -> dict[str, Any] | None:
    """Load cached model data if valid."""
    cache_path = files.get_abs_path(CACHE_FILE)
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)

        # Check TTL
        cached_at = cache.get("cached_at", 0)
        if (time.time() - cached_at) > CACHE_TTL_SECONDS:
            return None

        return cache
    except (json.JSONDecodeError, IOError) as e:
        PrintStyle.warning(f"Failed to load model cache: {e}")
        return None


def _save_cache(data: dict[str, Any]):
    """Save model data to cache."""
    cache_path = files.get_abs_path(CACHE_FILE)
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        data["cached_at"] = time.time()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        PrintStyle.warning(f"Failed to save model cache: {e}")


def _get_cached_models(provider: str, model_type: str) -> list[dict[str, str]] | None:
    """Get cached models for a provider if available."""
    cache = _load_cache()
    if cache:
        key = f"{provider}_{model_type}"
        return cache.get("providers", {}).get(key)
    return None


def _cache_models(provider: str, model_type: str, models: list[dict[str, str]]):
    """Cache models for a provider."""
    cache = _load_cache() or {"providers": {}}
    if "providers" not in cache:
        cache["providers"] = {}
    key = f"{provider}_{model_type}"
    cache["providers"][key] = models
    _save_cache(cache)


def _filter_models_by_type(
    models: list[dict[str, str]], model_type: str, provider: str
) -> list[dict[str, str]]:
    """Filter models based on type (chat vs embedding)."""
    if model_type == "embedding":
        # Look for embedding models
        embedding_keywords = ["embed", "embedding", "text-embedding"]
        return [
            m for m in models
            if any(kw in m["id"].lower() for kw in embedding_keywords)
        ]
    else:
        # For chat, exclude embedding, whisper, tts, dall-e, moderation models
        exclude_keywords = [
            "embed", "whisper", "tts", "dall-e", "davinci", "babbage",
            "moderation", "curie", "ada-", "text-ada", "text-babbage",
            "text-curie", "text-davinci", "code-", "audio"
        ]
        # For OpenRouter, include all since they're all chat models
        if provider == "openrouter":
            return models
        return [
            m for m in models
            if not any(kw in m["id"].lower() for kw in exclude_keywords)
        ]


async def _fetch_models_openai_compatible(
    api_key: str,
    base_url: str,
    extra_headers: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Fetch models from any OpenAI-compatible API."""
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    url = f"{base_url.rstrip('/')}/models"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                PrintStyle.warning(f"API returned status {response.status_code} from {url}")
                return []

            data = response.json()
            models_data = data.get("data", [])

            models = []
            for m in models_data:
                model_id = m.get("id", "")
                if model_id:
                    # Use id as name, or use name field if available
                    name = m.get("name") or model_id
                    models.append({"id": model_id, "name": name})

            return models

    except httpx.HTTPError as e:
        PrintStyle.warning(f"Failed to fetch models from {url}: {e}")
        return []
    except Exception as e:
        PrintStyle.error(f"Unexpected error fetching models from {url}: {e}")
        return []


async def _fetch_models_anthropic(api_key: str) -> list[dict[str, str]]:
    """Fetch models from Anthropic API."""
    import httpx

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers=headers,
            )

            if response.status_code != 200:
                PrintStyle.warning(f"Anthropic API returned status {response.status_code}")
                return []

            data = response.json()
            models_data = data.get("data", [])

            models = []
            for m in models_data:
                model_id = m.get("id", "")
                if model_id:
                    display_name = m.get("display_name") or model_id
                    models.append({"id": model_id, "name": display_name})

            return models

    except httpx.HTTPError as e:
        PrintStyle.warning(f"Failed to fetch Anthropic models: {e}")
        return []
    except Exception as e:
        PrintStyle.error(f"Unexpected error fetching Anthropic models: {e}")
        return []


async def _fetch_models_google(api_key: str) -> list[dict[str, str]]:
    """Fetch models from Google Gemini API."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            )

            if response.status_code != 200:
                PrintStyle.warning(f"Google API returned status {response.status_code}")
                return []

            data = response.json()
            models_data = data.get("models", [])

            models = []
            for m in models_data:
                # Google returns names like "models/gemini-pro"
                full_name = m.get("name", "")
                model_id = full_name.replace("models/", "") if full_name.startswith("models/") else full_name
                if model_id:
                    display_name = m.get("displayName") or model_id
                    models.append({"id": model_id, "name": display_name})

            return models

    except httpx.HTTPError as e:
        PrintStyle.warning(f"Failed to fetch Google models: {e}")
        return []
    except Exception as e:
        PrintStyle.error(f"Unexpected error fetching Google models: {e}")
        return []


async def _fetch_models_for_provider(
    provider: str,
    api_key: str,
    api_base: str | None = None,
) -> list[dict[str, str]]:
    """Fetch models from a specific provider."""
    if not api_key or api_key == "None" or api_key == "":
        return []

    # Handle Anthropic separately (different auth)
    if provider == "anthropic":
        return await _fetch_models_anthropic(api_key)

    # Handle Google separately (query param auth)
    if provider == "google":
        return await _fetch_models_google(api_key)

    # Handle known providers with predefined endpoints
    if provider in PROVIDER_ENDPOINTS:
        endpoint_config = PROVIDER_ENDPOINTS[provider]
        return await _fetch_models_openai_compatible(
            api_key=api_key,
            base_url=endpoint_config["url"].rsplit("/models", 1)[0],
            extra_headers=endpoint_config.get("extra_headers"),
        )

    # Handle OpenAI-compatible providers with custom api_base
    if provider in OPENAI_COMPATIBLE_PROVIDERS and api_base:
        return await _fetch_models_openai_compatible(
            api_key=api_key,
            base_url=api_base,
        )

    return []


async def get_models_for_provider(
    model_type: str,
    provider: str,
    api_keys: dict[str, str] | None = None,
    api_base: str | None = None,
    force_refresh: bool = False,
) -> list[FieldOption]:
    """
    Get available models for a provider by fetching from their API.

    Args:
        model_type: Either 'chat' or 'embedding'
        provider: Provider ID (e.g., 'openai', 'anthropic', 'openrouter')
        api_keys: Dictionary of API keys keyed by provider name
        api_base: Optional custom API base URL for OpenAI-compatible providers
        force_refresh: If True, bypass cache

    Returns:
        List of FieldOption dicts with 'value' and 'label' keys
    """
    if api_keys is None:
        api_keys = {}

    # Get API key for this provider
    api_key = api_keys.get(provider, "")

    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = _get_cached_models(provider, model_type)
        if cached:
            return _convert_to_options(cached)

    # Fetch from provider API
    models = await _fetch_models_for_provider(provider, api_key, api_base)

    if models:
        # Filter by model type
        models = _filter_models_by_type(models, model_type, provider)

        # Sort by name
        models.sort(key=lambda x: x["name"].lower())

        # Cache the results
        _cache_models(provider, model_type, models)

    return _convert_to_options(models)


def _convert_to_options(models: list[dict[str, str]]) -> list[FieldOption]:
    """Convert model list to FieldOption format."""
    options: list[FieldOption] = []

    for m in models:
        options.append({
            "value": m["id"],
            "label": m["name"],
        })

    # Always add custom option at the end
    options.append({
        "value": "__custom__",
        "label": "Custom (enter manually)",
    })

    return options


def get_models_for_provider_sync(
    model_type: str,
    provider: str,
    api_keys: dict[str, str] | None = None,
) -> list[FieldOption]:
    """
    Synchronous version - returns cached models or empty list with custom option.
    Used for initial settings load; async refresh happens on provider change.
    """
    if api_keys is None:
        api_keys = {}

    # Check cache
    cached = _get_cached_models(provider, model_type)
    if cached:
        return _convert_to_options(cached)

    # No cache available - return just the custom option
    # The frontend will trigger an async refresh when the modal opens
    return [{
        "value": "__custom__",
        "label": "Custom (enter manually)",
    }]


def clear_cache():
    """Clear the model cache to force refresh on next request."""
    cache_path = files.get_abs_path(CACHE_FILE)
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            PrintStyle.info("Model cache cleared")
        except IOError as e:
            PrintStyle.warning(f"Failed to clear model cache: {e}")


def clear_provider_cache(provider: str, model_type: str = "chat"):
    """Clear cache for a specific provider."""
    cache = _load_cache()
    if cache and "providers" in cache:
        key = f"{provider}_{model_type}"
        if key in cache["providers"]:
            del cache["providers"][key]
            _save_cache(cache)
            PrintStyle.info(f"Cleared cache for {provider}/{model_type}")
