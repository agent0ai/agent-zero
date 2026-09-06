from __future__ import annotations
import asyncio
import base64
import importlib
import io
import json
import sys
import threading
import pytest
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Iterator
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_EXTENSION_ID_ENV,
    BROWSER_BRIDGE_TRUST_CONTRACT,
    BROWSER_BRIDGE_TRUST_VERSION,
    FIXED_BROWSER_BRIDGE_SCOPES,
    PAIRING_MAX_FAILED_EXCHANGES,
    PAIRING_TTL_MS,
    BrowserBridgePairingError,
    BrowserBridgePairingExchangeFailed,
    BrowserBridgePairingStore,
    BrowserBridgePairingUnavailable,
    BrowserBridgeRecordRepository,
    build_browser_bridge_pairing_foundation_status,
    coarse_source_key,
    normalize_server_base_url,
    server_base_url_for_request,
)
from plugins._browser.helpers.bridge_foundation import BrowserBridgeGate, build_browser_bridge_status
from browser_bridge_test_support import FakeResponse as _FakeResponse, FakeApiHandler as _FakeApiHandler


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


PUBLIC_KEY = base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode("ascii")


def _repository() -> tuple[BrowserBridgeRecordRepository, dict[str, Any]]:
    state: dict[str, Any] = {}

    def load() -> Any:
        return state.get("document")

    def save(value: dict[str, Any]) -> None:
        state["document"] = value

    return BrowserBridgeRecordRepository(load=load, save=save), state


def _id_factory() -> Any:
    identifiers = iter(
        (
            "11111111-1111-4111-8111-111111111111",
            "22222222-2222-4222-8222-222222222222",
            "33333333-3333-4333-8333-333333333333",
            "44444444-4444-4444-8444-444444444444",
        )
    )
    return lambda: next(identifiers)


def _store(
    *,
    now: list[int] | None = None,
) -> tuple[BrowserBridgePairingStore, dict[str, Any], list[int]]:
    repository, state = _repository()
    clock = now or [1_788_492_400_000]
    store = BrowserBridgePairingStore(
        repository=repository,
        clock_ms=lambda: clock[0],
        random_bytes=lambda length: bytes([7]) * length,
        id_factory=_id_factory(),
    )
    return store, state, clock


def _create(store: BrowserBridgePairingStore, *, owner: str = "session-A"):
    return store.create(
        owner_id=owner,
        server_instance_id="server-instance-A",
        server_base_url="http://localhost:50080",
        extension_id=EXTENSION_ID,
        display_name="Taylor's browser host",
    )


def _exchange(creation, **updates: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "trust_version": 1,
        "pairing_code": creation.pairing_code,
        "server_base_url": "http://localhost:50080",
        "extension_id": EXTENSION_ID,
        "companion_instance_id": "companion-instance-A",
        "public_key": {
            "algorithm": "Ed25519",
            "encoding": "raw-base64url",
            "value": PUBLIC_KEY,
        },
    }
    value.update(updates)
    return value


def test_pairing_code_has_160_bits_is_memory_only_and_status_is_redacted() -> None:
    store, state, clock = _store()
    creation = _create(store)
    public = creation.as_public_dict()

    assert public["contract"] == BROWSER_BRIDGE_TRUST_CONTRACT
    assert public["trust_version"] == BROWSER_BRIDGE_TRUST_VERSION
    assert public["pairing_code"].startswith("A0B1-11111111-")
    assert len(public["pairing_code"].rsplit("-", 1)[1]) == 32
    assert public["expires_at_ms"] - public["created_at_ms"] == PAIRING_TTL_MS
    assert public["native_runtime_location"] == "user_browser_host"
    assert public["docker_install_target"] is False
    assert public["connector_session_ready"] is False
    assert public["browser_control_ready"] is False
    assert creation.pairing_code not in repr(creation)
    assert creation.pairing_code not in repr(store._pending)
    assert state == {}

    status = store.status(owner_id="session-A")
    assert status["state"] == "pairing_pending"
    assert status["pairing_code_present"] is False
    assert "pairing_code" not in status
    assert creation.pairing_code not in repr(status)

    clock[0] += PAIRING_TTL_MS
    assert store.status(owner_id="session-A")["state"] == "unpaired"


