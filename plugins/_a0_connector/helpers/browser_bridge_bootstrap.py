"""Explicit process owner for the optional Browser bridge application.

Importing this module does not construct or install a runtime.  The server
bootstrap must bind one fully composed application; absent that binding,
authentication remains hello-only and the protected site API remains
unavailable.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_runtime import (
    CONNECTOR_PROTOCOL,
    REQUIRED_INBOUND_EVENTS,
    REQUIRED_OUTBOUND_EVENTS,
    BrowserBridgeRuntimeRoute,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
)
from plugins._a0_connector.helpers.browser_bridge_site_authority import (
    bind_browser_bridge_site_authority_repository,
)
from plugins._a0_connector.helpers.browser_bridge_action_authority import (
    bind_browser_bridge_action_authority,
)

if TYPE_CHECKING:
    from plugins._a0_connector.helpers.browser_bridge_application import (
        BrowserBridgeApplication,
    )


_HELLO_INBOUND_EVENTS = frozenset({"connector_hello"})
_NO_OUTBOUND_EVENTS = frozenset()
_application: BrowserBridgeApplication | None = None
_retiring = False
_lock = threading.RLock()


def bind_browser_bridge_application(
    application: BrowserBridgeApplication | None,
) -> None:
    """Install or clear the one explicitly server-owned application."""

    if application is not None:
        from plugins._a0_connector.helpers.browser_bridge_application import (
            BrowserBridgeApplication,
        )

        if not isinstance(application, BrowserBridgeApplication):
            raise TypeError("invalid Browser bridge application")
        if not application.installed:
            raise RuntimeError("Browser bridge application is not installed")
    global _application
    with _lock:
        current = _application
        if _retiring:
            raise RuntimeError("Browser bridge application is retiring")
        if current is not None and application is not None and current is not application:
            raise RuntimeError("Browser bridge application is already installed")
        if current is not None and application is None:
            raise RuntimeError("retire the Browser bridge application explicitly")
        if application is not None:
            application.claim_bootstrap_binding()
        _application = application
        bind_browser_bridge_site_authority_repository(
            application.sites if application is not None else None
        )
        bind_browser_bridge_action_authority(application.actions if application is not None else None)


def get_browser_bridge_application() -> BrowserBridgeApplication | None:
    with _lock:
        application = None if _retiring else _application
        return (
            application
            if application is not None and application.installed
            else None
        )


def browser_bridge_principal_events(
) -> tuple[frozenset[str], frozenset[str]]:
    """Freeze event authority according to the application binding at auth."""

    with _lock:
        if _application is None or _retiring or not _application.installed:
            return _HELLO_INBOUND_EVENTS, _NO_OUTBOUND_EVENTS
        return REQUIRED_INBOUND_EVENTS, REQUIRED_OUTBOUND_EVENTS


def register_browser_bridge_hello(
    *,
    principal: WsPrincipal,
    connector_sid: str,
    data: object,
) -> BrowserBridgeRuntimeRoute | None:
    """Atomically select the installed owner and register one exact hello."""

    with _lock:
        application = _application
        if application is None or _retiring:
            return None
        return application.register_hello(
            principal=principal,
            connector_sid=connector_sid,
            data=data,
        )


async def retire_browser_bridge_application(
    application: BrowserBridgeApplication,
) -> bool:
    """Withdraw one exact owner, await its cleanup, then clear API binding."""

    global _application, _retiring
    with _lock:
        if _application is not application or _retiring:
            return False
        _retiring = True
    try:
        await application.close(_bootstrap_retirement=True)
    finally:
        with _lock:
            if _application is application:
                _application = None
                bind_browser_bridge_site_authority_repository(None)
                bind_browser_bridge_action_authority(None)
            _retiring = False
    return True


def admitted_hello_projection(
    route: BrowserBridgeRuntimeRoute,
) -> dict[str, object]:
    """Return the exact authenticated transport projection for one route."""

    if not isinstance(route, BrowserBridgeRuntimeRoute):
        raise TypeError("invalid Browser bridge runtime route")
    principal = route.principal
    hello = route.hello
    if (
        not isinstance(principal, WsPrincipal)
        or route.transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        or route.bridge_id != hello.bridge_id
        or route.load_generation_id != hello.load_generation_id
    ):
        raise TypeError("invalid Browser bridge runtime route")
    return {
        "protocol": CONNECTOR_PROTOCOL,
        "principal_type": "browser_bridge",
        "features": sorted(hello.outer_features),
        "connector_session_ready": True,
        "browser_control_ready": True,
        "activation": route.activation.as_wire_dict(),
        "connector_binding": {
            "server_instance_id": route.server_instance_id,
            "bridge_id": route.bridge_id,
            "connector_sid": route.connector_sid,
            "key_generation": principal.key_generation,
            "load_generation_id": route.load_generation_id,
        },
        "host_browser": {
            "supported": True,
            "enabled": True,
            "status": "ready",
            "backend_id": "chrome_extension",
            "browser_id": route.browser_id,
            "browser_label": hello.browser_label,
            "contract_version": hello.contract_version,
            "features": ["browser_extension_bridge_v1"],
            "capabilities": {
                "actions": sorted(hello.actions),
                "features": sorted(hello.features),
                "limits": dict(hello.limits),
            },
            "extension": {
                "version": hello.extension_version,
                "manifest_version": 3,
                "load_generation_id": hello.load_generation_id,
            },
            "companion": {
                "version": hello.companion_version,
                "platform": hello.companion_platform,
                "arch": hello.companion_arch,
            },
        },
    }
