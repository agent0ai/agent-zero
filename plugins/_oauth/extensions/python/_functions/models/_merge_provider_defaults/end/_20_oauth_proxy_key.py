from urllib.parse import urlsplit

from helpers import runtime
from helpers.extension import Extension
from plugins._oauth.helpers.providers import DUMMY_API_KEY, get_provider, oauth_provider_ids


class OAuthProxyKey(Extension):
    def execute(self, data: dict, **kwargs):
        args = data.get("args", ())
        provider_id = args[1] if len(args) > 1 else data.get("kwargs", {}).get("original_provider", "")
        if provider_id not in oauth_provider_ids():
            return
        result = data.get("result")
        if not isinstance(result, tuple):
            return

        _, call_kwargs = result
        base = urlsplit(call_kwargs.get("api_base") or "")
        proxy_path = get_provider(provider_id).metadata().proxy_base_path
        if (
            base.scheme in {"http", "https"}
            and base.hostname in {"127.0.0.1", "localhost", "::1"}
            and (base.port or (443 if base.scheme == "https" else 80)) == runtime.get_web_ui_port()
            and base.path.rstrip("/") == f"{proxy_path}/v1"
        ):
            call_kwargs["api_key"] = DUMMY_API_KEY
            if isinstance(call_kwargs.get("extra_headers"), dict):
                call_kwargs["extra_headers"] = {
                    key: value for key, value in call_kwargs["extra_headers"].items()
                    if key.lower() not in {"authorization", "x-api-key"}
                }
