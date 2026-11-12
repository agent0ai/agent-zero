from __future__ import annotations

import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import threading
from typing import Any, Iterator
from contextlib import contextmanager

from plugins._a0_connector.helpers.browser_bridge_application import (
    BrowserBridgeApplication,
)
from plugins._a0_connector.helpers.browser_bridge_bootstrap import (
    admitted_hello_projection,
    bind_browser_bridge_application,
    browser_bridge_principal_events,
    get_browser_bridge_application,
    retire_browser_bridge_application,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import (
    EXPECTED_LIMITS,
    REQUIRED_INBOUND_EVENTS,
    REQUIRED_OUTBOUND_EVENTS,
)
from plugins._browser.helpers.extension_sessions import (
    ExtensionSessionLifecycle,
    ExtensionSessionRegistry,
)
from test_browser_bridge_runtime_foundation import (
    EXTENSION_ID,
    _active,
    _admission,
    _hello,
    _principal,
)


class _Memory:
    def __init__(self) -> None:
        self.value: Any = None

    def load(self) -> Any:
        return deepcopy(self.value)

    def save(self, value: Any) -> None:
        self.value = deepcopy(value)


class _Manager:
    def __init__(self, principal: Any) -> None:
        self.principal = principal
        self.emitted: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def principal_for_sid(self, _namespace: str, _sid: str) -> Any:
        return self.principal

    async def emit_to(self, *args: Any, **kwargs: Any) -> None:
        self.emitted.append((args, kwargs))


@contextmanager
def _loaded_connector() -> Iterator[type]:
    path = (
        Path(__file__).parents[1]
        / "plugins"
        / "_a0_connector"
        / "api"
        / "ws_connector.py"
    )
    previous = sys.modules.pop("ws_connector", None)
    spec = importlib.util.spec_from_file_location("ws_connector", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ws_connector"] = module
    try:
        spec.loader.exec_module(module)
        yield module.WsConnector
    finally:
        sys.modules.pop("ws_connector", None)
        if previous is not None:
            sys.modules["ws_connector"] = previous


def _application(manager: _Manager) -> BrowserBridgeApplication:
    memory = _Memory()
    return BrowserBridgeApplication(
        manager=manager,
        server_instance_id=lambda: "server-A",
        lifecycle=ExtensionSessionLifecycle(
            registry=ExtensionSessionRegistry(persistence=memory)
        ),
        active_principal_verifier=_active,
        admission_evaluator=_admission,
        context_authorizer=lambda _route, context_id: context_id == "context-A",
    )


def test_bootstrap_default_is_hello_only_and_explicit_binding_is_bounded() -> None:
    async def scenario() -> None:
        bind_browser_bridge_application(None)
        assert get_browser_bridge_application() is None
        assert browser_bridge_principal_events() == (
            frozenset({"connector_hello"}),
            frozenset(),
        )

        principal = _principal()
        application = _application(_Manager(principal))
        try:
            bind_browser_bridge_application(application)
        except RuntimeError as error:
            assert "not installed" in str(error)
        else:
            raise AssertionError("uninstalled application was bound")
        application.install()
        bind_browser_bridge_application(application)
        assert get_browser_bridge_application() is application
        assert browser_bridge_principal_events() == (
            REQUIRED_INBOUND_EVENTS,
            REQUIRED_OUTBOUND_EVENTS,
        )
        try:
            await application.close()
        except RuntimeError as error:
            assert "retire" in str(error)
        else:
            raise AssertionError("bound application bypassed explicit retirement")
        try:
            bind_browser_bridge_application(None)
        except RuntimeError as error:
            assert "retire" in str(error)
        else:
            raise AssertionError("installed owner was cleared without retirement")
        assert await retire_browser_bridge_application(application)
        assert get_browser_bridge_application() is None

    asyncio.run(scenario())


def test_handler_registers_exact_hello_and_returns_full_authenticated_route() -> None:
    async def scenario() -> None:
        principal = _principal()
        manager = _Manager(principal)
        application = _application(manager)
        application.install()
        bind_browser_bridge_application(application)
        try:
            with _loaded_connector() as WsConnector:
                WsConnector.principal_is_active = classmethod(
                    lambda _cls, candidate: candidate is principal
                )
                connector = WsConnector(
                    None,
                    threading.RLock(),
                    manager=manager,
                )
                connector._principal = principal
                connector._principal_sid = "sid-A"
                transport_data = {**_hello(principal), "correlationId": "hello-transport-1"}
                response = await connector.process(
                    "connector_hello",
                    transport_data,
                    "sid-A",
                )
                assert transport_data["correlationId"] == "hello-transport-1"
                route = application.registry.current_sid_route(principal, "sid-A")
                assert route is not None
                assert response == admitted_hello_projection(route)
                assert response == {
                    "protocol": "a0-connector.v1",
                    "principal_type": "browser_bridge",
                    "features": [
                        "browser_extension_bridge_v1",
                        "connector_browser_artifact_chunks",
                        "connector_browser_control",
                        "connector_browser_event",
                    ],
                    "connector_session_ready": True,
                    "browser_control_ready": True,
                    "activation": {
                        "principal": "browser_bridge",
                        "bridge_id": "bridge-A",
                        "key_generation": 1,
                        "extension_id": EXTENSION_ID,
                        "install_instance_id": "install-A",
                        "server_features": [
                            "browser_extension_bridge_v1",
                            "connector_browser_artifact_chunks",
                            "connector_browser_control",
                            "connector_browser_event",
                        ],
                        "rollout": "preview_authorized",
                        "selected_bridge": True,
                        "heartbeat_fresh": True,
                        "subject_profile_bound": True,
                        "legacy_control_plane_inactive": True,
                    },
                    "connector_binding": {
                        "server_instance_id": "server-A",
                        "bridge_id": "bridge-A",
                        "connector_sid": "sid-A",
                        "key_generation": 1,
                        "load_generation_id": "generation-A",
                    },
                    "host_browser": {
                        "supported": True,
                        "enabled": True,
                        "status": "ready",
                        "backend_id": "chrome_extension",
                        "browser_id": "extension:bridge-A",
                        "browser_label": "Chrome - Agent Zero Extension",
                        "contract_version": 1,
                        "features": ["browser_extension_bridge_v1"],
                        "capabilities": {
                            "actions": ["list", "navigate", "open", "state"],
                            "features": ["cursor_v1", "tab_leases_v1"],
                            "limits": dict(EXPECTED_LIMITS),
                        },
                        "extension": {
                            "version": "0.2.0",
                            "manifest_version": 3,
                            "load_generation_id": "generation-A",
                        },
                        "companion": {
                            "version": "2.12.0",
                            "platform": "darwin",
                            "arch": "arm64",
                        },
                    },
                }
                serialized = repr(response)
                for forbidden in (
                    "single_user",
                    "companion-bridge-A",
                    "exec_config",
                    "remote_files",
                    "public_key",
                ):
                    assert forbidden not in serialized

                # Only framework metadata is stripped; arbitrary document
                # fields still reach (and are rejected by) strict decoders.
                invalid = await connector.process("connector_hello", {
                    **transport_data, "unexpected_authority": True,
                }, "sid-A")
                assert invalid.as_result(handler_id=connector.identifier,
                    fallback_correlation_id="hello-transport-2")["error"]["code"] == "INVALID_HELLO"

                forwarded = []
                async def capture_dispatch(candidate, sid, event, document):
                    forwarded.append((candidate, sid, event, document))
                    return {"accepted": True}
                application.dispatch = capture_dispatch
                operation = {"contract_version": 1, "correlationId": "op-transport-1", "unknown": True}
                await connector.process("connector_browser_op_result", operation, "sid-A")
                assert forwarded == [(principal, "sid-A", "connector_browser_op_result",
                    {"contract_version": 1, "unknown": True})]
                assert operation["correlationId"] == "op-transport-1"
                del application.dispatch

                second = WsConnector(
                    None,
                    threading.RLock(),
                    manager=manager,
                )
                second._principal = principal
                second._principal_sid = "sid-unadmitted"
                denied = await second.process(
                    "connector_browser_op_result",
                    {"contract_version": 1},
                    "sid-unadmitted",
                )
                projected = denied.as_result(
                    handler_id=second.identifier,
                    fallback_correlation_id=None,
                )
                assert projected["ok"] is False
                assert projected["error"] == {
                    "code": "RUNTIME_NOT_ADMITTED",
                    "error": "Browser bridge request rejected",
                }

                await connector.on_disconnect("sid-A")
                assert application.registry.session_count == 0
        finally:
            await retire_browser_bridge_application(application)

    asyncio.run(scenario())


def test_handler_never_routes_restricted_event_into_legacy_when_owner_disappears() -> None:
    async def scenario() -> None:
        principal = _principal()
        manager = _Manager(principal)
        bind_browser_bridge_application(None)
        with _loaded_connector() as WsConnector:
            WsConnector.principal_is_active = classmethod(
                lambda _cls, candidate: candidate is principal
            )
            connector = WsConnector(None, threading.RLock(), manager=manager)
            connector._principal = principal
            connector._principal_sid = "sid-A"

            def legacy_result(*_args: Any, **_kwargs: Any) -> None:
                raise AssertionError("restricted event reached legacy handler")

            connector._handle_browser_op_result = legacy_result
            denied = await connector.process(
                "connector_browser_op_result",
                {"contract_version": 1},
                "sid-A",
            )
            projected = denied.as_result(
                handler_id=connector.identifier,
                fallback_correlation_id=None,
            )
            assert projected["error"]["code"] == "RUNTIME_NOT_ADMITTED"

    asyncio.run(scenario())