def test_creating_second_intent_invalidates_first_for_same_session() -> None:
    store, _, _ = _store()
    first = _create(store)
    second = _create(store)

    with pytest.raises(BrowserBridgePairingExchangeFailed):
        store.exchange(_exchange(first), source_key=coarse_source_key("127.0.0.1"))
    assert store.status(owner_id="session-A")["pairing_id"] == second.pairing_id


def test_exchange_is_single_use_and_persists_only_public_credential_state() -> None:
    store, state, _ = _store()
    creation = _create(store)
    success = store.exchange(
        _exchange(creation),
        source_key=coarse_source_key("192.0.2.20"),
    )
    response = success.as_public_dict()

    assert response["state"] == "paired"
    assert response["server_instance_id"] == "server-instance-A"
    assert response["scopes"] == list(FIXED_BROWSER_BRIDGE_SCOPES)
    assert response["connector_session_ready"] is False
    assert response["browser_control_ready"] is False
    assert "private_key" not in repr(response)
    assert "bearer" not in repr(response).lower()

    stored = state["document"]
    assert stored["schema_version"] == 1
    assert len(stored["bridges"]) == 1
    assert stored["bridges"][0]["public_key"]["value"] == PUBLIC_KEY
    assert creation.pairing_code not in repr(stored)
    assert "private_key" not in repr(stored)

    with pytest.raises(BrowserBridgePairingExchangeFailed):
        store.exchange(
            _exchange(creation),
            source_key=coarse_source_key("192.0.2.20"),
        )
    assert store.status(owner_id="session-A")["state"] == "paired"
    assert store.status(
        owner_id="session-A",
        server_instance_id="different-server-instance",
    )["state"] == "unpaired"


