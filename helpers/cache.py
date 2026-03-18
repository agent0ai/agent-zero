import fnmatch
import threading
from typing import Any

_lock = threading.RLock()
_cache: dict[str, dict[str, Any]] = {}

_enabled_global: bool = True
_enabled_areas: dict[str, bool] = {}


def toggle_global(enabled: bool) -> None:
    global _enabled_global
    _enabled_global = enabled


def toggle_area(area: str, enabled: bool) -> None:
    _enabled_areas[area] = enabled


def has(area: str, key: Any) -> bool:
    if not _is_enabled(area):
        return False
    with _lock:
        return key in _cache.get(area, {})


def add(area: str, key: Any, data: Any) -> None:
    if not _is_enabled(area):
        return
    with _lock:
        if area not in _cache:
            _cache[area] = {}
        _cache[area][key] = data


def get(area: str, key: Any, default: Any = None) -> Any:
    if not _is_enabled(area):
        return default
    with _lock:
        return _cache.get(area, {}).get(key, default)


def remove(area: str, key: Any) -> None:
    if not _is_enabled(area):
        return
    with _lock:
        if area in _cache:
            _cache[area].pop(key, None)


def clear(area: str) -> None:
    with _lock:
        if any(ch in area for ch in "*?["):
            keys_to_remove = [k for k in _cache.keys() if fnmatch.fnmatch(k, area)]
            for k in keys_to_remove:
                _cache.pop(k, None)
            return

        _cache.pop(area, None)


def clear_all() -> None:
    with _lock:
        _cache.clear()


def _is_enabled(area: str) -> bool:
    if not _enabled_global:
        return False
    return _enabled_areas.get(area, True)


def determine_cache_key(agent, *additional):
    if agent:
        profile = agent.config.profile or "none"
        project = agent.context.get_data("project") or "none"
        return (profile, project, *additional)
    return ("none", "none", *additional)