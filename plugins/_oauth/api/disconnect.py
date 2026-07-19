from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers.providers import CODEX_PROVIDER_ID, get_provider


class Disconnect(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        del request
        raw_provider_id = _provider_id(input)
        try:
            provider = get_provider(raw_provider_id)
            result = provider.disconnect()
            response = {
                "ok": True,
                "provider_id": provider.provider_id,
                "result": result,
                "provider": provider.status(),
                **result,
            }
            if provider.provider_id == CODEX_PROVIDER_ID:
                response["codex"] = response["provider"]
            return response
        except Exception as exc:
            return {
                "ok": False,
                "provider_id": _provider_id_label(raw_provider_id),
                "error": str(exc),
            }


def _provider_id(input: dict) -> object:
    if "provider_id" not in input or input.get("provider_id") is None:
        return CODEX_PROVIDER_ID
    value = input.get("provider_id")
    if isinstance(value, str) and not value.strip():
        return CODEX_PROVIDER_ID
    return value


def _provider_id_label(value: object) -> str:
    if value is None:
        return CODEX_PROVIDER_ID
    text = str(value).strip()
    return text or CODEX_PROVIDER_ID
