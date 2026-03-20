import httpx
from helpers.api import ApiHandler, Request, Response
from helpers.providers import get_provider_config
import models

# Model name substrings to exclude from litellm fallback results
_LITELLM_EXCLUDE = frozenset({
    "dall-e", "gpt-image", "tts", "whisper", "audio",
    "realtime", "davinci", "babbage", "ada", "vision-preview",
})


class ModelSearch(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        provider = input.get("provider", "")
        model_type = input.get("model_type", "chat")
        user_api_base = input.get("api_base", "")

        if not provider:
            return {"models": []}

        cfg = self._get_provider_cfg(model_type, provider)
        ml = self._get_models_list(cfg)

        all_models = await self._fetch_models(provider, cfg, ml, user_api_base) or []

        if not all_models:
            litellm_provider = cfg.get("litellm_provider", provider)
            if litellm_provider == provider:
                all_models = self._litellm_fallback(provider, cfg)

        return {"models": sorted(all_models), "provider": provider}

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

    async def _fetch_models(self, provider: str, cfg: dict, ml: dict, user_api_base: str = "") -> list[str] | None:
        api_key = models.get_api_key(provider)
        api_base = user_api_base or (cfg or {}).get("kwargs", {}).get("api_base", "")

        url, fmt = self._resolve_url(ml, api_base)
        if not url:
            return None

        headers = self._build_headers(provider, api_key, cfg)
        params = dict(ml.get("params", {}) or {})

        # Google uses query-param auth
        if provider == "google" and api_key and api_key != "None":
            params.setdefault("key", api_key)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    result = self._parse(resp.json(), fmt)
                    if result:
                        return result
        except Exception:
            pass

        return None

    @staticmethod
    def _resolve_url(ml: dict, api_base: str) -> tuple[str | None, str]:
        fmt = ml.get("format", "openai")
        endpoint = ml.get("endpoint_url", "")
        default_base = ml.get("default_base", "")

        if endpoint.startswith("http"):
            return endpoint, fmt

        base = api_base or default_base
        if not base:
            return None, fmt

        if endpoint:
            return base.rstrip("/") + endpoint, fmt

        # Generic fallback: base + /models
        return base.rstrip("/") + "/models", fmt

    def _build_headers(self, provider: str, api_key: str, cfg: dict | None) -> dict[str, str]:
        headers: dict[str, str] = {}
        has_key = api_key and api_key != "None"

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
            for k, v in extra.items():
                if isinstance(v, str):
                    headers[k] = v

        return headers

    def _litellm_fallback(self, provider: str, cfg: dict | None) -> list[str]:
        try:
            import litellm
            registry = getattr(litellm, "models_by_provider", None)
            if not registry:
                return []

            litellm_provider = (cfg or {}).get("litellm_provider", provider)
            raw_models: set = registry.get(litellm_provider, set())
            if not raw_models:
                return []

            prefix = litellm_provider + "/"
            result: list[str] = []
            for name in raw_models:
                clean = name[len(prefix):] if name.startswith(prefix) else name
                low = clean.lower()
                if any(exc in low for exc in _LITELLM_EXCLUDE):
                    continue
                if clean:
                    result.append(clean)
            return result
        except Exception:
            return []

    def _parse(self, data: dict | list, fmt: str) -> list[str]:
        if fmt == "ollama":
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]

        if fmt == "google":
            result = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if name.startswith("models/"):
                    name = name[7:]
                if name:
                    result.append(name)
            return result

        if isinstance(data, dict) and "data" in data:
            return [m.get("id", "") for m in data["data"] if m.get("id")]

        return []
