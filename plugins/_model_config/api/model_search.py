from __future__ import annotations

from typing import Any

import httpx
from helpers.api import ApiHandler, Request, Response
from helpers.providers import get_provider_config
import models

# Model name substrings to exclude from chat dropdowns and LiteLLM fallback results.
_NON_CHAT_EXCLUDE = frozenset({
    "dall-e",
    "gpt-image",
    "image",
    "tts",
    "text-to-speech",
    "whisper",
    "audio",
    "transcribe",
    "transcription",
    "speech",
    "realtime",
    "embedding",
    "embed",
    "moderation",
    "omni-moderation",
    "vision-preview",
})


class ModelSearch(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        provider = str(input.get("provider", "") or "").strip().lower()
        model_type = str(input.get("model_type", "chat") or "chat").strip().lower()
        query = str(input.get("query", "") or "").strip().lower()
        user_api_base = str(input.get("api_base", "") or "").strip()

        if not provider:
            return {"models": [], "provider": "", "source": "none", "error": ""}

        cfg = self._get_provider_cfg(model_type, provider)
        ml = self._get_models_list(cfg)

        models_list, source, error = await self._fetch_models(provider, cfg, ml, user_api_base)

        if not models_list:
            fallback = self._litellm_fallback(provider, cfg)
            if fallback:
                models_list = fallback
                source = "litellm_registry"
            elif not source:
                source = "none"

        models_list = self._filter_models(models_list, model_type)
        if query:
            models_list = [name for name in models_list if query in name.lower()]

        return {
            "models": sorted(set(models_list), key=str.lower),
            "provider": provider,
            "source": source,
            "error": error,
        }

    @staticmethod
    def _get_provider_cfg(model_type: str, provider: str) -> dict:
        """Get provider config, falling back to chat config for models_list."""
        cfg = get_provider_config(model_type, provider) or {}
        if model_type != "chat" and not cfg.get("models_list"):
            chat_cfg = get_provider_config("chat", provider) or {}
            if chat_cfg.get("models_list"):
                merged = dict(cfg)
                merged["models_list"] = chat_cfg["models_list"]
                return merged
        return cfg

    @staticmethod
    def _get_models_list(cfg: dict) -> dict:
        """Extract models_list sub-config."""
        return cfg.get("models_list") or {}

    async def _fetch_models(
        self,
        provider: str,
        cfg: dict,
        ml: dict,
        user_api_base: str = "",
    ) -> tuple[list[str], str, str]:
        api_key = models.get_api_key(provider)
        kwargs = (cfg or {}).get("kwargs", {}) or {}
        api_base = user_api_base or kwargs.get("api_base", "") or ml.get("default_base", "")
        effective_ml = dict(ml or {})

        # Ollama's native endpoint is /api/tags, but user-supplied /v1 bases usually
        # mean the OpenAI-compatible /v1/models endpoint.
        if provider == "ollama" and user_api_base.rstrip("/").endswith("/v1"):
            effective_ml["endpoint_url"] = "/models"
            effective_ml["format"] = "openai"

        url, fmt = self._resolve_url(effective_ml, api_base)
        if not url:
            return [], "none", ""

        headers = self._build_headers(provider, api_key, cfg)
        params = dict(effective_ml.get("params", {}) or {})

        # Google uses query-param auth for the public models list endpoint.
        if provider == "google" and api_key and api_key != "None":
            params.setdefault("key", api_key)

        urls: list[tuple[str, str]] = [(url, fmt)]
        if provider == "ollama" and fmt == "ollama":
            ps_url = self._ollama_ps_url(url)
            if ps_url and ps_url != url:
                urls.append((ps_url, "ollama"))

        combined: list[str] = []
        errors: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for candidate_url, candidate_fmt in urls:
                    resp = await client.get(candidate_url, headers=headers, params=params)
                    if resp.status_code == 200:
                        combined.extend(self._parse(resp.json(), candidate_fmt))
                    else:
                        errors.append(f"{candidate_url}: HTTP {resp.status_code}")
        except Exception as exc:
            errors.append(str(exc))

        if combined:
            return combined, "provider_endpoint", ""
        return [], "provider_endpoint", "; ".join(errors)

    @staticmethod
    def _resolve_url(ml: dict, api_base: str) -> tuple[str | None, str]:
        fmt = ml.get("format", "openai")
        endpoint = str(ml.get("endpoint_url", "") or "")
        default_base = str(ml.get("default_base", "") or "")

        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint, fmt

        base = str(api_base or default_base or "").strip()
        if not base:
            return None, fmt

        endpoint = endpoint or "/models"
        base = base.rstrip("/")

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        # Avoid doubled /v1/v1 when users enter a base ending in /v1 and metadata
        # also contains a versioned endpoint.
        if base.endswith("/v1") and endpoint.startswith("/v1/"):
            endpoint = endpoint[3:]

        return base + endpoint, fmt

    @staticmethod
    def _ollama_ps_url(resolved_url: str) -> str:
        """Return the Ollama running-model endpoint for a resolved native URL."""
        marker = "/api/"
        if marker not in resolved_url:
            return ""
        return resolved_url.split(marker, 1)[0].rstrip("/") + "/api/ps"

    def _build_headers(self, provider: str, api_key: str, cfg: dict | None) -> dict[str, str]:
        headers: dict[str, str] = {}
        has_key = bool(api_key and api_key.strip() and api_key != "None")

        if provider == "anthropic":
            if has_key:
                headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        elif provider == "google":
            pass
        elif provider == "azure":
            if has_key:
                headers["api-key"] = api_key
        elif provider not in ("ollama", "lm_studio"):
            if has_key:
                headers["Authorization"] = f"Bearer {api_key}"

        extra = (cfg or {}).get("kwargs", {}).get("extra_headers", {})
        if isinstance(extra, dict):
            for key, value in extra.items():
                if isinstance(value, str):
                    headers[key] = value

        return headers

    def _litellm_fallback(self, provider: str, cfg: dict | None) -> list[str]:
        try:
            import litellm

            registry = getattr(litellm, "models_by_provider", None)
            if not registry:
                return []

            litellm_provider = (cfg or {}).get("litellm_provider", provider)
            raw_models = registry.get(litellm_provider, set()) or set()
            if not raw_models:
                return []

            prefix = litellm_provider + "/"
            result: list[str] = []
            for name in raw_models:
                clean = str(name or "")
                clean = clean[len(prefix):] if clean.startswith(prefix) else clean
                if clean and not self._is_non_chat_model(clean):
                    result.append(clean)
            return result
        except Exception:
            return []

    def _parse(self, data: dict | list, fmt: str) -> list[str]:
        if isinstance(data, list):
            return self._parse_list(data)

        if not isinstance(data, dict):
            return []

        if fmt == "ollama":
            return self._parse_models_array(data.get("models", []), "name")

        if fmt == "google":
            result = []
            for item in data.get("models", []) or []:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "") or "")
                if name.startswith("models/"):
                    name = name[7:]
                if name:
                    result.append(name)
            return result

        if "data" in data:
            return self._parse_models_array(data.get("data", []), "id")

        if "models" in data:
            return self._parse_models_array(data.get("models", []), "id")

        return []

    @staticmethod
    def _parse_models_array(items: Any, primary_key: str) -> list[str]:
        if not isinstance(items, list):
            return []
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                value = item.get(primary_key) or item.get("id") or item.get("name")
                if value:
                    result.append(str(value))
        return result

    def _parse_list(self, data: list) -> list[str]:
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                value = item.get("id") or item.get("name")
                if value:
                    result.append(str(value))
        return result

    def _filter_models(self, model_names: list[str], model_type: str) -> list[str]:
        cleaned = []
        for name in model_names or []:
            value = str(name or "").strip()
            if not value:
                continue
            if model_type == "chat" and self._is_non_chat_model(value):
                continue
            cleaned.append(value)
        return cleaned

    @staticmethod
    def _is_non_chat_model(name: str) -> bool:
        low = name.lower()
        return any(token in low for token in _NON_CHAT_EXCLUDE)
