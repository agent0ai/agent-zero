from __future__ import annotations
import asyncio
import base64
import importlib
import io
import json
import sys
import threading
import pytest
import helpers
from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
from typing import Any, Iterator
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_INVENTORY_CONTRACT,
    FIXED_BROWSER_BRIDGE_SCOPES,
    BrowserBridgePairingStore,
    BrowserBridgePairingUnavailable,
    BrowserBridgeRecordRepository,
)
from browser_bridge_test_support import FakeResponse as _FakeResponse, FakeApiHandler as _FakeApiHandler


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


PUBLIC_KEY = base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode()


NOW = 1_788_492_500_000


def _record(
    bridge_id: str,
    *,
    server_id: str = "server-A",
    state: str = "active",
    created_at_ms: int = NOW - 10_000,
) -> dict[str, Any]:
    return {
        "trust_version": 1,
        "bridge_id": bridge_id,
        "server_instance_id": server_id,
        "subject_id": "single_user",
        "display_name": f"Browser host {bridge_id[-1]}",
        "companion_instance_id": f"companion-{bridge_id}",
        "extension_id": EXTENSION_ID,
        "public_key": {
            "algorithm": "Ed25519",
            "encoding": "raw-base64url",
            "value": PUBLIC_KEY,
        },
        "key_generation": 1,
        "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
        "state": state,
        "created_at_ms": created_at_ms,
        "last_authenticated_at_ms": created_at_ms + 1_000,
        "revoked_at_ms": created_at_ms + 2_000 if state == "revoked" else None,
    }


def _store(
    records: list[dict[str, Any]],
    *,
    now: list[int] | None = None,
) -> tuple[BrowserBridgePairingStore, dict[str, Any], BrowserBridgeRecordRepository]:
    state: dict[str, Any] = {
        "document": {"schema_version": 1, "bridges": records},
        "saves": 0,
    }

    def load() -> Any:
        return state["document"]

    def save(value: dict[str, Any]) -> None:
        state["saves"] += 1
        state["document"] = value

    repository = BrowserBridgeRecordRepository(load=load, save=save)
    clock = now or [NOW]
    return (
        BrowserBridgePairingStore(repository=repository, clock_ms=lambda: clock[0]),
        state,
        repository,
    )


def test_inventory_is_server_subject_scoped_bounded_and_public_only() -> None:
    store, _, _ = _store(
        [
            _record("bridge-old", created_at_ms=NOW - 20_000),
            _record("bridge-new", state="revoked", created_at_ms=NOW - 5_000),
            _record("bridge-other-server", server_id="server-B", created_at_ms=NOW),
        ]
    )

    records = store.list_bridge_records(
        server_instance_id="server-A",
        subject_id="single_user",
    )
    public = [record.as_public_dict() for record in records]

    assert [record["bridge_id"] for record in public] == ["bridge-new", "bridge-old"]
    assert set(public[0]) == {
        "bridge_id",
        "display_name",
        "state",
        "key_generation",
        "created_at_ms",
        "last_authenticated_at_ms",
        "revoked_at_ms",
    }
    serialized = json.dumps(public)
    for forbidden in (
        "public_key", "private_key", "companion_instance_id", "extension_id",
        "server_instance_id", "subject_id", "scopes", "sid", "http://",
    ):
        assert forbidden not in serialized
    assert store.bridge_record(
        bridge_id="bridge-other-server",
        server_instance_id="server-A",
        subject_id="single_user",
    ) is None


def test_revoke_is_idempotent_durable_and_cannot_be_resurrected_by_auth() -> None:
    now = [NOW]
    store, state, repository = _store([_record("bridge-1")], now=now)
    original_revoke = repository.revoke

    def assert_locked_revoke(**kwargs):
        assert store._lock._is_owned()
        return original_revoke(**kwargs)

    repository.revoke = assert_locked_revoke  # type: ignore[method-assign]
    first = store.revoke_bridge(
        bridge_id="bridge-1",
        server_instance_id="server-A",
        subject_id="single_user",
    )

    assert first is not None
    assert first.already_revoked is False
    assert first.bridge.state == "revoked"
    assert first.bridge.revoked_at_ms == NOW
    assert state["saves"] == 1
    assert store.active_bridge_record(
        bridge_id="bridge-1", server_instance_id="server-A"
    ) is None
    with pytest.raises(BrowserBridgePairingUnavailable):
        store.mark_bridge_authenticated(
            bridge_id="bridge-1",
            key_generation=1,
            authenticated_at_ms=NOW + 1,
        )

    now[0] += 50_000
    repeated = store.revoke_bridge(
        bridge_id="bridge-1",
        server_instance_id="server-A",
        subject_id="single_user",
    )
    assert repeated is not None
    assert repeated.already_revoked is True
    assert repeated.bridge.revoked_at_ms == NOW
    assert state["saves"] == 1
    # Durable trust material remains server-side for revocation history, but is
    # never copied into the public record.
    assert state["document"]["bridges"][0]["public_key"]["value"] == PUBLIC_KEY
    assert "public_key" not in repeated.bridge.as_public_dict()


