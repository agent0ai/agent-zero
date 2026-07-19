from __future__ import annotations

from helpers.extension import Extension
from plugins._oauth.helpers.providers import DUMMY_API_KEY, get_provider, oauth_provider_ids


class OAuthAccountDummyKey(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        del kwargs
        if not isinstance(data, dict):
            return

        args = data.get("args")
        call_kwargs = data.get("kwargs")
        service = ""
        if isinstance(args, (list, tuple)) and args:
            service = str(args[0] or "")
        elif isinstance(call_kwargs, dict):
            service = str(call_kwargs.get("service") or "")

        if service.lower() not in oauth_provider_ids():
            return

        result = str(data.get("result") or "").strip()
        if (not result or result == "None") and oauth_provider_is_connected(service):
            data["result"] = DUMMY_API_KEY


def oauth_provider_is_connected(provider_id: str) -> bool:
    try:
        status = get_provider(provider_id).status()
    except Exception:
        return False
    if not isinstance(status, dict):
        return False
    return bool(status.get("connected"))
