from __future__ import annotations

import secrets
import time
import importlib
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from plugins._oauth.helpers.providers.base import (
    DUMMY_API_KEY,
    XAI_GROK_PROVIDER_ID,
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


XAI_ISSUER = "https://auth.x.ai"
XAI_DISCOVERY_URL = f"{XAI_ISSUER}/.well-known/openid-configuration"
XAI_CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
XAI_SCOPE = "openid profile email offline_access grok-cli:access api:access"
XAI_REDIRECT_URI = "http://127.0.0.1:56121/callback"
XAI_API_BASE = "https://api.x.ai/v1"
CURATED_MODELS = [
    "grok-4.3",
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-multi-agent-0309",
    "grok-code-fast-1",
]
NOT_CONNECTED_MESSAGE = "xAI Grok OAuth is not connected yet."
OAUTH_TIER_WARNING = (
    "xAI Grok OAuth API access may be restricted by tier. "
    "If OAuth token exchange is denied, the separate API-key `xai` provider may work."
)
REFRESH_MARGIN_MS = 60_000


class XaiGrokOAuthProvider:
    provider_id = XAI_GROK_PROVIDER_ID

    def auth_path(self) -> Path:
        return provider_auth_path("xai_grok")

    def read_auth(self) -> dict[str, Any]:
        return read_json_file(self.auth_path())

    def write_auth(self, data: dict[str, Any]) -> None:
        write_private_json(self.auth_path(), data)

    def discovery(self) -> dict[str, str]:
        import requests

        response = requests.get(
            XAI_DISCOVERY_URL,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        payload = _json_payload(response)
        if not response.ok:
            raise ProviderError(
                _error_message(payload, f"xAI Grok discovery failed with status {response.status_code}."),
                code="discovery_failed",
                status=response.status_code,
            )
        authorization_endpoint = str(payload.get("authorization_endpoint") or "").strip()
        token_endpoint = str(payload.get("token_endpoint") or "").strip()
        if not authorization_endpoint or not token_endpoint:
            raise ProviderError(
                "xAI Grok discovery response was missing OAuth endpoints.",
                code="discovery_malformed",
                status=502,
            )
        _validate_xai_endpoint(authorization_endpoint)
        _validate_xai_endpoint(token_endpoint)
        return {
            "authorization_endpoint": authorization_endpoint,
            "token_endpoint": token_endpoint,
        }

    def metadata(self) -> OAuthProviderMetadata:
        return OAuthProviderMetadata(
            provider_id=XAI_GROK_PROVIDER_ID,
            display_name="xAI Grok",
            short_name="Grok",
            model_provider_id=XAI_GROK_PROVIDER_ID,
            icon="xai",
            auth_flow="browser_pkce",
            default_model="grok-4.3",
            default_models=list(CURATED_MODELS),
            proxy_base_path="/oauth/xai-grok",
            callback_path="/oauth/xai-grok/callback",
            supports_manual_callback=True,
            warning=OAUTH_TIER_WARNING,
        )

    def status(self) -> dict[str, Any]:
        auth = self.read_auth()
        access = str(auth.get("access") or "")
        refresh = str(auth.get("refresh") or "")
        result = {
            **self.metadata().to_dict(),
            "connected": bool(access and refresh),
            "account_label": "xAI Grok" if access or refresh else "",
            "base_url": str(auth.get("base_url") or XAI_API_BASE),
            "auth_file_path": str(self.auth_path()),
        }
        warning = str(auth.get("warning") or "")
        if warning:
            result["warning"] = warning
        elif access and refresh and _as_int(auth.get("expires"), 0) <= int(time.time() * 1000):
            result["warning"] = "xAI Grok OAuth access token is expired and will be refreshed on the next request."
        return result

    def start_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginStartResult:
        del input, request
        try:
            codex = importlib.import_module("plugins._oauth.helpers.codex")
            metadata = self.discovery()
            pkce = codex.generate_pkce()
            state = codex.generate_state()
            nonce = secrets.token_urlsafe(24)
            attempt = put_attempt(
                state,
                pkce.verifier,
                XAI_REDIRECT_URI,
                provider_id=XAI_GROK_PROVIDER_ID,
                extra={
                    "nonce": nonce,
                    "code_challenge": pkce.challenge,
                    "token_endpoint": metadata["token_endpoint"],
                },
            )
            query = {
                "response_type": "code",
                "client_id": XAI_CLIENT_ID,
                "redirect_uri": XAI_REDIRECT_URI,
                "scope": XAI_SCOPE,
                "code_challenge": pkce.challenge,
                "code_challenge_method": "S256",
                "state": state,
                "nonce": nonce,
                "plan": "generic",
                "referrer": "agent-zero",
            }
            auth_url = f'{metadata["authorization_endpoint"]}?{urlencode(query)}'
        except Exception as exc:
            return LoginStartResult(
                ok=False,
                provider_id=XAI_GROK_PROVIDER_ID,
                flow="browser_pkce",
                error=str(exc),
                message=str(exc),
            )

        return LoginStartResult(
            ok=True,
            provider_id=XAI_GROK_PROVIDER_ID,
            flow="browser_pkce",
            auth_url=auth_url,
            redirect_uri=XAI_REDIRECT_URI,
            expires_at=attempt.expires_at,
        )

    def poll_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginPollResult:
        del input, request
        return LoginPollResult(
            ok=False,
            provider_id=XAI_GROK_PROVIDER_ID,
            error="xAI Grok uses browser callback login.",
        )

    def exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
        code_challenge: str,
    ) -> dict[str, Any]:
        import requests

        response = requests.post(
            token_endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": XAI_CLIENT_ID,
                "code_verifier": code_verifier,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            },
            timeout=30,
        )
        payload = _json_payload(response)
        if not response.ok:
            if response.status_code == 403:
                raise ProviderError(
                    OAUTH_TIER_WARNING,
                    code="oauth_tier_restricted",
                    status=403,
                )
            raise ProviderError(
                _error_message(payload, f"xAI Grok token exchange failed with status {response.status_code}."),
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
            provider_id=XAI_GROK_PROVIDER_ID,
            account_label=result.account_label,
            error=result.error,
        )

    def _complete_from_callback(
        self,
        callback: dict[str, str | None] | None,
        *,
        allow_missing_state: bool,
    ) -> LoginPollResult:
        if not callback:
            return LoginPollResult(ok=False, provider_id=XAI_GROK_PROVIDER_ID, error="Missing OAuth callback.")
        if callback.get("error"):
            return LoginPollResult(
                ok=False,
                provider_id=XAI_GROK_PROVIDER_ID,
                error=str(callback.get("error_description") or callback.get("error")),
            )

        code = str(callback.get("code") or "").strip()
        if not code:
            return LoginPollResult(
                ok=False,
                provider_id=XAI_GROK_PROVIDER_ID,
                error="The OAuth callback did not include an authorization code.",
            )

        state = str(callback.get("state") or "").strip()
        attempt = None
        if state:
            attempt = get_attempt(state)
            if attempt is None:
                if latest_attempt(XAI_GROK_PROVIDER_ID) is not None:
                    return LoginPollResult(
                        ok=False,
                        provider_id=XAI_GROK_PROVIDER_ID,
                        error="OAuth state mismatch. Return to Agent Zero and start a new xAI Grok connection.",
                    )
                return LoginPollResult(
                    ok=False,
                    provider_id=XAI_GROK_PROVIDER_ID,
                    expired=True,
                    error="OAuth sign-in expired. Return to Agent Zero and start a new xAI Grok connection.",
                )
            if attempt.provider_id != XAI_GROK_PROVIDER_ID:
                return LoginPollResult(
                    ok=False,
                    provider_id=XAI_GROK_PROVIDER_ID,
                    error="OAuth state mismatch. Return to Agent Zero and start a new xAI Grok connection.",
                )
        elif allow_missing_state:
            attempt = latest_attempt(XAI_GROK_PROVIDER_ID)
            if attempt is None:
                return LoginPollResult(
                    ok=False,
                    provider_id=XAI_GROK_PROVIDER_ID,
                    error="No active xAI Grok sign-in attempt was found.",
                )
            state = attempt.state
        else:
            return LoginPollResult(
                ok=False,
                provider_id=XAI_GROK_PROVIDER_ID,
                error="The OAuth callback did not include state.",
            )

        token_endpoint = str(attempt.extra.get("token_endpoint") or "")
        if not token_endpoint:
            token_endpoint = self.discovery()["token_endpoint"]
        code_challenge = str(attempt.extra.get("code_challenge") or "")
        try:
            payload = self.exchange_code(
                token_endpoint,
                code,
                attempt.redirect_uri,
                attempt.verifier,
                code_challenge,
            )
            auth = _auth_from_token_payload(payload, token_endpoint)
            self.write_auth(auth)
            pop_attempt(state)
        except Exception as exc:
            return LoginPollResult(
                ok=False,
                provider_id=XAI_GROK_PROVIDER_ID,
                error=str(exc),
            )

        return LoginPollResult(
            ok=True,
            provider_id=XAI_GROK_PROVIDER_ID,
            completed=True,
            account_label="xAI Grok",
        )

    def ensure_fresh_auth(self) -> dict[str, Any]:
        auth = self.read_auth()
        access = str(auth.get("access") or "")
        refresh = str(auth.get("refresh") or "")
        if not access or not refresh:
            return auth

        expires = _as_int(auth.get("expires"), 0)
        if expires and expires > int(time.time() * 1000) + REFRESH_MARGIN_MS:
            return auth

        token_endpoint = str(auth.get("token_endpoint") or "")
        if not token_endpoint:
            token_endpoint = self.discovery()["token_endpoint"]
        _validate_xai_endpoint(token_endpoint, code="invalid_token_endpoint")
        try:
            refreshed = self._refresh_tokens(token_endpoint, refresh, auth)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(
                f"xAI Grok OAuth refresh failed: {exc}",
                code="auth_refresh_failed",
                status=401,
            ) from exc
        self.write_auth(refreshed)
        return refreshed

    def _refresh_tokens(self, token_endpoint: str, refresh: str, existing: dict[str, Any]) -> dict[str, Any]:
        import requests

        response = requests.post(
            token_endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": XAI_CLIENT_ID,
            },
            timeout=30,
        )
        payload = _json_payload(response)
        if not response.ok:
            if response.status_code == 403:
                raise ProviderError(
                    OAUTH_TIER_WARNING,
                    code="oauth_tier_restricted",
                    status=403,
                )
            raise ProviderError(
                _error_message(payload, f"xAI Grok token refresh failed with status {response.status_code}."),
                code="token_refresh_failed",
                status=response.status_code,
            )
        _validate_token_payload(payload, require_refresh=False)
        merged = dict(existing)
        merged.update(_auth_from_token_payload(payload, token_endpoint, fallback_refresh=refresh))
        if not payload.get("id_token") and existing.get("id_token"):
            merged["id_token"] = existing["id_token"]
        if not payload.get("token_type") and existing.get("token_type"):
            merged["token_type"] = existing["token_type"]
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
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access}",
                },
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
            ("/oauth/xai-grok/health", "oauth_xai_grok_health", routes.xai_grok_health, ["GET"]),
            ("/oauth/xai-grok/callback", "oauth_xai_grok_callback", routes.xai_grok_callback, ["GET"]),
            (
                "/oauth/xai-grok/v1/models",
                "oauth_xai_grok_models",
                routes.xai_grok_models,
                ["GET", "OPTIONS"],
            ),
            (
                "/oauth/xai-grok/v1/chat/completions",
                "oauth_xai_grok_chat_completions",
                routes.xai_grok_chat_completions,
                ["POST", "OPTIONS"],
            ),
            (
                "/oauth/xai-grok/v1/responses",
                "oauth_xai_grok_responses",
                routes.xai_grok_responses,
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
) -> dict[str, Any]:
    return {
        "provider": XAI_GROK_PROVIDER_ID,
        "type": "oauth",
        "access": str(payload.get("access_token") or ""),
        "refresh": str(payload.get("refresh_token") or fallback_refresh or ""),
        "expires": _expires_ms(payload),
        "id_token": str(payload.get("id_token") or ""),
        "token_type": str(payload.get("token_type") or "Bearer"),
        "token_endpoint": token_endpoint,
        "base_url": XAI_API_BASE,
    }


def _validate_token_payload(payload: dict[str, Any], *, require_refresh: bool) -> None:
    if not isinstance(payload, dict):
        raise ProviderError("xAI Grok token endpoint returned a malformed response.", code="token_malformed", status=502)
    missing = []
    if not str(payload.get("access_token") or ""):
        missing.append("access_token")
    if require_refresh and not str(payload.get("refresh_token") or ""):
        missing.append("refresh_token")
    if missing:
        raise ProviderError(
            f"xAI Grok token response is missing: {', '.join(missing)}",
            code="token_malformed",
            status=502,
        )


def safe_api_base_url(value: Any) -> str:
    text = str(value or "").strip().rstrip("/")
    if not text:
        return XAI_API_BASE
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https" and (host == "api.x.ai" or host.endswith(".api.x.ai")):
        return text
    return XAI_API_BASE


def _validate_xai_endpoint(value: str, *, code: str = "discovery_invalid_endpoint") -> None:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "x.ai" or host.endswith(".x.ai")):
        raise ProviderError(
            "xAI Grok discovery returned an invalid OAuth endpoint.",
            code=code,
            status=502,
        )