def test_revoke_serializes_with_an_overlapping_authentication_write() -> None:
    store, state, repository = _store([_record("bridge-1")])
    mark_entered = threading.Event()
    release_mark = threading.Event()
    revoke_started = threading.Event()
    revoke_finished = threading.Event()
    failures: list[BaseException] = []
    original_mark = repository.mark_authenticated

    def blocking_mark(**kwargs):
        mark_entered.set()
        if not release_mark.wait(1):
            raise AssertionError("test did not release authentication write")
        return original_mark(**kwargs)

    repository.mark_authenticated = blocking_mark  # type: ignore[method-assign]

    def authenticate() -> None:
        try:
            store.mark_bridge_authenticated(
                bridge_id="bridge-1",
                key_generation=1,
                authenticated_at_ms=NOW + 1,
            )
        except BaseException as error:
            failures.append(error)

    def revoke() -> None:
        revoke_started.set()
        try:
            store.revoke_bridge(
                bridge_id="bridge-1",
                server_instance_id="server-A",
                subject_id="single_user",
            )
        except BaseException as error:
            failures.append(error)
        finally:
            revoke_finished.set()

    auth_thread = threading.Thread(target=authenticate)
    revoke_thread = threading.Thread(target=revoke)
    auth_thread.start()
    assert mark_entered.wait(1)
    revoke_thread.start()
    assert revoke_started.wait(1)
    assert not revoke_finished.wait(0.05)
    release_mark.set()
    auth_thread.join(1)
    revoke_thread.join(1)

    assert not auth_thread.is_alive()
    assert not revoke_thread.is_alive()
    assert failures == []
    assert state["document"]["bridges"][0]["state"] == "revoked"
    assert state["document"]["bridges"][0]["revoked_at_ms"] == NOW


def test_revoke_is_scoped_and_unknown_bridge_does_not_write() -> None:
    store, state, _ = _store([_record("bridge-1")])

    assert store.revoke_bridge(
        bridge_id="bridge-1",
        server_instance_id="server-B",
        subject_id="single_user",
    ) is None
    assert store.revoke_bridge(
        bridge_id="missing",
        server_instance_id="server-A",
        subject_id="single_user",
    ) is None
    assert state["saves"] == 0
    assert state["document"]["bridges"][0]["state"] == "active"


@pytest.mark.parametrize(
    ("state", "revoked_at_ms"),
    [("active", NOW), ("revoked", None)],
)
def test_inventory_fails_closed_on_inconsistent_revocation_state(
    state: str,
    revoked_at_ms: int | None,
) -> None:
    record = _record("bridge-1")
    record["state"] = state
    record["revoked_at_ms"] = revoked_at_ms
    store, _, _ = _store([record])

    with pytest.raises(BrowserBridgePairingUnavailable):
        store.list_bridge_records(
            server_instance_id="server-A",
            subject_id="single_user",
        )


@contextmanager
def _endpoint_module(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    module_name = "plugins._a0_connector.api.browser_bridge_bridges"
    api_stub = ModuleType("helpers.api")
    api_stub.ApiHandler = _FakeApiHandler
    api_stub.Request = object
    api_stub.Response = _FakeResponse
    runtime_stub = ModuleType("helpers.runtime")
    runtime_stub.get_persistent_id = lambda: "server-A"
    previous = sys.modules.pop(module_name, None)
    previous_runtime = getattr(helpers, "runtime", None)
    try:
        with monkeypatch.context() as context:
            context.setitem(sys.modules, "helpers.api", api_stub)
            context.setitem(sys.modules, "helpers.runtime", runtime_stub)
            context.setattr(helpers, "runtime", runtime_stub, raising=False)
            yield importlib.import_module(module_name)
    finally:
        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous
        if previous_runtime is not None:
            helpers.runtime = previous_runtime


def _request(raw: bytes) -> Any:
    return SimpleNamespace(
        data=raw,
        content_length=len(raw),
        is_json=True,
        stream=io.BytesIO(raw),
    )


def test_endpoint_list_and_detail_are_protected_no_store_and_gate_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _, _ = _store([_record("bridge-1")])
    with _endpoint_module(monkeypatch) as endpoint:
        monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: store)
        handler = endpoint.BrowserBridgeBridges(None, None)
        listed = asyncio.run(handler.process({"action": "list"}, request=None))
        detail = asyncio.run(
            handler.process(
                {"action": "detail", "bridge_id": "bridge-1"},
                request=None,
            )
        )

    listed_payload = json.loads(listed.response)
    detail_payload = json.loads(detail.response)
    assert handler.requires_auth() is True
    assert handler.requires_csrf() is True
    assert listed.headers["Cache-Control"] == "no-store"
    assert listed_payload == {
        "contract": BROWSER_BRIDGE_INVENTORY_CONTRACT,
        "trust_version": 1,
        "browser_control_ready": False,
        "bridges": [detail_payload["bridge"]],
    }
    assert set(detail_payload) == {
        "contract", "trust_version", "browser_control_ready", "bridge"
    }
    assert "get_browser_bridge_gate" not in vars(endpoint)
    assert "configured_extension_id" not in vars(endpoint)


