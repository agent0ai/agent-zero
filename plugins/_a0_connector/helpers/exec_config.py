from __future__ import annotations

from typing import Any


_TIMEOUT_KEYS = ("first_output_timeout", "between_output_timeout", "max_exec_timeout", "dialog_timeout")


def _parse_patterns(value: object) -> list[str]:
    if isinstance(value, str):
        items = value.splitlines()
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def _parse_timeouts(cfg: dict[str, Any], prefix: str, defaults: tuple[int, ...]) -> dict[str, int]:
    return {
        key: int(cfg.get(f"{prefix}_{key}", default))
        for key, default in zip(_TIMEOUT_KEYS, defaults)
    }


def build_exec_config(*, agent: object | None = None) -> dict[str, Any]:
    from helpers import plugins

    cfg = plugins.get_plugin_config("_code_execution", agent=agent) or {}
    return {
        "version": 1,
        "code_exec_timeouts": _parse_timeouts(cfg, "code_exec", (30, 15, 180, 5)),
        "output_timeouts": _parse_timeouts(cfg, "output", (90, 45, 300, 5)),
        "prompt_patterns": _parse_patterns(cfg.get("prompt_patterns", "")),
        "dialog_patterns": _parse_patterns(cfg.get("dialog_patterns", "")),
    }
