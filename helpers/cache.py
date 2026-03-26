import fnmatch
import threading
import time
from dataclasses import dataclass
from typing import Any

_lock = threading.RLock()
_cache: dict[str, dict[str, "CacheEntry"]] = {}

_enabled_global: bool = True
_enabled_areas: dict[str, bool] = {}


@dataclass(slots=True)
class CacheEntry:
    value: Any
    timestamp: float


def toggle_global(enabled: bool) -> None:
    global _enabled_global
    _enabled_global = enabled


def toggle_area(area: str, enabled: bool) -> None:
    _enabled_areas[area] = enabled


def has(area: str, key: Any) -> bool:
    if not _is_enabled(area):
        return False
    with _lock:
        entry = _cache.get(area, {}).get(key)
        if entry is None:
            return False
        _touch_entry(entry)
        return True


def add(area: str, key: Any, data: Any) -> None:
    if not _is_enabled(area):
        return
    with _lock:
        if area not in _cache:
            _cache[area] = {}
        _cache[area][key] = _create_entry(data)


def get(area: str, key: Any, default: Any = None) -> Any:
    if not _is_enabled(area):
        return default
    with _lock:
        entry = _cache.get(area, {}).get(key)
        if entry is None:
            return default
        _touch_entry(entry)
        return entry.value


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


def trim_cache(area: str, seconds: float = 300) -> None:
    cutoff = time.time() - seconds
    with _lock:
        for area_key in _get_matching_areas(area):
            area_cache = _cache.get(area_key)
            if not area_cache:
                continue

            keys_to_remove = [key for key, entry in area_cache.items() if entry.timestamp < cutoff]
            for key in keys_to_remove:
                area_cache.pop(key, None)

            if not area_cache:
                _cache.pop(area_key, None)


def clear_all() -> None:
    with _lock:
        _cache.clear()


def _is_enabled(area: str) -> bool:
    if not _enabled_global:
        return False
    return _enabled_areas.get(area, True)


def _create_entry(value: Any) -> CacheEntry:
    return CacheEntry(value=value, timestamp=time.time())


def _touch_entry(entry: CacheEntry) -> None:
    entry.timestamp = time.time()


def _get_matching_areas(area: str) -> list[str]:
    if any(ch in area for ch in "*?["):
        return [k for k in _cache.keys() if fnmatch.fnmatch(k, area)]
    return [area]


def determine_cache_key(agent, *additional):
    if agent:
        profile = agent.config.profile or "none"
        project = agent.context.get_data("project") or "none"
        return (profile, project, *additional)
    return ("none", "none", *additional)