def test_exactly_one_concurrent_exchange_consumes_pairing() -> None:
    store, state, _ = _store()
    creation = _create(store)
    successes: list[str] = []
    failures: list[str] = []

    def exchange() -> None:
        try:
            successes.append(
                store.exchange(
                    _exchange(creation),
                    source_key=coarse_source_key("198.51.100.7"),
                ).bridge_id
            )
        except BrowserBridgePairingExchangeFailed:
            failures.append("pairing_exchange_failed")

    threads = [threading.Thread(target=exchange) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(successes) == 1
    assert failures == ["pairing_exchange_failed"]
    assert len(state["document"]["bridges"]) == 1


def test_five_failed_matching_exchanges_consume_the_intent() -> None:
    store, _, _ = _store()
    creation = _create(store)
    incorrect = creation.pairing_code[:-1] + (
        "0" if creation.pairing_code[-1] != "0" else "1"
    )

    for _ in range(PAIRING_MAX_FAILED_EXCHANGES):
        with pytest.raises(BrowserBridgePairingExchangeFailed):
            store.exchange(
                _exchange(creation, pairing_code=incorrect),
                source_key=coarse_source_key("203.0.113.10"),
            )

    with pytest.raises(BrowserBridgePairingExchangeFailed):
        store.exchange(
            _exchange(creation),
            source_key=coarse_source_key("203.0.113.10"),
        )
    assert store.status(owner_id="session-A")["state"] == "unpaired"


def test_source_exchange_rate_is_bounded_and_failure_remains_generic() -> None:
    store, _, _ = _store()
    creation = _create(store)
    invalid = _exchange(creation, pairing_code="not-a-pairing-code")
    source = coarse_source_key("203.0.113.12")

    for _ in range(20):
        with pytest.raises(
            BrowserBridgePairingExchangeFailed,
            match="pairing exchange failed",
        ):
            store.exchange(invalid, source_key=source)
    with pytest.raises(
        BrowserBridgePairingExchangeFailed,
        match="pairing exchange failed",
    ):
        store.exchange(_exchange(creation), source_key=source)


@pytest.mark.parametrize(
    "updates",
    [
        {"trust_version": True},
        {"server_base_url": "https://different.example.test"},
        {"extension_id": "bcdefghijklmnopabcdefghijklmnopa"},
        {"companion_instance_id": " companion"},
        {"public_key": {"algorithm": "Ed25519", "encoding": "raw-base64url", "value": "x"}},
        {"unexpected": "field"},
    ],
)
def test_exchange_schema_and_identity_mismatches_share_generic_failure(
    updates: dict[str, Any],
) -> None:
    store, _, _ = _store()
    creation = _create(store)
    request = _exchange(creation)
    request.update(updates)

    with pytest.raises(
        BrowserBridgePairingExchangeFailed,
        match="pairing exchange failed",
    ):
        store.exchange(request, source_key=coarse_source_key("203.0.113.11"))


@pytest.mark.parametrize(
    "value",
    [
        "http://agent.example.test",
        "https://user:password@agent.example.test",
        "https://agent.example.test/a0?secret=value",
        "https://agent.example.test/a0#fragment",
        "https://agent.example.test/%2e%2e/private",
        "https://bad_host.example.test",
        "http://localhost:0",
    ],
)
def test_server_base_url_fails_closed_on_unsafe_values(value: str) -> None:
    with pytest.raises(BrowserBridgePairingError):
        normalize_server_base_url(value)


def test_server_url_uses_external_browser_origin_and_supports_docker_loopback() -> None:
    request = type(
        "Request",
        (),
        {
            "headers": {"Origin": "http://localhost:50080"},
            "script_root": "",
            "url_root": "http://localhost:50080/",
        },
    )()

    assert server_base_url_for_request(request, environ={}) == "http://localhost:50080"
    assert normalize_server_base_url("https://agent.example.test/a0/") == (
        "https://agent.example.test/a0"
    )

    mismatched = type(
        "Request",
        (),
        {
            "headers": {"Origin": "https://attacker.example.test"},
            "script_root": "",
            "url_root": "https://agent.example.test/",
        },
    )()
    with pytest.raises(BrowserBridgePairingUnavailable):
        server_base_url_for_request(mismatched, environ={})


@pytest.mark.parametrize("gate", [None, "invalid", "disabled"])
def test_pairing_foundation_is_disabled_by_default(gate: str | None) -> None:
    status = build_browser_bridge_pairing_foundation_status(
        BrowserBridgeGate.from_value(gate),
        environ={BROWSER_BRIDGE_EXTENSION_ID_ENV: EXTENSION_ID},
    )

    assert status["state"] == "disabled"
    assert status["pairing_create_enabled"] is False
    assert status["pairing_exchange_enabled"] is False
    assert status["connector_session_ready"] is False
    assert status["browser_control_ready"] is False


def test_pairing_foundation_requires_server_pinned_extension_id() -> None:
    unavailable = build_browser_bridge_pairing_foundation_status(
        BrowserBridgeGate.from_value("preview"),
        environ={},
    )
    available = build_browser_bridge_pairing_foundation_status(
        BrowserBridgeGate.from_value("preview"),
        environ={BROWSER_BRIDGE_EXTENSION_ID_ENV: EXTENSION_ID},
    )

    assert unavailable["state"] == "disabled"
    assert unavailable["reason_code"] == "expected_extension_id_not_configured"
    assert available["state"] == "available"
    assert available["pairing_create_enabled"] is True
    assert available["connector_session_ready"] is False


def test_browser_status_adds_trust_foundation_without_runtime_claims(monkeypatch) -> None:
    monkeypatch.setenv(BROWSER_BRIDGE_EXTENSION_ID_ENV, EXTENSION_ID)
    status = build_browser_bridge_status(
        None,
        BrowserBridgeGate.from_value("preview"),
        checked_at="2026-09-04T12:00:00Z",
    )

    assert status["trust"]["contract"] == BROWSER_BRIDGE_TRUST_CONTRACT
    assert status["trust"]["state"] == "available"
    assert status["trust"]["connector_session_ready"] is False
    assert status["trust"]["browser_control_ready"] is False
    assert EXTENSION_ID not in repr(status["trust"])


class _FakePublicApiHandler(_FakeApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False


@contextmanager
def _endpoint_module(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> Iterator[ModuleType]:
    api_stub = ModuleType("helpers.api")
    api_stub.ApiHandler = _FakeApiHandler
    api_stub.Request = object
    api_stub.Response = _FakeResponse
    api_stub.session = {}
    base_stub = ModuleType("plugins._a0_connector.api.v1.base")
    base_stub.PublicConnectorApiHandler = _FakePublicApiHandler
    v1_stub = ModuleType("plugins._a0_connector.api.v1")
    v1_stub.base = base_stub
    runtime_stub = ModuleType("helpers.runtime")
    runtime_stub.get_persistent_id = lambda: "server-A"
    previous = sys.modules.pop(module_name, None)
    previous_base = sys.modules.get("plugins._a0_connector.api.v1.base")
    previous_v1 = sys.modules.get("plugins._a0_connector.api.v1")
    try:
        with monkeypatch.context() as context:
            context.setitem(sys.modules, "helpers.api", api_stub)
            context.setitem(sys.modules, "helpers.runtime", runtime_stub)
            context.setitem(sys.modules, "plugins._a0_connector.api.v1", v1_stub)
            context.setitem(sys.modules, "plugins._a0_connector.api.v1.base", base_stub)
            yield importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous
        if previous_base is not None:
            sys.modules["plugins._a0_connector.api.v1.base"] = previous_base
        if previous_v1 is not None:
            sys.modules["plugins._a0_connector.api.v1"] = previous_v1


def test_pairing_endpoint_keeps_default_auth_csrf_and_no_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "plugins._a0_connector.api.browser_bridge_pairing"
    store, _, _ = _store()
    request = type(
        "Request",
        (),
        {
            "headers": {"Origin": "http://localhost:50080"},
            "script_root": "",
            "url_root": "http://localhost:50080/",
            "data": b"",
            "content_length": 0,
            "is_json": True,
        },
    )()
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        monkeypatch.setenv(BROWSER_BRIDGE_EXTENSION_ID_ENV, EXTENSION_ID)
        monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: store)
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_gate",
            lambda: BrowserBridgeGate.from_value("preview"),
        )
        monkeypatch.setattr(endpoint, "configured_extension_id", lambda: EXTENSION_ID)
        monkeypatch.setattr(endpoint.runtime, "get_persistent_id", lambda: "server-A")
        handler = endpoint.BrowserBridgePairing(None, None)
        response = asyncio.run(
            handler.process(
                {"action": "create", "display_name": "Browser host"},
                request,
            )
        )

    payload = json.loads(response.response)
    assert handler.requires_auth() is True
    assert handler.requires_csrf() is True
    assert response.status == 201
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["state"] == "pairing_pending"
    assert payload["connector_session_ready"] is False


@pytest.mark.parametrize(
    "document",
    [
        {"action": "create", "display_name": " Browser host"},
        {"action": "create", "display_name": "x" * 193},
        {"action": "cancel", "pairing_id": " pairing-id"},
    ],
)
def test_pairing_endpoint_rejects_malformed_presentation_values(
    monkeypatch: pytest.MonkeyPatch,
    document: dict[str, Any],
) -> None:
    module_name = "plugins._a0_connector.api.browser_bridge_pairing"
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        handler = endpoint.BrowserBridgePairing(None, None)
        response = asyncio.run(handler.process(document, request=None))

    assert response.status == 400
    assert json.loads(response.response) == {"error": "invalid_pairing_request"}
    assert response.headers["Cache-Control"] == "no-store"


def test_public_exchange_endpoint_has_no_ambient_auth_and_generic_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "plugins._a0_connector.api.browser_bridge_exchange"
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_gate",
            lambda: BrowserBridgeGate.from_value("preview"),
        )
        monkeypatch.setattr(endpoint, "configured_extension_id", lambda: EXTENSION_ID)
        handler = endpoint.BrowserBridgeExchange(None, None)
        response = asyncio.run(handler.process({}, request=None))

    payload = json.loads(response.response)
    assert handler.requires_auth() is False
    assert handler.requires_csrf() is False
    assert response.status == 400
    assert payload == {
        "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
        "trust_version": 1,
        "error": "pairing_exchange_failed",
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_public_exchange_endpoint_accepts_only_the_frozen_pairing_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "plugins._a0_connector.api.browser_bridge_exchange"
    store, state, _ = _store()
    creation = _create(store)
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_gate",
            lambda: BrowserBridgeGate.from_value("preview"),
        )
        monkeypatch.setattr(endpoint, "configured_extension_id", lambda: EXTENSION_ID)
        monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: store)
        handler = endpoint.BrowserBridgeExchange(None, None)
        response = asyncio.run(handler.process(_exchange(creation), request=None))

    payload = json.loads(response.response)
    assert response.status == 200
    assert payload["contract"] == BROWSER_BRIDGE_TRUST_CONTRACT
    assert payload["state"] == "paired"
    assert payload["server_base_url"] == "http://localhost:50080"
    assert payload["scopes"] == list(FIXED_BROWSER_BRIDGE_SCOPES)
    assert payload["native_runtime_location"] == "user_browser_host"
    assert payload["docker_install_target"] is False
    assert payload["connector_session_ready"] is False
    assert payload["browser_control_ready"] is False
    assert response.headers["Cache-Control"] == "no-store"
    assert creation.pairing_code not in response.response
    assert creation.pairing_code not in repr(state["document"])


