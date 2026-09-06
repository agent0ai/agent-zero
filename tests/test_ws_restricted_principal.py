"""Effect-free shared WebSocket security regressions (sync pytest entry points)."""

import asyncio
from dataclasses import FrozenInstanceError
import threading
from unittest.mock import AsyncMock

import pytest
from flask import Flask
from werkzeug.test import EnvironBuilder

from helpers import ws
from helpers.ws import WsHandler
from helpers.ws_manager import BufferedEvent, WsManager, WsResult
from helpers.ws_principal import WsPrincipal, WsScopeDeniedError


PATH = "plugins/_test/scoped"
NS = "/ws"


class Scoped(WsHandler):
    active = True
    calls = []
    fail = False

    @classmethod
    def accepted_principal_types(cls):
        return frozenset({"browser_bridge"})

    @classmethod
    def authenticate_principal(cls, auth):
        envelope = auth.get("principal")
        if envelope != {"type": "browser_bridge", "proof": {}, "signature": "valid"}:
            return None
        return principal()

    @classmethod
    def principal_is_active(cls, value):
        return cls.active

    async def on_connect(self, sid):
        if self.fail:
            raise ValueError("secret activation error")

    async def process(self, event, data, sid):
        self.calls.append((event, data, sid))
        return {"safe": True}


def principal(**overrides):
    values = dict(
        principal_type="browser_bridge", principal_id="bridge-1",
        subject_id="single_user", scopes={"bridge.connect"},
        handler_path=PATH, handler_id=f"{Scoped.__module__}.{Scoped.__name__}",
        inbound_events={"connector_hello"}, outbound_events={"connector_bridge_credential_status"},
        key_generation=1,
    )
    values.update(overrides)
    return WsPrincipal(**values)


class Socket:
    def __init__(self):
        self.handlers = {}
        self.emit = AsyncMock()
        self.disconnect = AsyncMock()

    def on(self, event, *, namespace):
        def decorate(fn):
            self.handlers[event] = fn
            return fn
        return decorate


@pytest.fixture
def setup(monkeypatch):
    server = Socket()
    manager = WsManager(server, threading.RLock())
    app = Flask(__name__)
    app.secret_key = "synthetic-test-secret"
    monkeypatch.setattr(ws.cache, "get", lambda area, path: Scoped if path == PATH else None)
    monkeypatch.setattr(Scoped, "active", True)
    monkeypatch.setattr(Scoped, "calls", [])
    monkeypatch.setattr(Scoped, "fail", False)
    monkeypatch.setattr(ws, "_ws_contexts", {})
    monkeypatch.setattr(ws, "_active_handlers", {})
    ws.register_ws_namespace(server, app, threading.RLock(), manager)
    return server, manager, app


def auth():
    return {"handlers": [PATH], "principal": {"type": "browser_bridge", "proof": {}, "signature": "valid"}}


def environ(origin="http://localhost:50080"):
    return EnvironBuilder(base_url="http://localhost:50080", headers={"Origin": origin}).get_environ()


async def connect(setup, sid="bridge"):
    server, manager, app = setup
    assert await server.handlers["connect"](sid, environ(), auth()) is True
    return ws._active_handlers[sid][PATH]


def test_principal_is_deeply_immutable():
    events = {"connector_hello"}
    value = principal(inbound_events=events)
    events.add("code_execution")
    assert value.inbound_events == frozenset({"connector_hello"})
    with pytest.raises(FrozenInstanceError):
        value.key_generation = 2


@pytest.mark.parametrize("mutation", [
    lambda a: a.update(principal=None),
    lambda a: a.update(principal={}),
    lambda a: a["principal"].update(signature="bad"),
    lambda a: a["principal"].update(type="webui_session"),
    lambda a: a["principal"].update(scopes=["everything"]),
    lambda a: a.update(api_key="ambient", csrf_token="ambient"),
    lambda a: a.update(handlers=[PATH, "ws_webui"]),
    lambda a: a.update(handlers=["../ws_webui"]),
    lambda a: a.update(handlers=[]),
])
def test_invalid_principal_never_falls_back_to_ambient_auth(setup, mutation, monkeypatch):
    server, manager, app = setup
    value = auth()
    mutation(value)
    # An open server would accept ordinary session auth. None of these may
    # become an ordinary/open client instead.
    assert asyncio.run(server.handlers["connect"]("bad", environ(), value)) is False
    assert not manager.connections and not ws._ws_contexts
    assert not server.emit.called


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost:broken"])
def test_origin_rejected_before_authenticator(setup, monkeypatch, origin):
    server, manager, app = setup
    called = []
    monkeypatch.setattr(Scoped, "authenticate_principal", lambda a: called.append(a))
    assert asyncio.run(server.handlers["connect"]("bad", environ(origin), auth())) is False
    assert called == []


