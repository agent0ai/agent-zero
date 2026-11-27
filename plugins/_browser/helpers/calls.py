"""Batch ordering shared by internal and host browser transports."""
import asyncio
from typing import Any

def multi_group_key(call: dict[str, Any]) -> Any:
    value = call.get("browser_id")
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip()
    if raw.startswith("browser-"):
        raw = raw.split("-", 1)[1]
    try:
        return int(raw)
    except ValueError:
        return raw


async def run_browser_calls(calls: list[dict[str, Any]], dispatch: Any) -> list[dict[str, Any]]:
    if not isinstance(calls, list) or not calls:
        raise ValueError("multi requires a non-empty list of calls")
    groups: dict[Any, list[tuple[int, dict[str, Any]]]] = {}
    for idx, call in enumerate(calls):
        if not isinstance(call, dict):
            raise ValueError(f"calls[{idx}] is not an object")
        groups.setdefault(multi_group_key(call), []).append((idx, call))

    results: list[dict[str, Any]] = [{"ok": False, "error": "missing"} for _ in calls]

    async def run_group(group: list[tuple[int, dict[str, Any]]]) -> None:
        for idx, call in group:
            try:
                results[idx] = {"ok": True, "result": await dispatch(call)}
            except Exception as exc:
                results[idx] = {"ok": False, "error": str(exc)}

    await asyncio.gather(*(run_group(group) for group in groups.values()))
    return results

