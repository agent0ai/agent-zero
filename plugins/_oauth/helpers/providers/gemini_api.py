from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from plugins._oauth.helpers.providers.base import (
    DUMMY_API_KEY,
    GEMINI_API_PROVIDER_ID,
    CallbackResult,
    LoginPollResult,
    LoginStartResult,
    OAuthProviderMetadata,
    ProviderError,
    provider_auth_path,
    read_json_file,
    write_private_json,
)
from plugins._oauth.helpers.providers.common import (
    as_int as _as_int,
    as_optional_string as _as_optional_string,
    error_message as _error_message,
    expires_ms as _expires_ms,
    json_payload as _json_payload,
    latest_attempt,
    models_from_payload as _models_from_payload,
    parse_manual_callback,
)
from plugins._oauth.helpers.state import get_attempt, pop_attempt, put_attempt


GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GEMINI_OPENAI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
CURATED_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]
NOT_CONNECTED_MESSAGE = "Google Gemini API OAuth is not connected yet."
CLIENT_CONFIG_NOTE = (
    "Requires a Google Cloud OAuth client with the Generative Language API enabled. "
    "This uses Gemini API billing/quotas, not Antigravity or Gemini Code Assist subscription quota."
)
REFRESH_MARGIN_MS = 60_000


class GeminiApiOAuthProvider:
    provider_id = GEMINI_API_PROVIDER_ID

    def auth_path(self) -> Path:
        return provider_auth_path("gemini_api")

    def read_auth(self) -> dict[str, Any]:
        return read_json_file(self.auth_path())

    def write_auth(self, data: dict[str, Any]) -> None:
        write_private_json(self.auth_path(), data)

    def metadata(self) -> OAuthProviderMetadata:
        cfg = _gemini_api_config()
        base_path = cfg["proxy_base_path"]
        return OAuthProviderMetadata(
            provider_id=GEMINI_API_PROVIDER_ID,
            display_name="Google Cloud Gemini",
            short_name="Google Cloud",
            model_provider_id=GEMINI_API_PROVIDER_ID,
            icon="google",
            auth_flow="browser_pkce",
            default_model="gemini-3.5-flash",
            default_models=list(CURATED_MODELS),
            proxy_base_path=base_path,
            callback_path=cfg["callback_path"],
            supports_manual_callback=True,
            supports_oauth_client_config=True,
            supports_quota_project=True,
            note=CLIENT_CONFIG_NOTE,
        )

    def status(self) -> dict[str, Any]:
        cfg = _gemini_api_config()
        auth = self.read_auth()
        access = str(auth.get("access") or "")
        refresh = str(auth.get("refresh") or "")
        client_id = str(cfg.get("client_id") or auth.get("client_id") or "")
        quota_project_id = str(cfg.get("quota_project_id") or auth.get("quota_project_id") or "")
        result = {
            **self.metadata().to_dict(),
            "enabled": cfg["enabled"],
            "connected": bool(access and refresh),
            "account_label": _account_label(auth) if access or refresh else "",
            "client_id": client_id,
            "client_secret_configured": bool(cfg.get("client_secret") or auth.get("client_secret")),
            "quota_project_id": quota_project_id,
            "base_url": safe_api_base_url(auth.get("base_url") or cfg.get("api_base_url")),
            "auth_file_path": str(self.auth_path()),
            "v1_base_path": f'{cfg["proxy_base_path"]}/v1',
        }
        if access and refresh and _as_int(auth.get("expires"), 0) <= int(time.time() * 1000):
            result["warning"] = "Google Gemini API OAuth access token is expired and will be refreshed on the next request."
        return result

    def start_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginStartResult:
        data = input or {}
        cfg = _gemini_api_config()
        if not cfg["enabled"]:
            return LoginStartResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                flow="browser_pkce",
                error="Google Gemini API OAuth connection is disabled.",
            )

        try:
            client = _client_config(data, cfg)
            codex = _codex_helper()
            pkce = codex.generate_pkce()
            state = codex.generate_state()
            redirect_uri = _redirect_uri(request, cfg["callback_path"])
            attempt = put_attempt(
                state,
                pkce.verifier,
                redirect_uri,
                provider_id=GEMINI_API_PROVIDER_ID,
                extra={
                    "client_id": client["client_id"],
                    "client_secret": client["client_secret"],
                    "quota_project_id": client["quota_project_id"],
                    "scope": " ".join(cfg["scopes"]),
                    "code_challenge": pkce.challenge,
                    "token_endpoint": GOOGLE_TOKEN_ENDPOINT,
                    "api_base_url": safe_api_base_url(cfg["api_base_url"]),
                },
            )
            query = {
                "response_type": "code",
                "client_id": client["client_id"],
                "redirect_uri": redirect_uri,
                "scope": " ".join(cfg["scopes"]),
                "code_challenge": pkce.challenge,
                "code_challenge_method": "S256",
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
                "include_granted_scopes": "true",
            }
            auth_url = f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{urlencode(query)}"
        except Exception as exc:
            return LoginStartResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                flow="browser_pkce",
                error=str(exc),
                message=str(exc),
            )

        return LoginStartResult(
            ok=True,
            provider_id=GEMINI_API_PROVIDER_ID,
            flow="browser_pkce",
            auth_url=auth_url,
            redirect_uri=redirect_uri,
            expires_at=attempt.expires_at,
        )

    def poll_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginPollResult:
        del input, request
        return LoginPollResult(
            ok=False,
            provider_id=GEMINI_API_PROVIDER_ID,
            error="Google Gemini API OAuth uses browser callback login.",
        )

    def exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
        client_id: str,
        client_secret: str,
    ) -> dict[str, Any]:
        import requests

        _validate_google_token_endpoint(token_endpoint)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": code_verifier,
        }
        if client_secret:
            data["client_secret"] = client_secret

        response = requests.post(
            token_endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=data,
            timeout=30,
        )
        payload = _json_payload(response)
        if not response.ok:
            raise ProviderError(
                _error_message(payload, f"Google Gemini API token exchange failed with status {response.status_code}."),
                code="token_exchange_failed",
                status=response.status_code,
            )
        _validate_token_payload(payload, require_refresh=True)
        return payload

    def manual_callback(self, input: dict[str, Any], request: Any = None) -> LoginPollResult:
        del request
        raw = input.get("callback")
        if raw is None:
            raw = input.get("callback_url")
        return self._complete_from_callback(parse_manual_callback(raw), allow_missing_state=True)

    def complete_callback(
        self,
        args: dict[str, Any],
        request: Any = None,
    ) -> CallbackResult:
        del request
        callback = {
            "code": _as_optional_string(args.get("code")),
            "state": _as_optional_string(args.get("state")),
            "error": _as_optional_string(args.get("error")),
            "error_description": _as_optional_string(args.get("error_description")),
        }
        result = self._complete_from_callback(callback, allow_missing_state=False)
        return CallbackResult(
            ok=result.ok,
            provider_id=GEMINI_API_PROVIDER_ID,
            account_label=result.account_label,
            account_id=result.account_id,
            error=result.error,
        )

    def _complete_from_callback(
        self,
        callback: dict[str, str | None] | None,
        *,
        allow_missing_state: bool,
    ) -> LoginPollResult:
        if not callback:
            return LoginPollResult(ok=False, provider_id=GEMINI_API_PROVIDER_ID, error="Missing OAuth callback.")
        if callback.get("error"):
            return LoginPollResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                error=str(callback.get("error_description") or callback.get("error")),
            )

        code = str(callback.get("code") or "").strip()
        if not code:
            return LoginPollResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                error="The OAuth callback did not include an authorization code.",
            )

        state = str(callback.get("state") or "").strip()
        attempt = None
        if state:
            attempt = get_attempt(state)
            if attempt is None:
                if latest_attempt(GEMINI_API_PROVIDER_ID) is not None:
                    return LoginPollResult(
                        ok=False,
                        provider_id=GEMINI_API_PROVIDER_ID,
                        error="OAuth state mismatch. Return to Agent Zero and start a new Google Gemini API connection.",
                    )
                return LoginPollResult(
                    ok=False,
                    provider_id=GEMINI_API_PROVIDER_ID,
                    expired=True,
                    error="OAuth sign-in expired. Return to Agent Zero and start a new Google Gemini API connection.",
                )
            if attempt.provider_id != GEMINI_API_PROVIDER_ID:
                return LoginPollResult(
                    ok=False,
                    provider_id=GEMINI_API_PROVIDER_ID,
                    error="OAuth state mismatch. Return to Agent Zero and start a new Google Gemini API connection.",
                )
        elif allow_missing_state:
            attempt = latest_attempt(GEMINI_API_PROVIDER_ID)
            if attempt is None:
                return LoginPollResult(
                    ok=False,
                    provider_id=GEMINI_API_PROVIDER_ID,
                    error="No active Google Gemini API sign-in attempt was found.",
                )
            state = attempt.state
        else:
            return LoginPollResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                error="The OAuth callback did not include state.",
            )

        token_endpoint = str(attempt.extra.get("token_endpoint") or GOOGLE_TOKEN_ENDPOINT)
        client_id = str(attempt.extra.get("client_id") or "")
        client_secret = str(attempt.extra.get("client_secret") or "")
        try:
            payload = self.exchange_code(
                token_endpoint,
                code,
                attempt.redirect_uri,
                attempt.verifier,
                client_id,
                client_secret,
            )
            auth = _auth_from_token_payload(
                payload,
                token_endpoint,
                client_id=client_id,
                client_secret=client_secret,
                quota_project_id=str(attempt.extra.get("quota_project_id") or ""),
                api_base_url=str(attempt.extra.get("api_base_url") or GEMINI_OPENAI_API_BASE),
            )
            self.write_auth(auth)
            pop_attempt(state)
        except Exception as exc:
            return LoginPollResult(
                ok=False,
                provider_id=GEMINI_API_PROVIDER_ID,
                error=str(exc),
            )

        label = _account_label(auth)
        return LoginPollResult(
            ok=True,
            provider_id=GEMINI_API_PROVIDER_ID,
            completed=True,
            account_label=label,
            account_id=label,
        )

    def ensure_fresh_auth(self) -> dict[str, Any]:
        auth = self.read_auth()
        refresh = str(auth.get("refresh") or "")
        if not refresh:
            return auth

        access = str(auth.get("access") or "")
        expires = _as_int(auth.get("expires"), 0)
        if access and expires and expires > int(time.time() * 1000) + REFRESH_MARGIN_MS:
            return auth

        token_endpoint = str(auth.get("token_endpoint") or GOOGLE_TOKEN_ENDPOINT)
        _validate_google_token_endpoint(token_endpoint)
        client_id = str(auth.get("client_id") or "")
        client_secret = str(auth.get("client_secret") or "")
        cfg = _gemini_api_config()
        if cfg.get("client_id"):
            client_id = str(cfg["client_id"])
        if cfg.get("client_secret"):
            client_secret = str(cfg["client_secret"])
        if not client_id:
            raise ProviderError(
                "Google Gemini API OAuth refresh requires the original OAuth client ID.",
                code="missing_oauth_client",
                status=401,
            )

        refreshed = self._refresh_tokens(token_endpoint, refresh, client_id, client_secret, auth)
        self.write_auth(refreshed)
        return refreshed

    def _refresh_tokens(
        self,
        token_endpoint: str,
        refresh: str,
        client_id: str,
        client_secret: str,
        existing: dict[str, Any],
    ) -> dict[str, Any]:
        import requests

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
        }
        if client_secret:
            data["client_secret"] = client_secret
        response = requests.post(
            token_endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=data,
            timeout=30,
        )
        payload = _json_payload(response)
        if not response.ok:
            raise ProviderError(
                _error_message(payload, f"Google Gemini API token refresh failed with status {response.status_code}."),
                code="token_refresh_failed",
                status=response.status_code,
            )
        _validate_token_payload(payload, require_refresh=False)
        merged = dict(existing)
        merged.update(
            _auth_from_token_payload(
                payload,
                token_endpoint,
                fallback_refresh=refresh,
                client_id=client_id,
                client_secret=client_secret,
                quota_project_id=str(existing.get("quota_project_id") or ""),
                api_base_url=str(existing.get("base_url") or GEMINI_OPENAI_API_BASE),
            )
        )
        if not payload.get("id_token") and existing.get("id_token"):
            merged["id_token"] = existing["id_token"]
        return merged

    def models(self) -> list[str]:
        if not self.read_auth():
            return list(CURATED_MODELS)
        try:
            auth = self.ensure_fresh_auth()
        except Exception:
            return list(CURATED_MODELS)
        access = str(auth.get("access") or "")
        if not access:
            return list(CURATED_MODELS)

        base_url = safe_api_base_url(auth.get("base_url"))
        try:
            import requests

            response = requests.get(
                f"{base_url}/models",
                headers=_gemini_headers(auth),
                timeout=30,
            )
            if not response.ok:
                return list(CURATED_MODELS)
            parsed = _models_from_payload(response.json())
            return parsed or list(CURATED_MODELS)
        except Exception:
            return list(CURATED_MODELS)

    def disconnect(self) -> dict[str, Any]:
        path = self.auth_path()
        existed = path.exists()
        try:
            path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass
        return {
            "disconnected": existed,
            "removed_auth_files": [str(path)] if existed else [],
        }

    def api_key(self) -> str:
        return DUMMY_API_KEY

    def register_routes(self, app: Any) -> None:
        from plugins._oauth.helpers import routes

        route_defs = [
            ("/oauth/gemini-api/health", "oauth_gemini_api_health", routes.gemini_api_health, ["GET"]),
            ("/oauth/gemini-api/callback", "oauth_gemini_api_callback", routes.gemini_api_callback, ["GET"]),
            (
                "/oauth/gemini-api/v1/models",
                "oauth_gemini_api_models",
                routes.gemini_api_models,
                ["GET", "OPTIONS"],
            ),
            (
                "/oauth/gemini-api/v1/chat/completions",
                "oauth_gemini_api_chat_completions",
                routes.gemini_api_chat_completions,
                ["POST", "OPTIONS"],
            ),
            (
                "/oauth/gemini-api/v1/responses",
                "oauth_gemini_api_responses",
                routes.gemini_api_responses,
                ["POST", "OPTIONS"],
            ),
        ]
        for rule, endpoint, view_func, methods in route_defs:
            if endpoint in app.view_functions:
                continue
            app.add_url_rule(rule, endpoint, view_func, methods=methods)


