from __future__ import annotations

import asyncio
import base64
import importlib
import sys
import threading
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from types import ModuleType
from typing import Any, Iterator

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import helpers
from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers import browser_bridge_session as session
from plugins._a0_connector.helpers import ws_runtime
from plugins._a0_connector.helpers.browser_bridge_auth import (
    BRIDGE_CONNECTOR_HANDLER,
    BrowserBridgeChallengeStore,
    canonical_proof_bytes,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    CONNECTOR_PROTOCOL,
    FIXED_BROWSER_BRIDGE_SCOPES,
    BrowserBridgePairingStore,
    BrowserBridgeRecordRepository,
    coarse_source_key,
)
from plugins._browser.helpers.bridge_foundation import BrowserBridgeGate


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"
OTHER_EXTENSION_ID = "bcdefghijklmnopabcdefghijklmnopa"
BRIDGE_ID = "22222222-2222-4222-8222-222222222222"
SERVER_ID = "server-instance-A"
SERVER_BASE_URL = "http://localhost:50080"
CLIENT_NONCE = base64.urlsafe_b64encode(bytes([3]) * 32).rstrip(b"=").decode()
HANDLER_ID = "plugins._a0_connector.api.ws_connector.WsConnector"


class _SessionFixture:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {}
        self.now = 1_788_492_445_000
        self.gate = "preview"
        self.server_id = SERVER_ID
        self.extension_id: str | None = EXTENSION_ID
        self._challenge_number = 0
        self.flask = ModuleType("flask")
        self.flask.Flask = object
        self.flask.session = {}
        self.flask.request = _Request(SERVER_BASE_URL)
        self.runtime = ModuleType("helpers.runtime")
        self.runtime.get_persistent_id = lambda: self.server_id

        def load() -> Any:
            return self.state.get("document")

        def save(value: dict[str, Any]) -> None:
            self.state["document"] = value

        self.private_key = Ed25519PrivateKey.generate()
        public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        encoded_public_key = base64.urlsafe_b64encode(public_key).rstrip(b"=").decode()
        repository = BrowserBridgeRecordRepository(load=load, save=save)
        repository.add(
            {
                "trust_version": 1,
                "bridge_id": BRIDGE_ID,
                "server_instance_id": SERVER_ID,
                "subject_id": "single_user",
                "display_name": "Synthetic browser host",
                "companion_instance_id": "companion-instance-A",
                "extension_id": EXTENSION_ID,
                "public_key": {
                    "algorithm": "Ed25519",
                    "encoding": "raw-base64url",
                    "value": encoded_public_key,
                },
                "key_generation": 1,
                "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
                "state": "active",
                "created_at_ms": self.now - 45_000,
                "last_authenticated_at_ms": None,
                "revoked_at_ms": None,
            }
        )
        self.pairing = BrowserBridgePairingStore(repository=repository)
        self.challenges = BrowserBridgeChallengeStore(
            record_lookup=lambda bridge_id, server_id: self.pairing.active_bridge_record(
                bridge_id=bridge_id,
                server_instance_id=server_id,
            ),
            record_authenticated=lambda bridge_id, generation, authenticated_at: (
                self.pairing.mark_bridge_authenticated(
                    bridge_id=bridge_id,
                    key_generation=generation,
                    authenticated_at_ms=authenticated_at,
                )
            ),
            clock_ms=lambda: self.now,
            random_bytes=lambda size: bytes([7]) * size,
            id_factory=self._next_challenge_id,
        )

    def _next_challenge_id(self) -> str:
        self._challenge_number += 1
        return f"challenge-{self._challenge_number}"

    def auth(self) -> dict[str, Any]:
        challenge = self.challenges.issue(
            {
                "trust_version": 1,
                "bridge_id": BRIDGE_ID,
                "client_nonce": CLIENT_NONCE,
            },
            source_key=coarse_source_key("127.0.0.1"),
            server_instance_id=SERVER_ID,
            server_base_url=SERVER_BASE_URL,
        )
        proof = {
            "aud": SERVER_ID,
            "bridge_id": BRIDGE_ID,
            "challenge_id": challenge.challenge_id,
            "client_nonce": CLIENT_NONCE,
            "handler": BRIDGE_CONNECTOR_HANDLER,
            "protocol": CONNECTOR_PROTOCOL,
            "server_base_url": SERVER_BASE_URL,
            "server_nonce": challenge.server_nonce,
            "trust_version": 1,
        }
        signature = self.private_key.sign(canonical_proof_bytes(proof))
        return {
            "handlers": [BRIDGE_CONNECTOR_HANDLER],
            "principal": {
                "type": "browser_bridge",
                "proof": proof,
                "signature": base64.urlsafe_b64encode(signature)
                .rstrip(b"=")
                .decode(),
            },
        }


