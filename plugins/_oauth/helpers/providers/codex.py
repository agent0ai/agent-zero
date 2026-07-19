from __future__ import annotations

import secrets
import webbrowser
from typing import Any

from plugins._oauth.helpers.providers.base import (
    CODEX_PROVIDER_ID,
    DUMMY_API_KEY,
    CallbackResult,
    LoginPollResult,
    LoginStartResult,
    OAuthProviderMetadata,
)
from plugins._oauth.helpers.state import (
    get_device_attempt,
    pop_device_attempt,
    put_attempt,
    put_device_attempt,
)


CODEX_DEFAULT_MODEL = "gpt-5.5"
CODEX_FALLBACK_CONFIG = {
    "enabled": True,
    "models": [],
    "proxy_base_path": "/oauth/codex",
    "callback_path": "/auth/callback",
    "open_browser_from_server": False,
}


class CodexOAuthProvider:
    provider_id = CODEX_PROVIDER_ID

    def metadata(self) -> OAuthProviderMetadata:
        cfg = _codex_config()
        models = list(cfg["models"])
        return OAuthProviderMetadata(
            provider_id=CODEX_PROVIDER_ID,
            display_name="Codex/ChatGPT",
            short_name="Codex",
            model_provider_id=CODEX_PROVIDER_ID,
            icon="openai",
            auth_flow="device_code",
            default_model=models[0] if models else CODEX_DEFAULT_MODEL,
            default_models=models,
            proxy_base_path=cfg["proxy_base_path"],
            callback_path=cfg["callback_path"],
        )

    def status(self) -> dict[str, Any]:
        from plugins._oauth.helpers import codex

        cfg = _codex_config()
        return {
            **self.metadata().to_dict(),
            **codex.status(),
            "enabled": cfg["enabled"],
            "proxy_base_path": cfg["proxy_base_path"],
            "callback_path": cfg["callback_path"],
            "v1_base_path": f'{cfg["proxy_base_path"]}/v1',
        }

    def start_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginStartResult:
        del input, request
        from plugins._oauth.helpers import codex

        cfg = _codex_config()
        if not cfg["enabled"]:
            return LoginStartResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                flow="device_code",
                error="Codex/ChatGPT account connection is disabled.",
            )

        try:
            device = codex.request_device_code()
            attempt_id = secrets.token_urlsafe(24)
            attempt = put_device_attempt(
                attempt_id,
                device["device_auth_id"],
                device["user_code"],
                device["interval"],
                device["expires_at"],
                provider_id=CODEX_PROVIDER_ID,
            )
        except Exception as exc:
            return LoginStartResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                flow="device_code",
                error=str(exc),
            )

        return LoginStartResult(
            ok=True,
            provider_id=CODEX_PROVIDER_ID,
            flow="device_code",
            attempt_id=attempt.attempt_id,
            verification_url=device["verification_url"],
            user_code=attempt.user_code,
            interval=attempt.interval,
            expires_at=attempt.expires_at,
        )

    def start_browser_login(
        self,
        input: dict[str, Any] | None = None,
        request: Any = None,
    ) -> LoginStartResult:
        del input
        cfg = _codex_config()
        if not cfg["enabled"]:
            return LoginStartResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                flow="browser_pkce",
                error="Codex/ChatGPT account connection is disabled.",
            )

        from plugins._oauth.helpers import codex

        redirect_uri = _redirect_uri(request, cfg["callback_path"])
        pkce = codex.generate_pkce()
        state = codex.generate_state()
        attempt = put_attempt(
            state,
            pkce.verifier,
            redirect_uri,
            provider_id=CODEX_PROVIDER_ID,
        )
        auth_url = codex.build_authorize_url(redirect_uri, state, pkce)

        if cfg["open_browser_from_server"]:
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

        return LoginStartResult(
            ok=True,
            provider_id=CODEX_PROVIDER_ID,
            flow="browser_pkce",
            auth_url=auth_url,
            redirect_uri=redirect_uri,
            expires_at=attempt.expires_at,
        )

    def poll_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginPollResult:
        del request
        data = input or {}
        attempt_id = str(data.get("attempt_id") or "").strip()
        if not attempt_id:
            return LoginPollResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                error="Missing device authorization attempt.",
            )

        attempt = get_device_attempt(attempt_id)
        if attempt is None:
            return LoginPollResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                expired=True,
                error="Device authorization expired.",
            )
        if attempt.provider_id != CODEX_PROVIDER_ID:
            return LoginPollResult(
                ok=False,
                provider_id=CODEX_PROVIDER_ID,
                error="Device authorization provider mismatch.",
            )

        try:
            from plugins._oauth.helpers import codex

            result = codex.poll_device_authorization(
                attempt.device_auth_id,
                attempt.user_code,
            )
        except Exception as exc:
            return LoginPollResult(ok=False, provider_id=CODEX_PROVIDER_ID, error=str(exc))

        if result.get("completed"):
            pop_device_attempt(attempt_id)
            account_id = str(result.get("account_id") or "")
            return LoginPollResult(
                ok=True,
                provider_id=CODEX_PROVIDER_ID,
                completed=True,
                account_label=str(result.get("account_label") or account_id),
                account_id=account_id,
            )

        return LoginPollResult(
            ok=True,
            provider_id=CODEX_PROVIDER_ID,
            completed=False,
            interval=attempt.interval,
            expires_at=attempt.expires_at,
        )

    def complete_callback(
        self,
        args: dict[str, Any],
        request: Any = None,
    ) -> CallbackResult:
        del args, request
        return CallbackResult(
            ok=False,
            provider_id=CODEX_PROVIDER_ID,
            error="Codex OAuth callback is handled by compatibility routes.",
        )

    def manual_callback(
        self,
        input: dict[str, Any],
        request: Any = None,
    ) -> LoginPollResult:
        del input, request
        return LoginPollResult(
            ok=False,
            provider_id=CODEX_PROVIDER_ID,
            error="Codex uses device-code login in this UI.",
        )

    def models(self) -> list[str]:
        from plugins._oauth.helpers import codex

        return codex.fetch_models()

    def model_catalog(self) -> list[dict[str, Any]]:
        from plugins._oauth.helpers import codex

        return codex.fetch_model_catalog()

    def disconnect(self) -> dict[str, Any]:
        from plugins._oauth.helpers import codex

        return codex.disconnect_auth()

    def api_key(self) -> str:
        return DUMMY_API_KEY

    def register_routes(self, app: Any) -> None:
        del app
        return None


def _redirect_uri(request: Any, callback_path: str) -> str:
    origin = ""
    if request is not None:
        origin = (getattr(request, "headers", {}).get("Origin") or "").rstrip("/")
        if not _is_local_origin(origin):
            origin = getattr(request, "url_root", "").rstrip("/")
    return f"{origin}{callback_path}"


def _codex_config() -> dict[str, Any]:
    try:
        from plugins._oauth.helpers.config import codex_config

        return codex_config()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("plugins._oauth"):
            raise
        return dict(CODEX_FALLBACK_CONFIG)


def _is_local_origin(origin: str) -> bool:
    if not origin:
        return False
    return (
        origin.startswith("http://localhost:")
        or origin == "http://localhost"
        or origin.startswith("http://127.0.0.1:")
        or origin == "http://127.0.0.1"
        or origin.startswith("http://[::1]:")
        or origin == "http://[::1]"
    )
