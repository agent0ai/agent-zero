from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from plugins._oauth.helpers.providers.base import (
    DUMMY_API_KEY,
    GITHUB_COPILOT_PROVIDER_ID,
    CallbackResult,
    LoginPollResult,
    LoginStartResult,
    OAuthProviderMetadata,
    ProviderError,
    provider_auth_path,
    read_json_file,
    write_private_json,
)
from plugins._oauth.helpers.state import (
    DeviceAttempt,
    get_device_attempt,
    pop_device_attempt,
    put_device_attempt,
)


CLIENT_ID = "Iv1.b507a08c87ecfe98"
DEFAULT_DOMAIN = "github.com"
COPILOT_HEADERS = {
    "User-Agent": "GitHubCopilotChat/0.35.0",
    "Editor-Version": "vscode/1.107.0",
    "Editor-Plugin-Version": "copilot-chat/0.35.0",
    "Copilot-Integration-Id": "vscode-chat",
}
CURATED_MODELS = [
    "gpt-5.2",
    "claude-sonnet-4.5",
    "claude-opus-4.5",
    "gemini-2.5-pro",
    "grok-code-fast-1",
    "gpt-4.1",
    "gpt-4o",
]
NOT_CONNECTED_MESSAGE = "GitHub Copilot OAuth is not connected yet."
ENTERPRISE_NOTE = "Leave Enterprise domain blank for github.com, or enter a GitHub Enterprise domain."
DEFAULT_COPILOT_BASE_URL = "https://api.individual.githubcopilot.com"
DEFAULT_COPILOT_HOST = "api.individual.githubcopilot.com"
GITHUB_COPILOT_API_HOSTS = {
    DEFAULT_COPILOT_HOST,
    "api.githubcopilot.com",
}
REFRESH_MARGIN_MS = 60_000