@pytest.fixture
def bridge_session(
    monkeypatch: pytest.MonkeyPatch,
) -> _SessionFixture:
    fixture = _SessionFixture()
    monkeypatch.delenv("A0_BROWSER_BRIDGE_SERVER_BASE_URL", raising=False)
    monkeypatch.setitem(sys.modules, "flask", fixture.flask)
    monkeypatch.setitem(sys.modules, "helpers.runtime", fixture.runtime)
    monkeypatch.setattr(helpers, "runtime", fixture.runtime, raising=False)
    monkeypatch.setattr(
        session,
        "get_browser_bridge_gate",
        lambda: BrowserBridgeGate.from_value(fixture.gate),
    )
    monkeypatch.setattr(
        session,
        "get_browser_bridge_challenge_store",
        lambda: fixture.challenges,
    )
    monkeypatch.setattr(
        session,
        "get_browser_bridge_pairing_store",
        lambda: fixture.pairing,
    )
    monkeypatch.setattr(
        session,
        "configured_extension_id",
        lambda: fixture.extension_id,
    )
    return fixture


@contextmanager
def _request_at(
    bridge_session: _SessionFixture,
    base_url: str = SERVER_BASE_URL,
) -> Iterator[None]:
    previous = bridge_session.flask.request
    bridge_session.flask.request = _Request(base_url)
    try:
        yield
    finally:
        bridge_session.flask.request = previous


def _authenticate(
    bridge_session: _SessionFixture,
    auth: dict[str, Any],
    *,
    base_url: str = SERVER_BASE_URL,
) -> WsPrincipal | None:
    with _request_at(bridge_session, base_url):
        return session.authenticate(auth, handler_id=HANDLER_ID)


def test_real_proof_creates_only_the_immutable_hello_principal(
    bridge_session: _SessionFixture,
) -> None:
    principal = _authenticate(bridge_session, bridge_session.auth())

    assert principal == WsPrincipal(
        principal_type="browser_bridge",
        principal_id=BRIDGE_ID,
        subject_id="single_user",
        scopes=frozenset(FIXED_BROWSER_BRIDGE_SCOPES),
        handler_path=BRIDGE_CONNECTOR_HANDLER,
        handler_id=HANDLER_ID,
        inbound_events=frozenset({"connector_hello"}),
        outbound_events=frozenset(),
        key_generation=1,
    )
    assert isinstance(principal.scopes, frozenset)
    assert isinstance(principal.inbound_events, frozenset)
    assert bridge_session.state["document"]["bridges"][0][
        "last_authenticated_at_ms"
    ] == bridge_session.now
    with pytest.raises(FrozenInstanceError):
        principal.principal_id = "replacement"  # type: ignore[misc]