def test_scoped_connect_isolated_from_ambient_and_global_lifecycle(setup):
    async def scenario():
        server, manager, app = setup
        global_handler = Scoped(server, threading.RLock())
        global_handler.on_connect = AsyncMock()
        global_handler.on_disconnect = AsyncMock()
        manager.register_handlers({NS: [global_handler]})
        manager.set_server_restart_broadcast(True)
        manager.buffers[(NS, "bridge")].append(BufferedEvent("state_push", {"secret": "canary"}))
        instance = await connect(setup)
        ctx = ws._ws_contexts["bridge"]
        assert ctx.principal is manager.connections[(NS, "bridge")].principal
        assert ctx.auth_hash is ctx.api_key is ctx.csrf_token is ctx.csrf_cookie is None
        assert not manager.user_to_sids and not manager.sid_to_user
        assert not manager.buffers and not server.emit.called
        assert not manager.register_diagnostic_watcher(NS, "bridge")
        global_handler.on_connect.assert_not_called()
        with pytest.raises(WsScopeDeniedError):
            instance.principal_for_sid("someone-else")
        await server.handlers["disconnect"]("bridge")
        await server.handlers["disconnect"]("bridge")
        global_handler.on_disconnect.assert_not_called()
        assert not manager.connections and not manager._known_sids
        assert not manager._disconnect_times and not ws._ws_contexts
    asyncio.run(scenario())


def test_activation_failure_rolls_back_without_legacy_lifecycle(setup, monkeypatch):
    server, manager, app = setup
    monkeypatch.setattr(Scoped, "fail", True)
    assert asyncio.run(server.handlers["connect"]("bridge", environ(), auth())) is False
    assert not manager.connections and not manager._known_sids and not ws._ws_contexts


@pytest.mark.parametrize("event", ["state_request", "connector_send_message", "connector_exec_op_result", "connector_file_op_result", "secret-arbitrary-event"])
def test_denied_inbound_never_invokes_handler_or_diagnostic_payloads(setup, event):
    async def scenario():
        server, manager, app = setup
        await connect(setup)
        manager._diagnostics_enabled = True
        result = await server.handlers["*"](event, "bridge", {"data": {"secret": "canary"}})
        assert result["results"][0]["error"]["code"] == "SCOPE_DENIED"
        assert not Scoped.calls and not server.emit.called
        assert len(manager._scope_denials) == 1
        assert "canary" not in str(manager._scope_denials)
        assert event not in str(manager._scope_denials)
    asyncio.run(scenario())


def test_allowed_inbound_and_direct_manager_rechecks_active_identity(setup, monkeypatch):
    async def scenario():
        server, manager, app = setup
        instance = await connect(setup)
        result = await server.handlers["*"]("connector_hello", "bridge", {"data": {"secret": "canary"}, "correlationId": {"secret": "canary"}})
        assert result["results"][0]["data"] == {"safe": True}
        assert "canary" not in result["correlationId"]
        assert len(Scoped.calls) == 1
        monkeypatch.setattr(Scoped, "active", False)
        result = await manager.process_client_event(NS, "connector_hello", {}, "bridge", handlers=[instance])
        assert result["results"][0]["error"]["code"] == "SCOPE_DENIED"
        await server.handlers["disconnect"]("bridge")
        result = await manager.process_client_event(NS, "connector_hello", {}, "bridge", handlers=[instance])
        assert result["results"][0]["error"]["code"] == "SCOPE_DENIED"
        assert len(Scoped.calls) == 1
    asyncio.run(scenario())


@pytest.mark.parametrize("event,handler", [
    ("server_restart", None), ("state_push", None),
    ("ws_dev_console_event", None), ("connector_bridge_credential_status", "unrelated"),
])
def test_forbidden_outbound_is_typed_and_never_buffered(setup, event, handler):
    async def scenario():
        server, manager, app = setup
        await connect(setup)
        with pytest.raises(WsScopeDeniedError):
            await manager.emit_to(NS, "bridge", event, {"secret": "canary"}, handler_id=handler, diagnostic=True)
        assert not server.emit.called and not manager.buffers
    asyncio.run(scenario())


def test_outbound_revalidates_and_broadcast_never_targets_restricted_sids(setup, monkeypatch):
    async def scenario():
        server, manager, app = setup
        instance = await connect(setup)
        await manager.emit_to(NS, "bridge", "connector_bridge_credential_status", {}, handler_id=instance.identifier)
        assert server.emit.await_count == 1
        server.emit.reset_mock()
        monkeypatch.setattr(Scoped, "active", False)
        with pytest.raises(WsScopeDeniedError):
            await manager.emit_to(NS, "bridge", "connector_bridge_credential_status", {}, handler_id=instance.identifier)
        await manager.broadcast(NS, "connector_bridge_credential_status", {}, handler_id=instance.identifier)
        assert not server.emit.called
        assert await manager.route_event_all(NS, "connector_hello", {}) == []
    asyncio.run(scenario())