def test_revoke_disconnects_only_matching_restricted_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _, _ = _store([_record("bridge-1"), _record("bridge-2")])
    disconnected: list[tuple[str, str]] = []

    class Socket:
        async def disconnect(self, sid, *, namespace):
            disconnected.append((namespace, sid))

    matching = SimpleNamespace(
        principal=SimpleNamespace(
            principal_type="browser_bridge",
            principal_id="bridge-1",
            subject_id="single_user",
        )
    )
    other_bridge = SimpleNamespace(
        principal=SimpleNamespace(
            principal_type="browser_bridge",
            principal_id="bridge-2",
            subject_id="single_user",
        )
    )
    ordinary = SimpleNamespace(principal=None)
    manager = SimpleNamespace(
        lock=threading.RLock(),
        connections={
            ("/ws", "secret-matching-sid"): matching,
            ("/ws", "secret-other-sid"): other_bridge,
            ("/ws", "secret-ordinary-sid"): ordinary,
        },
        socketio=Socket(),
    )
    ws_stub = ModuleType("helpers.ws_manager")
    ws_stub.get_shared_ws_manager = lambda: manager

    with _endpoint_module(monkeypatch) as endpoint:
        monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: store)
        monkeypatch.setitem(sys.modules, "helpers.ws_manager", ws_stub)
        handler = endpoint.BrowserBridgeBridges(None, None)
        response = asyncio.run(
            handler.process(
                {"action": "revoke", "bridge_id": "bridge-1"},
                request=None,
            )
        )

    payload = json.loads(response.response)
    assert response.status == 200
    assert disconnected == [("/ws", "secret-matching-sid")]
    assert payload == {
        "contract": BROWSER_BRIDGE_INVENTORY_CONTRACT,
        "trust_version": 1,
        "browser_control_ready": False,
        "revoked": True,
        "already_revoked": False,
        "bridge": {
            "bridge_id": "bridge-1",
            "display_name": "Browser host 1",
            "state": "revoked",
            "key_generation": 1,
            "created_at_ms": NOW - 10_000,
            "last_authenticated_at_ms": NOW - 9_000,
            "revoked_at_ms": NOW,
        },
        "server_session_cleanup": "completed",
    }
    serialized = response.response.lower()
    assert "sid" not in serialized
    assert "public_key" not in serialized
    assert "native" not in serialized
    assert "tab" not in serialized


def test_revoke_remains_successful_when_session_cleanup_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, state, _ = _store([_record("bridge-1")])
    ws_stub = ModuleType("helpers.ws_manager")
    ws_stub.get_shared_ws_manager = lambda: (_ for _ in ()).throw(
        RuntimeError("not initialized")
    )

    with _endpoint_module(monkeypatch) as endpoint:
        monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: store)
        monkeypatch.setitem(sys.modules, "helpers.ws_manager", ws_stub)
        handler = endpoint.BrowserBridgeBridges(None, None)
        response = asyncio.run(
            handler.process(
                {"action": "revoke", "bridge_id": "bridge-1"},
                request=None,
            )
        )

    payload = json.loads(response.response)
    assert response.status == 200
    assert payload["revoked"] is True
    assert payload["server_session_cleanup"] == "pending"
    assert state["document"]["bridges"][0]["state"] == "revoked"
    assert state["document"]["bridges"][0]["revoked_at_ms"] == NOW


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"action": "list", "bridge_id": "bridge-1"},
        {"action": "detail"},
        {"action": "revoke", "bridge_id": " bridge-1"},
        {"action": "revoke", "bridge_id": "bridge-1", "server_id": "server-B"},
        {"action": "delete", "bridge_id": "bridge-1"},
    ],
)
def test_endpoint_rejects_nonexact_request_shapes(
    monkeypatch: pytest.MonkeyPatch,
    document: dict[str, Any],
) -> None:
    with _endpoint_module(monkeypatch) as endpoint:
        handler = endpoint.BrowserBridgeBridges(None, None)
        response = asyncio.run(handler.process(document, request=None))

    assert response.status == 400
    assert json.loads(response.response) == {
        "error": "invalid_bridge_inventory_request"
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_endpoint_rejects_duplicate_and_oversized_raw_json_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    duplicate = b'{"action":"list","action":"revoke"}'

    class UnreadableStream(io.BytesIO):
        def read(self, *_args, **_kwargs):
            raise AssertionError("oversized request must fail before stream read")

    oversized = SimpleNamespace(
        data=b"",
        content_length=8 * 1024 + 1,
        is_json=True,
        stream=UnreadableStream(b"secret"),
    )
    with _endpoint_module(monkeypatch) as endpoint:
        handler = endpoint.BrowserBridgeBridges(None, None)
        duplicate_response = asyncio.run(handler.handle_request(_request(duplicate)))
        oversized_response = asyncio.run(handler.handle_request(oversized))

    assert duplicate_response.status == 400
    assert oversized_response.status == 400