def test_auth_schema_is_exact_and_rejected_shapes_do_not_consume_proof(
    bridge_session: _SessionFixture,
) -> None:
    auth = bridge_session.auth()
    principal = auth["principal"]
    invalid = [
        {**auth, "api_key": "ambient-authority"},
        {**auth, "handlers": []},
        {**auth, "handlers": [BRIDGE_CONNECTOR_HANDLER, "api/state_sync"]},
        {**auth, "handlers": ["plugins/_a0_connector/other"]},
        {**auth, "principal": None},
        {
            **auth,
            "principal": {
                key: value
                for key, value in principal.items()
                if key != "signature"
            },
        },
        {**auth, "principal": {**principal, "scopes": ["browser.operate"]}},
        {**auth, "principal": {**principal, "type": "webui_session"}},
    ]

    for candidate in invalid:
        assert _authenticate(bridge_session, candidate) is None

    assert _authenticate(bridge_session, auth) is not None


@pytest.mark.parametrize(
    ("current_server_id", "current_extension_id", "request_base_url"),
    [
        ("different-server", EXTENSION_ID, SERVER_BASE_URL),
        (SERVER_ID, OTHER_EXTENSION_ID, SERVER_BASE_URL),
        (SERVER_ID, None, SERVER_BASE_URL),
        (SERVER_ID, EXTENSION_ID, "http://localhost:50081"),
    ],
)
def test_authentication_rechecks_current_server_id_url_and_extension_pin(
    bridge_session: _SessionFixture,
    current_server_id: str,
    current_extension_id: str | None,
    request_base_url: str,
) -> None:
    bridge_session.server_id = current_server_id
    bridge_session.extension_id = current_extension_id

    assert (
        _authenticate(
            bridge_session,
            bridge_session.auth(),
            base_url=request_base_url,
        )
        is None
    )


def test_gate_blocks_before_consumption_and_revalidates_established_principal(
    bridge_session: _SessionFixture,
) -> None:
    auth = bridge_session.auth()
    bridge_session.gate = "disabled"
    assert _authenticate(bridge_session, auth) is None

    bridge_session.gate = "preview"
    principal = _authenticate(bridge_session, auth)
    assert principal is not None
    assert session.is_active(principal) is True

    bridge_session.gate = "disabled"
    assert session.is_active(principal) is False


def test_active_principal_revalidates_server_pin_scopes_and_revocation(
    bridge_session: _SessionFixture,
) -> None:
    principal = _authenticate(bridge_session, bridge_session.auth())
    assert principal is not None
    assert session.is_active(principal) is True

    bridge_session.server_id = "different-server"
    assert session.is_active(principal) is False
    bridge_session.server_id = SERVER_ID

    bridge_session.extension_id = OTHER_EXTENSION_ID
    assert session.is_active(principal) is False
    bridge_session.extension_id = EXTENSION_ID

    wrong_scopes = WsPrincipal(
        principal_type=principal.principal_type,
        principal_id=principal.principal_id,
        subject_id=principal.subject_id,
        scopes=frozenset({"bridge.connect"}),
        handler_path=principal.handler_path,
        handler_id=principal.handler_id,
        inbound_events=principal.inbound_events,
        outbound_events=principal.outbound_events,
        key_generation=principal.key_generation,
    )
    assert session.is_active(wrong_scopes) is False
    assert session.is_active(replace(principal, key_generation=2)) is False
    assert session.is_active(replace(principal, subject_id="different-subject")) is False

    record = bridge_session.state["document"]["bridges"][0]
    record["state"] = "revoked"
    record["revoked_at_ms"] = bridge_session.now + 1
    assert session.is_active(principal) is False


class _PrincipalManager:
    def __init__(self, principal: WsPrincipal) -> None:
        self.principal = principal

    def principal_for_sid(self, namespace: str, sid: str) -> WsPrincipal:
        return self.principal