def test_new_proof_replaces_old_sid_and_old_handler_cannot_dispatch(setup):
    async def scenario():
        server, manager, app = setup
        old = await connect(setup, "old")
        await connect(setup, "new")
        server.disconnect.assert_awaited_once_with("old", namespace=NS)
        assert (NS, "old") not in manager.connections
        result = await manager.process_client_event(NS, "connector_hello", {}, "old", handlers=[old])
        assert result["results"][0]["error"]["code"] == "SCOPE_DENIED"
        with pytest.raises(WsScopeDeniedError):
            await old.emit_to("old", "connector_bridge_credential_status", {})
        with pytest.raises(WsScopeDeniedError):
            await old.broadcast("connector_bridge_credential_status", {})
        with pytest.raises(WsScopeDeniedError):
            await old.dispatch_to_all_sids("connector_hello", {})
    asyncio.run(scenario())


def test_queued_emit_cannot_cross_connection_generation(setup):
    async def scenario():
        server, manager, app = setup
        await manager.handle_connect(NS, "reused")
        old = manager.connections[(NS, "reused")]
        # Capture work already authorized for a legacy generation.
        queued = manager._emit_for_connection(old, "state_push", {"secret": "canary"})
        await manager.handle_disconnect(NS, "reused")
        await connect(setup, "reused")
        server.emit.reset_mock()
        await queued
        assert not server.emit.called
    asyncio.run(scenario())


@pytest.mark.parametrize("raised", [True, False])
def test_handler_failures_do_not_echo_raw_error_details(setup, raised, monkeypatch):
    async def scenario():
        server, manager, app = setup
        instance = await connect(setup)
        async def fail(*args):
            if raised:
                raise ValueError("secret-canary")
            return WsResult.error(code="secret-canary", message="secret-canary", details="secret-canary")
        monkeypatch.setattr(instance, "process", fail)
        result = await manager.process_client_event(NS, "connector_hello", {}, "bridge", handlers=[instance])
        assert "secret-canary" not in str(result)
        assert result["results"][0]["ok"] is False
    asyncio.run(scenario())


def test_signed_proof_through_real_loaded_connector_and_namespace(setup, monkeypatch):
    # Reuse the effect-free credential fixture, but exercise real Flask request
    # context, module loading, WsHandler hooks, manager and connector together.
    from test_browser_bridge_challenge_foundation import (
        _credential, _challenge_store, _issue, _proof, _signature,
        SERVER_ID, EXTENSION_ID, BRIDGE_CONNECTOR_HANDLER,
    )
    from helpers import runtime
    from helpers.modules import load_classes_from_file
    from plugins._a0_connector.helpers import browser_bridge_session as adapter
    from plugins._a0_connector.helpers import ws_runtime

    pairing, state, key = _credential()
    challenges, clock = _challenge_store(pairing)
    proof = _proof(_issue(challenges))
    signature = _signature(key, proof)
    envelope = {
        "handlers": [BRIDGE_CONNECTOR_HANDLER],
        "principal": {"type": "browser_bridge", "proof": proof, "signature": signature},
    }
    handler = load_classes_from_file("plugins/_a0_connector/api/ws_connector.py", WsHandler)[0]
    monkeypatch.setattr(ws.cache, "get", lambda area, path: handler if path == BRIDGE_CONNECTOR_HANDLER else None)
    monkeypatch.setattr(runtime, "get_persistent_id", lambda: SERVER_ID)
    monkeypatch.setattr(adapter, "get_browser_bridge_challenge_store", lambda: challenges)
    monkeypatch.setattr(adapter, "get_browser_bridge_pairing_store", lambda: pairing)
    monkeypatch.setenv("A0_BROWSER_BRIDGE_ROLLOUT", "preview")
    monkeypatch.setenv("A0_BROWSER_BRIDGE_EXTENSION_ID", EXTENSION_ID)
    monkeypatch.delenv("A0_BROWSER_BRIDGE_SERVER_BASE_URL", raising=False)

    async def scenario():
        server, manager, app = setup
        old_cli_sids = ws_runtime.connected_sids()
        assert await server.handlers["connect"]("signed", environ(), envelope)
        ctx = ws._ws_contexts["signed"]
        assert ctx.principal.handler_id == "ws_connector.WsConnector"
        assert signature not in repr(ctx) and proof["server_nonce"] not in repr(ctx)
        assert ws_runtime.connected_sids() == old_cli_sids
        response = await server.handlers["*"]("connector_hello", "signed", {"data": {"remote_exec": {"enabled": True}, "context_id": "victim"}})
        assert response["results"][0]["data"] == adapter.hello({})
        assert not server.emit.called
        assert await server.handlers["connect"]("replay", environ(), envelope) is False
        # Credential changes apply to the already connected namespace path.
        record = state["document"]["bridges"][0]
        record["state"] = "revoked"
        record["revoked_at_ms"] = clock[0]
        denied = await server.handlers["*"]("connector_hello", "signed", {})
        assert denied["results"][0]["error"]["code"] == "SCOPE_DENIED"
        await server.handlers["disconnect"]("signed")
        assert not manager.connections and not manager.buffers
        assert ws_runtime.connected_sids() == old_cli_sids
    asyncio.run(scenario())
