from __future__ import annotations

from typing import Any

from helpers import plugins


PLUGIN_NAME = "_oauth"

DEFAULT_CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CODEX_ISSUER = "https://auth.openai.com"
DEFAULT_CODEX_TOKEN_URL = "https://auth.openai.com/oauth/token"
DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_CODEX_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "api.connectors.read",
    "api.connectors.invoke",
]


def oauth_config() -> dict[str, Any]:
    value = plugins.get_plugin_config(PLUGIN_NAME) or {}
    return value if isinstance(value, dict) else {}


def codex_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    source = config if isinstance(config, dict) else oauth_config()
    raw = source.get("codex", {}) if isinstance(source, dict) else {}
    raw = raw if isinstance(raw, dict) else {}

    return {
        "enabled": _as_bool(raw.get("enabled"), True),
        "auth_file_path": _as_str(raw.get("auth_file_path")),
        "issuer": _trim_url(raw.get("issuer"), DEFAULT_CODEX_ISSUER),
        "token_url": _as_str(raw.get("token_url")) or DEFAULT_CODEX_TOKEN_URL,
        "client_id": _as_str(raw.get("client_id")) or DEFAULT_CODEX_CLIENT_ID,
        "scopes": _as_str_list(raw.get("scopes")) or DEFAULT_CODEX_SCOPES,
        "open_browser_from_server": _as_bool(raw.get("open_browser_from_server"), False),
        "forced_workspace_id": _as_str(raw.get("forced_workspace_id")),
        "upstream_base_url": _trim_url(raw.get("upstream_base_url"), DEFAULT_CODEX_BASE_URL),
        "codex_version": _as_str(raw.get("codex_version")),
        "models": _as_str_list(raw.get("models")),
        "request_timeout_seconds": _as_int(raw.get("request_timeout_seconds"), 120),
        "proxy_base_path": _normalize_base_path(raw.get("proxy_base_path"), "/oauth/codex"),
        "callback_path": _normalize_base_path(raw.get("callback_path"), "/auth/callback"),
        "require_proxy_token": _as_bool(raw.get("require_proxy_token"), False),
        "proxy_token": _as_str(raw.get("proxy_token")),
    }


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace(",", "\n").splitlines()
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]

    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _as_str(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _trim_url(value: Any, default: str) -> str:
    text = _as_str(value) or default
    return text.rstrip("/")


def _normalize_base_path(value: Any, default: str) -> str:
    text = _as_str(value) or default
    if not text.startswith("/"):
        text = "/" + text
    return text.rstrip("/") or default
