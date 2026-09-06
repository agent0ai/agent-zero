"""Fail-closed server selection for the extension Browser runtime.

The WebUI may identify the chat whose Browser panel is open, but it does not
select a bridge. Selection is derived from that live AgentContext's agent0
project/profile configuration and is valid only for the host-required backend.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Mapping


_CONTEXT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_BRIDGE_ID = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?"
)
_write_lock = threading.RLock()


def default_selected_bridge() -> str | None:
    """Read the explicit global default, independently of any loaded chat."""
    from helpers import plugins
    from plugins._browser.helpers.config import parse_extension_browser_selection

    config = plugins.get_plugin_config("_browser", project_name="", agent_profile="")
    if not isinstance(config, Mapping):
        raise RuntimeError("browser defaults are unavailable")
    if config.get("runtime_backend") != "host_required":
        return None
    selection = parse_extension_browser_selection(config.get("host_browser_selection"))
    return selection.bridge_id if selection is not None else None


def select_default_bridge(bridge_id: str | None, *, expected_bridge_id: str | None) -> str | None:
    """Explicit global-only CAS; scoped settings and consent are unchanged."""
    from helpers import plugins, runtime
    from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application
    from plugins._a0_connector.helpers.browser_bridge_pairing import (
        SUBJECT_ID, configured_extension_id, get_browser_bridge_pairing_store,
    )
    from plugins._browser.helpers.config import protected_production_selection_write
    from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate

    for value in (bridge_id, expected_bridge_id):
        if value is not None and (not isinstance(value, str) or _BRIDGE_ID.fullmatch(value) is None):
            raise ValueError("invalid browser selection")
    if bridge_id is None and expected_bridge_id is None:
        raise ValueError("missing previous browser selection")
    with _write_lock:
        previous = default_selected_bridge()
        if previous != expected_bridge_id:
            raise RuntimeError("browser default changed")
        application = get_browser_bridge_application()

        def check_pair():
            if application is None or get_browser_bridge_gate().state != "available":
                raise RuntimeError("browser runtime is not configured")
            record = get_browser_bridge_pairing_store().active_bridge_record(
                bridge_id=bridge_id, server_instance_id=runtime.get_persistent_id(),
            )
            if (not isinstance(record, Mapping) or record.get("subject_id") != SUBJECT_ID
                    or record.get("extension_id") != configured_extension_id()):
                raise RuntimeError("paired browser is unavailable")

        if bridge_id is not None:
            check_pair()
        config = dict(plugins.get_plugin_config("_browser", project_name="", agent_profile=""))
        config.update(runtime_backend="host_required" if bridge_id else "container",
                      host_browser_selection=f"extension:{bridge_id}" if bridge_id else "")
        if application is not None and previous is not None and previous != bridge_id:
            application.registry.retire_bridge(previous)
        with protected_production_selection_write():
            plugins.save_plugin_config("_browser", "", "", config, caller="api")
        if default_selected_bridge() != bridge_id:
            raise RuntimeError("browser default readback failed")
        if bridge_id is not None:
            check_pair()
        return bridge_id


def selected_bridge(context_id: Any) -> str | None:
    """Return the bridge selected by current server-owned context config."""

    if not isinstance(context_id, str) or _CONTEXT_ID.fullmatch(context_id) is None:
        return None
    try:
        from agent import AgentContext
        from plugins._browser.helpers.config import (
            HOST_BROWSER_SELECTION_KEY,
            RUNTIME_BACKEND_KEY,
            get_browser_config,
            parse_extension_browser_selection,
        )

        context = AgentContext.get(context_id)
        if context is None or getattr(context, "id", None) != context_id:
            return None
        agent = getattr(context, "agent0", None)
        if agent is None or getattr(agent, "context", None) is not context:
            return None
        config = get_browser_config(agent=agent)
        if (
            not isinstance(config, Mapping)
            or config.get(RUNTIME_BACKEND_KEY) != "host_required"
        ):
            return None
        selection = parse_extension_browser_selection(
            config.get(HOST_BROWSER_SELECTION_KEY)
        )
        if selection is None or _BRIDGE_ID.fullmatch(selection.bridge_id) is None:
            return None
        return selection.bridge_id
    except Exception:
        return None


def selection_current(context_id: Any, bridge_id: Any) -> bool:
    """Check one claimed bridge against the context's current server selection."""

    if not isinstance(bridge_id, str) or _BRIDGE_ID.fullmatch(bridge_id) is None:
        return False
    return selected_bridge(context_id) == bridge_id


def select_bridge_for_context(context_id: str, bridge_id: str | None, *, expected_bridge_id: str | None = None) -> str | None:
    """Protected API mutation with active-record validation and exact readback.

    Browser's configuration is project-scoped, never profile-scoped. Selection
    remains separate from readiness; a newly selected native must authenticate
    and supply a currently admitted hello before any operation can execute.
    """
    from agent import AgentContext
    from helpers import plugins, projects, runtime
    from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application
    from plugins._a0_connector.helpers.browser_bridge_pairing import (
        SUBJECT_ID, configured_extension_id, get_browser_bridge_pairing_store,
    )
    from plugins._browser.helpers.config import (
        get_browser_config, protected_production_selection_write,
    )
    from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate

    if not isinstance(context_id, str) or _CONTEXT_ID.fullmatch(context_id) is None:
        raise ValueError("invalid browser context")
    if bridge_id is not None and (
        not isinstance(bridge_id, str) or _BRIDGE_ID.fullmatch(bridge_id) is None
    ):
        raise ValueError("invalid browser selection")
    with _write_lock:
        if bridge_id is None and (
            not isinstance(expected_bridge_id, str)
            or _BRIDGE_ID.fullmatch(expected_bridge_id) is None
            or selected_bridge(context_id) != expected_bridge_id
        ):
            raise RuntimeError("browser selection changed")
        context = AgentContext.get(context_id)
        if context is None or getattr(getattr(context, "agent0", None), "context", None) is not context:
            raise ValueError("invalid browser context")
        application = get_browser_bridge_application()
        if bridge_id is not None:
            if application is None or get_browser_bridge_gate().state != "available":
                raise RuntimeError("browser runtime is not configured")
            record = get_browser_bridge_pairing_store().active_bridge_record(
                bridge_id=bridge_id, server_instance_id=runtime.get_persistent_id(),
            )
            if (
                not isinstance(record, Mapping) or record.get("subject_id") != SUBJECT_ID
                or record.get("extension_id") != configured_extension_id()
            ):
                raise RuntimeError("paired browser is unavailable")
        config = dict(get_browser_config(agent=context.agent0))
        config.update(
            runtime_backend="host_required" if bridge_id is not None else "container",
            host_browser_selection=f"extension:{bridge_id}" if bridge_id is not None else "",
        )
        # Retire before a shared scope changes. Even if persistence subsequently
        # fails, old pending operations cannot race a newly selected browser.
        previous_bridge = selected_bridge(context_id)
        if application is not None and previous_bridge is not None and previous_bridge != bridge_id:
            application.registry.retire_bridge(previous_bridge)
        with protected_production_selection_write():
            plugins.save_plugin_config(
                "_browser", projects.get_context_project_name(context) or "", "",
                config, caller="api",
            )
        if selected_bridge(context_id) != bridge_id:
            raise RuntimeError("browser selection readback failed")
        return bridge_id