def normalize_enterprise_domain(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return DEFAULT_DOMAIN
    if any(char.isspace() for char in text):
        raise ValueError("Invalid GitHub Enterprise URL/domain.")

    parsed = urlparse(text if "://" in text else f"//{text}")
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid GitHub Enterprise URL/domain.")
    if "@" in parsed.netloc:
        raise ValueError("Invalid GitHub Enterprise URL/domain.")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host or "/" in host or "\\" in host:
        raise ValueError("Invalid GitHub Enterprise URL/domain.")
    if host.startswith("-") or host.endswith("-") or ".." in host:
        raise ValueError("Invalid GitHub Enterprise URL/domain.")
    return host


def github_urls(domain: Any) -> dict[str, str]:
    normalized = normalize_enterprise_domain(domain)
    web_base = f"https://{normalized}"
    if normalized == DEFAULT_DOMAIN:
        copilot_token = "https://api.github.com/copilot_internal/v2/token"
    else:
        copilot_token = f"https://{normalized}/api/v3/copilot_internal/v2/token"
    return {
        "device_code": f"{web_base}/login/device/code",
        "access_token": f"{web_base}/login/oauth/access_token",
        "copilot_token": copilot_token,
    }


def copilot_base_url_from_token(token: str, enterprise_domain: Any = "") -> str:
    domain = normalize_enterprise_domain(enterprise_domain)
    for part in str(token or "").split(";"):
        key, separator, value = part.partition("=")
        if separator and key.strip() == "proxy-ep":
            try:
                return safe_copilot_base_url_from_proxy_endpoint(value, domain)
            except ProviderError:
                return DEFAULT_COPILOT_BASE_URL
    if domain != DEFAULT_DOMAIN:
        return f"https://copilot-api.{domain}"
    return DEFAULT_COPILOT_BASE_URL


def safe_copilot_base_url(value: Any, enterprise_domain: Any = "") -> str:
    text = str(value or "").strip().rstrip("/")
    domain = normalize_enterprise_domain(enterprise_domain)
    if not text:
        return _default_copilot_base_url_for_domain(domain)

    parsed = urlparse(text)
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if parsed.scheme == "https" and _is_allowed_copilot_api_host(host, domain):
        return f"https://{host}"
    return _default_copilot_base_url_for_domain(domain)


def safe_copilot_base_url_from_proxy_endpoint(value: Any, enterprise_domain: Any = "") -> str:
    text = str(value or "").strip()
    if not text:
        raise ProviderError("GitHub Copilot token returned an invalid proxy endpoint.", code="invalid_proxy_endpoint", status=502)

    parsed = urlparse(text if "://" in text else f"//{text}")
    if parsed.scheme and parsed.scheme != "https":
        raise ProviderError("GitHub Copilot token returned an invalid proxy endpoint.", code="invalid_proxy_endpoint", status=502)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProviderError(
            "GitHub Copilot token returned an invalid proxy endpoint.",
            code="invalid_proxy_endpoint",
            status=502,
        ) from exc
    if parsed.username or parsed.password or port is not None:
        raise ProviderError("GitHub Copilot token returned an invalid proxy endpoint.", code="invalid_proxy_endpoint", status=502)
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ProviderError("GitHub Copilot token returned an invalid proxy endpoint.", code="invalid_proxy_endpoint", status=502)

    domain = normalize_enterprise_domain(enterprise_domain)
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if host.startswith("proxy."):
        host = f"api.{host.removeprefix('proxy.')}"
    if not _is_allowed_proxy_endpoint_host(host, domain):
        raise ProviderError("GitHub Copilot token returned an invalid proxy endpoint.", code="invalid_proxy_endpoint", status=502)
    return f"https://{host}"


def _default_copilot_base_url_for_domain(domain: str) -> str:
    if domain != DEFAULT_DOMAIN:
        return f"https://copilot-api.{domain}"
    return DEFAULT_COPILOT_BASE_URL


def _is_allowed_copilot_api_host(host: str, enterprise_domain: str) -> bool:
    if host in GITHUB_COPILOT_API_HOSTS:
        return True
    return enterprise_domain != DEFAULT_DOMAIN and host == f"copilot-api.{enterprise_domain}"


def _is_allowed_proxy_endpoint_host(host: str, enterprise_domain: str) -> bool:
    if host.endswith(".githubcopilot.com"):
        return True
    return enterprise_domain != DEFAULT_DOMAIN and host == f"copilot-api.{enterprise_domain}"


class GitHubCopilotOAuthProvider:
    provider_id = GITHUB_COPILOT_PROVIDER_ID

    def auth_path(self) -> Path:
        return provider_auth_path("github_copilot")

    def read_auth(self) -> dict[str, Any]:
        return read_json_file(self.auth_path())

    def write_auth(self, data: dict[str, Any]) -> None:
        write_private_json(self.auth_path(), data)

    def ensure_fresh_auth(self) -> dict[str, Any]:
        auth = self.read_auth()
        refresh = str(auth.get("refresh") or "")
        access = str(auth.get("access") or "")
        if not refresh or not access:
            return auth

        expires = _as_int(auth.get("expires"), 0)
        if not expires or expires > int(time.time() * 1000) + REFRESH_MARGIN_MS:
            return auth

        domain = auth.get("enterprise_domain") or DEFAULT_DOMAIN
        refreshed = refresh_copilot_token(refresh, domain)
        if auth.get("models_warning") and not refreshed.get("models_warning"):
            refreshed["models_warning"] = auth["models_warning"]
        self.write_auth(refreshed)
        return refreshed

    def metadata(self) -> OAuthProviderMetadata:
        return OAuthProviderMetadata(
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            display_name="GitHub Copilot",
            short_name="GitHub Copilot",
            model_provider_id=GITHUB_COPILOT_PROVIDER_ID,
            icon="github",
            auth_flow="device_code",
            default_model=CURATED_MODELS[0],
            default_models=list(CURATED_MODELS),
            proxy_base_path="/oauth/github-copilot",
            supports_enterprise_domain=True,
            note=ENTERPRISE_NOTE,
        )

    def status(self) -> dict[str, Any]:
        auth = self.read_auth()
        access = str(auth.get("access") or "")
        refresh = str(auth.get("refresh") or "")
        enterprise_domain = str(auth.get("enterprise_domain") or "")
        domain = enterprise_domain or DEFAULT_DOMAIN
        result = {
            **self.metadata().to_dict(),
            "connected": bool(access and refresh),
            "account_label": domain,
            "enterprise_domain": enterprise_domain,
            "base_url": str(auth.get("base_url") or ""),
            "auth_file_path": str(self.auth_path()),
        }
        if auth.get("models_warning"):
            result["models_warning"] = str(auth["models_warning"])
        return result

    def start_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginStartResult:
        del request
        data = input or {}
        try:
            domain = normalize_enterprise_domain(data.get("enterprise_domain", ""))
            device = _post_device_code(domain)
            device_code = str(device.get("device_code") or "")
            user_code = str(device.get("user_code") or "")
            verification_url = str(
                device.get("verification_uri")
                or device.get("verification_url")
                or "https://github.com/login/device"
            )
            if not device_code or not user_code:
                raise RuntimeError("GitHub device-code response was malformed.")
            interval = _as_positive_int(device.get("interval"), 5)
            expires_in = _as_positive_int(device.get("expires_in"), 900)
            attempt = put_device_attempt(
                secrets.token_urlsafe(24),
                device_code,
                user_code,
                interval,
                time.time() + expires_in,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                extra={"domain": domain},
            )
        except Exception as exc:
            message = str(exc)
            return LoginStartResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                flow="device_code",
                message=message,
                error=message,
            )

        return LoginStartResult(
            ok=True,
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            flow="device_code",
            attempt_id=attempt.attempt_id,
            verification_url=verification_url,
            user_code=attempt.user_code,
            interval=attempt.interval,
            expires_at=attempt.expires_at,
        )

    def poll_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginPollResult:
        del request
        data = input or {}
        attempt_id = str(data.get("attempt_id") or "").strip()
        if not attempt_id:
            return LoginPollResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                error="Missing device authorization attempt.",
            )

        attempt = get_device_attempt(attempt_id)
        if attempt is None:
            return LoginPollResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                expired=True,
                error="Device authorization expired.",
            )
        if attempt.provider_id != GITHUB_COPILOT_PROVIDER_ID:
            return LoginPollResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                error="Device authorization provider mismatch.",
            )

        domain = normalize_enterprise_domain(attempt.extra.get("domain", ""))
        try:
            payload = _post_device_poll(domain, attempt.device_auth_id)
        except Exception as exc:
            return LoginPollResult(ok=False, provider_id=GITHUB_COPILOT_PROVIDER_ID, error=str(exc))

        error = str(payload.get("error") or "")
        if error == "authorization_pending":
            return LoginPollResult(
                ok=True,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                completed=False,
                interval=attempt.interval,
                expires_at=attempt.expires_at,
            )
        if error == "slow_down":
            interval = attempt.interval + 5
            put_device_attempt(
                attempt.attempt_id,
                attempt.device_auth_id,
                attempt.user_code,
                interval,
                attempt.expires_at,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                extra=attempt.extra,
            )
            return LoginPollResult(
                ok=True,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                completed=False,
                interval=interval,
                expires_at=attempt.expires_at,
            )
        if error in {"expired_token", "access_denied"}:
            pop_device_attempt(attempt_id)
            return LoginPollResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                expired=error == "expired_token",
                error=error,
            )
        if error:
            return LoginPollResult(ok=False, provider_id=GITHUB_COPILOT_PROVIDER_ID, error=error)

        github_access_token = str(payload.get("access_token") or "")
        if not github_access_token:
            return LoginPollResult(
                ok=False,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                error="GitHub device poll response was malformed.",
            )

        try:
            auth = refresh_copilot_token(github_access_token, domain)
        except Exception as exc:
            return LoginPollResult(ok=False, provider_id=GITHUB_COPILOT_PROVIDER_ID, error=str(exc))

        warning = ""
        try:
            summary = enable_known_models(auth["access"], domain)
            if summary.get("failed"):
                auth["models_warning"] = "Some Copilot models could not be enabled."
                warning = auth["models_warning"]
        except Exception as exc:
            auth["models_warning"] = str(exc)
            warning = str(exc)

        self.write_auth(auth)
        pop_device_attempt(attempt_id)
        return LoginPollResult(
            ok=True,
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            completed=True,
            account_label=domain,
            warning=warning,
        )

    def complete_callback(
        self,
        args: dict[str, Any],
        request: Any = None,
    ) -> CallbackResult:
        del args, request
        return CallbackResult(
            ok=False,
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            error="GitHub Copilot uses device-code login.",
        )

    def manual_callback(
        self,
        input: dict[str, Any],
        request: Any = None,
    ) -> LoginPollResult:
        del input, request
        return LoginPollResult(
            ok=False,
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            error="GitHub Copilot uses device-code login.",
        )

    def models(self) -> list[str]:
        try:
            auth = self.ensure_fresh_auth()
        except Exception:
            return list(CURATED_MODELS)
        access = str(auth.get("access") or "")
        if not access:
            return list(CURATED_MODELS)

        try:
            import requests

            base_url = safe_copilot_base_url(auth.get("base_url"), auth.get("enterprise_domain"))
            response = requests.get(
                f"{base_url}/models",
                headers={
                    **COPILOT_HEADERS,
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
            ("/oauth/github-copilot/health", "oauth_github_copilot_health", routes.github_copilot_health, ["GET"]),
            (
                "/oauth/github-copilot/v1/models",
                "oauth_github_copilot_models",
                routes.github_copilot_models,
                ["GET", "OPTIONS"],
            ),
            (
                "/oauth/github-copilot/v1/chat/completions",
                "oauth_github_copilot_chat_completions",
                routes.github_copilot_chat_completions,
                ["POST", "OPTIONS"],
            ),
            (
                "/oauth/github-copilot/v1/responses",
                "oauth_github_copilot_responses",
                routes.github_copilot_responses,
                ["POST", "OPTIONS"],
            ),
        ]
        for rule, endpoint, view_func, methods in route_defs:
            if endpoint in app.view_functions:
                continue
            app.add_url_rule(rule, endpoint, view_func, methods=methods)

    def _store_device_attempt_for_test(
        self,
        domain: str,
        device_code: str,
        user_code: str,
        interval: int,
    ) -> DeviceAttempt:
        return put_device_attempt(
            secrets.token_urlsafe(24),
            device_code,
            user_code,
            interval,
            time.time() + 900,
            provider_id=GITHUB_COPILOT_PROVIDER_ID,
            extra={"domain": normalize_enterprise_domain(domain)},
        )


def refresh_copilot_token(refresh: str, domain: Any) -> dict[str, Any]:
    normalized = normalize_enterprise_domain(domain)
    import requests

    response = requests.get(
        github_urls(normalized)["copilot_token"],
        headers={
            **COPILOT_HEADERS,
            "Accept": "application/json",
            "Authorization": f"Bearer {refresh}",
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"GitHub Copilot token refresh failed with status {response.status_code}.")

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub Copilot token response was malformed.")
    token = str(payload.get("token") or payload.get("access_token") or "")
    expires_at = _expires_ms(payload)
    if not token or not expires_at:
        raise RuntimeError("GitHub Copilot token response was missing token data.")

    return {
        "provider": GITHUB_COPILOT_PROVIDER_ID,
        "type": "oauth",
        "refresh": refresh,
        "access": token,
        "expires": max(0, expires_at - 300_000),
        "enterprise_domain": "" if normalized == DEFAULT_DOMAIN else normalized,
        "base_url": copilot_base_url_from_token(token, normalized),
    }


def enable_known_models(token: str, domain: Any) -> dict[str, Any]:
    base_url = copilot_base_url_from_token(token, domain).rstrip("/")
    summary: dict[str, Any] = {"attempted": len(CURATED_MODELS), "enabled": 0, "failed": []}
    try:
        import requests
    except Exception as exc:
        summary["failed"] = [{"model": model, "error": str(exc)} for model in CURATED_MODELS]
        return summary

    for model in CURATED_MODELS:
        try:
            response = requests.post(
                f"{base_url}/models/{model}/policy",
                headers={
                    **COPILOT_HEADERS,
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"state": "enabled"},
                timeout=30,
            )
            if response.ok:
                summary["enabled"] += 1
            else:
                summary["failed"].append({"model": model, "status": response.status_code})
        except Exception as exc:
            summary["failed"].append({"model": model, "error": str(exc)})
    return summary


def _post_device_code(domain: str) -> dict[str, Any]:
    import requests

    response = requests.post(
        github_urls(domain)["device_code"],
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": COPILOT_HEADERS["User-Agent"],
        },
        data={"client_id": CLIENT_ID, "scope": "read:user"},
        timeout=30,
    )
    payload = _json_payload(response)
    if not response.ok:
        raise RuntimeError(str(payload.get("error_description") or payload.get("error") or "GitHub device-code request failed."))
    return payload


def _post_device_poll(domain: str, device_code: str) -> dict[str, Any]:
    import requests

    response = requests.post(
        github_urls(domain)["access_token"],
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": COPILOT_HEADERS["User-Agent"],
        },
        data={
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
        timeout=30,
    )
    payload = _json_payload(response)
    if response.ok or payload.get("error"):
        return payload
    raise RuntimeError("GitHub device poll request failed.")


def _json_payload(response: Any) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _models_from_payload(payload: Any) -> list[str]:
    values: list[Any]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        values = payload["data"]
    elif isinstance(payload, dict) and isinstance(payload.get("models"), list):
        values = payload["models"]
    elif isinstance(payload, list):
        values = payload
    else:
        return []

    models: list[str] = []
    seen: set[str] = set()
    for value in values:
        model_id = ""
        if isinstance(value, str):
            model_id = value
        elif isinstance(value, dict):
            model_id = str(value.get("id") or value.get("name") or "")
        model_id = model_id.strip()
        if model_id and model_id not in seen:
            seen.add(model_id)
            models.append(model_id)
    return models


def _expires_ms(payload: dict[str, Any]) -> int:
    raw = payload.get("expires_at")
    if raw is None and payload.get("expires_in") is not None:
        return int((time.time() + float(payload["expires_in"])) * 1000)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0
    if value < 1_000_000_000_000:
        value *= 1000
    return int(value)


def _as_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