def test_public_exchange_rejects_oversized_body_before_reading_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_name = "plugins._a0_connector.api.browser_bridge_exchange"

    class UnreadableStream(io.BytesIO):
        def read(self, *args, **kwargs):
            raise AssertionError("oversized body must be rejected before reading")

    request = type(
        "Request",
        (),
        {
            "content_length": 8 * 1024 + 1,
            "is_json": True,
            "stream": UnreadableStream(b"secret"),
        },
    )()
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        handler = endpoint.BrowserBridgeExchange(None, None)
        response = asyncio.run(handler.handle_request(request))

    assert response.status == 400
    assert json.loads(response.response)["error"] == "pairing_exchange_failed"
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    ("module_name", "raw_body", "expected_error"),
    [
        (
            "plugins._a0_connector.api.browser_bridge_pairing",
            b'{"action":"status","action":"create"}',
            "invalid_pairing_request",
        ),
        (
            "plugins._a0_connector.api.browser_bridge_exchange",
            b'{"trust_version":1,"public_key":{"algorithm":"Ed25519",'
            b'"algorithm":"Ed25519"}}',
            "pairing_exchange_failed",
        ),
    ],
)
def test_pairing_endpoints_reject_duplicate_json_object_keys(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    raw_body: bytes,
    expected_error: str,
) -> None:
    request = type(
        "Request",
        (),
        {
            "content_length": len(raw_body),
            "is_json": True,
            "stream": io.BytesIO(raw_body),
        },
    )()
    with _endpoint_module(monkeypatch, module_name) as endpoint:
        handler_class = (
            endpoint.BrowserBridgePairing
            if module_name.endswith("browser_bridge_pairing")
            else endpoint.BrowserBridgeExchange
        )
        response = asyncio.run(handler_class(None, None).handle_request(request))

    assert response.status == 400
    assert json.loads(response.response)["error"] == expected_error
    assert response.headers["Cache-Control"] == "no-store"