def _auth_from_token_payload(
    payload: dict[str, Any],
    token_endpoint: str,
    *,
    fallback_refresh: str = "",
    client_id: str = "",
    client_secret: str = "",
    quota_project_id: str = "",
    api_base_url: str = GEMINI_OPENAI_API_BASE,
) -> dict[str, Any]:
    return {
        "provider": GEMINI_API_PROVIDER_ID,
        "type": "oauth",
        "access": str(payload.get("access_token") or ""),
        "refresh": str(payload.get("refresh_token") or fallback_refresh or ""),
        "expires": _expires_ms(payload),
        "id_token": str(payload.get("id_token") or ""),
        "token_type": str(payload.get("token_type") or "Bearer"),
        "scope": str(payload.get("scope") or ""),
        "token_endpoint": token_endpoint,
        "base_url": safe_api_base_url(api_base_url),
        "client_id": client_id,
        "client_secret": client_secret,
        "quota_project_id": quota_project_id,
    }


def _validate_token_payload(payload: dict[str, Any], *, require_refresh: bool) -> None:
    if not isinstance(payload, dict):
        raise ProviderError("Google Gemini API token endpoint returned a malformed response.", code="token_malformed", status=502)
    missing = []
    if not str(payload.get("access_token") or ""):
        missing.append("access_token")
    if require_refresh and not str(payload.get("refresh_token") or ""):
        missing.append("refresh_token")
    if missing:
        raise ProviderError(
            f"Google Gemini API token response is missing: {', '.join(missing)}",
            code="token_malformed",
            status=502,
        )


