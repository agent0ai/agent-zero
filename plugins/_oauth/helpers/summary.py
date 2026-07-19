from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from plugins._oauth.helpers.providers import CODEX_PROVIDER_ID
from plugins._oauth.helpers.usage_plans import usage_plan_catalog


ProviderRegistryFactory = Callable[[], Mapping[str, Any]]
RoutesInstalledFactory = Callable[[], bool]


def build_oauth_status_summary(
    *,
    provider_registry: ProviderRegistryFactory,
    routes_installed: RoutesInstalledFactory,
) -> dict[str, Any]:
    """Return the shared OAuth account status payload for APIs and discovery cards."""

    providers = [_provider_status(provider) for provider in provider_registry().values()]
    provider_map = {
        provider["provider_id"]: provider
        for provider in providers
        if provider.get("provider_id")
    }
    connected = [provider for provider in providers if provider.get("connected")]
    available = [provider for provider in providers if not provider.get("connected")]
    catalog = usage_plan_catalog()

    return {
        "ok": True,
        "routes_installed": routes_installed(),
        "providers": providers,
        "provider_map": provider_map,
        "usage_plan_catalog": catalog,
        "connected_count": len(connected),
        "available_count": len(available),
        "oauth_accounts": {
            "connected_count": len(connected),
            "available_count": len(available),
            "total_count": len(providers),
            "connected": [_account_summary(provider, catalog) for provider in connected],
            "available": [_account_summary(provider, catalog) for provider in available],
        },
        "codex": provider_map.get(CODEX_PROVIDER_ID, {}),
    }


def _provider_status(provider: Any) -> dict[str, Any]:
    try:
        status = provider.status()
        if not isinstance(status, dict):
            status = {}
        provider_id = str(status.get("provider_id") or getattr(provider, "provider_id", ""))
        status = {
            **status,
            "provider_id": provider_id,
            "connected": bool(status.get("connected")),
        }
        usage_windows = _usage_windows(status)
        if usage_windows:
            status["usage_windows"] = usage_windows
        return status
    except Exception as exc:
        metadata = _provider_metadata(provider)
        return {
            **metadata,
            "provider_id": str(getattr(provider, "provider_id", "")),
            "connected": False,
            "error": str(exc),
        }


def _provider_metadata(provider: Any) -> dict[str, Any]:
    try:
        metadata = provider.metadata()
        to_dict = getattr(metadata, "to_dict", None)
        value = to_dict() if callable(to_dict) else metadata
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _account_summary(provider: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    provider_id = str(provider.get("provider_id") or "")
    plan_entry = catalog.get(provider_id) if isinstance(catalog, dict) else None
    plans = plan_entry.get("plans", []) if isinstance(plan_entry, dict) else []
    return {
        "provider_id": provider_id,
        "display_name": provider.get("display_name") or provider_id,
        "short_name": provider.get("short_name") or provider.get("display_name") or provider_id,
        "connected": bool(provider.get("connected")),
        "account_label": provider.get("account_label") or provider.get("email") or "",
        "auth_flow": provider.get("auth_flow") or "",
        "icon": provider.get("icon") or "",
        "warning": provider.get("warning") or provider.get("models_warning") or "",
        "usage_windows": list(provider.get("usage_windows") or []),
        "plan_count": len(plans) if isinstance(plans, list) else 0,
    }


def _usage_windows(status: dict[str, Any]) -> list[dict[str, Any]]:
    usage = status.get("usage") if isinstance(status, dict) else {}
    if not isinstance(usage, dict) or not usage.get("available"):
        return []

    windows: list[dict[str, Any]] = []
    for key, title in (("primary", "Session"), ("secondary", "Week")):
        window = usage.get(key)
        if not isinstance(window, dict):
            continue
        remaining = _remaining_percent(window)
        if remaining is None:
            continue
        windows.append({
            "key": key,
            "title": title,
            "label": window.get("label") or "",
            "remaining_percent": remaining,
            "reset_at": window.get("reset_at") or 0,
        })
    return windows


def _remaining_percent(window: dict[str, Any]) -> float | None:
    remaining = window.get("remaining_percent")
    if remaining is not None:
        try:
            return max(0, min(100, float(remaining)))
        except (TypeError, ValueError):
            pass

    used = window.get("used_percent")
    if used is not None:
        try:
            return max(0, min(100, 100 - float(used)))
        except (TypeError, ValueError):
            return None
    return None
