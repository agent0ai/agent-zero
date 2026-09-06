from __future__ import annotations

from typing import Any

from helpers.errors import RepairableException
from plugins._browser.helpers.config import (
    HOST_BROWSER_SELECTION_KEY,
    RUNTIME_BACKEND_KEY,
    get_browser_config,
    parse_development_extension_browser_selection,
    parse_extension_browser_selection,
)

DOCKER_BROWSER_RECOVERY_HELP = (
    "To use Agent Zero's internal Docker browser instead, open Browser settings and "
    "set Browser location to Internal Docker browser, or run `/browser container` "
    "from A0 CLI."
)


async def get_container_runtime(context_id: str):
    from plugins._browser.helpers.runtime import get_runtime

    return await get_runtime(context_id)


async def get_tool_runtime(agent: Any):
    context_id = str(agent.context.id)
    config = get_browser_config(agent=agent)
    backend = str(config.get(RUNTIME_BACKEND_KEY) or "container").strip()

    if backend == "container":
        return await get_container_runtime(context_id)

    selection = config.get(HOST_BROWSER_SELECTION_KEY, "")
    try:
        development_selection = parse_development_extension_browser_selection(
            selection
        )
    except ValueError as exc:
        raise RepairableException(
            "The development Chrome extension browser selection is invalid. "
            "Choose it again from Browser settings. Agent Zero did not fall back."
        ) from exc
    if development_selection is not None:
        raise RepairableException(
            "This development browser connection has been retired. Pair and select the "
            "production Chrome extension in Browser settings. No fallback was attempted."
        )
    try:
        extension_selection = parse_extension_browser_selection(selection)
    except ValueError as exc:
        raise RepairableException(
            "The Chrome extension browser selection is invalid. Choose a paired browser "
            "from Browser settings and retry. Agent Zero did not fall back to another browser."
        ) from exc
    if extension_selection is not None:
        from plugins._browser.helpers.extension_runtime import wait_selected_extension_runtime

        runtime = await wait_selected_extension_runtime(agent, extension_selection.bridge_id)
        if runtime is not None:
            return runtime
        raise RepairableException(
            "The selected Chrome browser has not established a verified connection for this chat. "
            "Keep Chrome open and check its Agent Zero extension connection status. "
            "No browser action was sent by this attempt, and no other browser or tool was used. "
            "Agent Zero did not fall back to another browser. "
            "Do not repeat an earlier action whose outcome was unknown."
        )

    sid = _select_host_browser_candidate_sid(context_id)
    if sid:
        from plugins._browser.helpers.connector_runtime import ConnectorBrowserRuntime

        return ConnectorBrowserRuntime(context_id, agent)

    if backend == "host_required":
        detail = _host_browser_status_detail(context_id)
        message = (
            "Bring Your Own Browser mode is enabled, but no subscribed A0 CLI currently "
            "advertises host-browser support"
            + (f": {detail}" if detail else ".")
        )
        raise RepairableException(
            f"{message} Connect A0 CLI to this chat, allow host browser access, and retry. "
            f"{DOCKER_BROWSER_RECOVERY_HELP}"
        )

    return await get_container_runtime(context_id)


def _select_host_browser_target_sid(context_id: str) -> str | None:
    try:
        from plugins._a0_connector.helpers.ws_runtime import select_host_browser_target_sid
    except ImportError:
        return None
    return select_host_browser_target_sid(context_id)


def _select_host_browser_candidate_sid(context_id: str) -> str | None:
    try:
        from plugins._a0_connector.helpers.ws_runtime import select_host_browser_candidate_sid
    except ImportError:
        return _select_host_browser_target_sid(context_id)
    return select_host_browser_candidate_sid(context_id)


def _host_browser_status_detail(context_id: str) -> str:
    try:
        from plugins._a0_connector.helpers.ws_runtime import host_browser_metadata_for_context
    except ImportError:
        return ""
    statuses = host_browser_metadata_for_context(context_id)
    if not statuses:
        return "open A0 CLI and connect it to this Agent Zero chat."
    parts = []
    for status in statuses:
        parts.append(
            f"sid={status.get('sid')} supported={status.get('supported')} "
            f"can_prepare={status.get('can_prepare')} enabled={status.get('enabled')} "
            f"status={status.get('status') or 'unknown'} "
            f"reason={status.get('support_reason') or 'none'}"
        )
    return "; ".join(parts)