def safe_api_base_url(value: Any) -> str:
    text = str(value or "").strip().rstrip("/")
    if not text:
        return GEMINI_OPENAI_API_BASE
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https" and host == "generativelanguage.googleapis.com":
        return text
    return GEMINI_OPENAI_API_BASE


def _gemini_headers(auth: dict[str, Any]) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Authorization": f'Bearer {str(auth.get("access") or "")}',
    }
    quota_project_id = str(auth.get("quota_project_id") or "").strip()
    if quota_project_id:
        headers["x-goog-user-project"] = quota_project_id
    return headers


def _client_config(data: dict[str, Any], cfg: dict[str, Any]) -> dict[str, str]:
    client_id = str(data.get("client_id") or cfg.get("client_id") or "").strip()
    client_secret = str(data.get("client_secret") or cfg.get("client_secret") or "").strip()
    quota_project_id = str(data.get("quota_project_id") or cfg.get("quota_project_id") or "").strip()
    if not client_id or not client_secret:
        raise ProviderError(
            "Configure a Google OAuth client ID and client secret before connecting Gemini API OAuth.",
            code="missing_oauth_client",
        )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "quota_project_id": quota_project_id,
    }


def _redirect_uri(request: Any, callback_path: str) -> str:
    origin = ""
    if request is not None:
        origin = (getattr(request, "headers", {}).get("Origin") or "").rstrip("/")
        if not _is_local_origin(origin):
            origin = getattr(request, "url_root", "").rstrip("/")
    return f"{origin}{callback_path}"


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


def _validate_google_token_endpoint(value: str) -> None:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host != "oauth2.googleapis.com":
        raise ProviderError(
            "Google Gemini API OAuth token endpoint is invalid.",
            code="invalid_token_endpoint",
            status=502,
        )


def _account_label(auth: dict[str, Any]) -> str:
    claims = _jwt_claims(str(auth.get("id_token") or ""))
    return str(claims.get("email") or auth.get("account_label") or "Google Gemini API")


def _jwt_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        parsed = json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _codex_helper():
    import importlib

    return importlib.import_module("plugins._oauth.helpers.codex")


def _gemini_api_config() -> dict[str, Any]:
    try:
        from plugins._oauth.helpers.config import gemini_api_config

        return gemini_api_config()
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("plugins._oauth"):
            raise
        return {
            "enabled": True,
            "client_id": "",
            "client_secret": "",
            "scopes": [
                "openid",
                "email",
                "profile",
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/generative-language.retriever",
            ],
            "quota_project_id": "",
            "api_base_url": GEMINI_OPENAI_API_BASE,
            "proxy_base_path": "/oauth/gemini-api",
            "callback_path": "/oauth/gemini-api/callback",
        }