def test_restricted_connector_hello_ignores_malicious_legacy_authority(
    bridge_session: _SessionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _load_ws_connector(monkeypatch) as ws_connector_module:
        WsConnector = ws_connector_module.WsConnector
    principal = _authenticate(bridge_session, bridge_session.auth())
    assert principal is not None
    sid = "restricted-bridge-sid"
    before_sids = ws_runtime.connected_sids()
    connector = WsConnector(
        None,
        threading.RLock(),
        manager=_PrincipalManager(principal),  # type: ignore[arg-type]
    )
    connector._principal = principal
    connector._principal_sid = sid

    asyncio.run(connector.on_connect(sid))
    response = asyncio.run(
        connector.process(
            "connector_hello",
            {
                "context_id": "victim-context",
                "features": ["remote_file_tree", "code_execution_remote"],
                "exec_config": {"enabled": True},
                "remote_files": {"enabled": True, "write_enabled": True},
                "remote_exec": {"enabled": True},
                "computer_use": {"supported": True, "enabled": True},
                "gateway": {"master_enabled": True, "scopes": {"files": True}},
                "host_browser": {
                    "backend_id": "legacy_cdp",
                    "features": ["evaluate", "raw_cdp"],
                },
            },
            sid,
        )
    )

    assert response == {
        "protocol": CONNECTOR_PROTOCOL,
        "features": [],
        "principal_type": "browser_bridge",
        "connector_session_ready": False,
        "browser_control_ready": False,
        "reason_code": "scoped_runtime_not_available",
    }
    assert ws_runtime.connected_sids() == before_sids
    assert ws_runtime.subscribed_contexts_for_sid(sid) == set()
    assert ws_runtime.host_browser_metadata_for_sid(sid) is None
    assert ws_runtime.remote_file_metadata_for_sid(sid) is None
    assert ws_runtime.remote_exec_metadata_for_sid(sid) is None
    assert ws_runtime.computer_use_metadata_for_sid(sid) is None
    assert ws_runtime.launcher_gateway_metadata_for_sid(sid) is None


class _Request:
    def __init__(self, base_url: str) -> None:
        self.headers = {"Origin": base_url}
        self.script_root = ""
        self.url_root = f"{base_url}/"
        self.remote_addr = "127.0.0.1"


class _PrintStyle:
    @staticmethod
    def debug(_message: str) -> None:
        return None

    @staticmethod
    def error(_message: str) -> None:
        return None


class _WsHandler:
    def __init__(
        self,
        socketio_server: Any,
        lock: Any,
        *,
        manager: Any = None,
        namespace: str = "/ws",
    ) -> None:
        self.socketio = socketio_server
        self.lock = lock
        self._manager = manager
        self._namespace = namespace
        self._principal: WsPrincipal | None = None
        self._principal_sid: str | None = None

    @property
    def identifier(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def manager(self) -> Any:
        return self._manager

    def principal_for_sid(self, _sid: str) -> WsPrincipal | None:
        return self._principal


class _WsResult:
    @classmethod
    def error(cls, *, code: str, message: str, **_kwargs: Any) -> dict[str, str]:
        return {"code": code, "message": message}


@contextmanager
def _load_ws_connector(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[ModuleType]:
    module_name = "plugins._a0_connector.api.ws_connector"
    parent = importlib.import_module("plugins._a0_connector.api")
    previous_attribute = getattr(parent, "ws_connector", None)
    previous = sys.modules.pop(module_name, None)
    print_style_stub = ModuleType("helpers.print_style")
    print_style_stub.PrintStyle = _PrintStyle
    ws_stub = ModuleType("helpers.ws")
    ws_stub.WsHandler = _WsHandler
    ws_manager_stub = ModuleType("helpers.ws_manager")
    ws_manager_stub.WsResult = _WsResult
    try:
        with monkeypatch.context() as context:
            context.setitem(sys.modules, "helpers.print_style", print_style_stub)
            context.setitem(sys.modules, "helpers.ws", ws_stub)
            context.setitem(sys.modules, "helpers.ws_manager", ws_manager_stub)
            yield importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous
        if previous_attribute is None:
            if hasattr(parent, "ws_connector"):
                delattr(parent, "ws_connector")
        else:
            parent.ws_connector = previous_attribute
