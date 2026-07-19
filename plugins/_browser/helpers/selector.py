from __future__ import annotations

from typing import Any

from helpers.errors import RepairableException
from plugins._browser.helpers.config import RUNTIME_BACKEND_KEY, get_browser_config
from plugins._browser.helpers.runtime import get_runtime as get_container_runtime


async def get_tool_runtime(agent: Any):
    context_id = str(agent.context.id)
    config = get_browser_config(agent=agent)
    backend = str(config.get(RUNTIME_BACKEND_KEY) or "container").strip()

    if backend == "container":
        return await get_container_runtime(context_id)

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
            f"{message} Connect A0 CLI to this chat, allow host browser access, and retry."
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
