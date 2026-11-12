from __future__ import annotations
import asyncio
import base64
import importlib
import io
import json
import sys
import pytest
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Iterator
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from plugins._a0_connector.helpers.browser_bridge_auth import (
    BRIDGE_CONNECTOR_HANDLER,
    CHALLENGE_SOURCE_RATE_MAX,
    CHALLENGE_TTL_MS,
    BrowserBridgeChallengeFailed,
    BrowserBridgeChallengeStore,
    canonical_proof_bytes,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_RECORD_SCHEMA_VERSION,
    BROWSER_BRIDGE_TRUST_CONTRACT,
    CONNECTOR_PROTOCOL,
    FIXED_BROWSER_BRIDGE_SCOPES,
    BrowserBridgePairingStore,
    BrowserBridgeRecordRepository,
    coarse_source_key,
)
from plugins._browser.helpers.bridge_foundation import BrowserBridgeGate
from browser_bridge_test_support import FakeResponse as _FakeResponse


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


BRIDGE_ID = "22222222-2222-4222-8222-222222222222"


SERVER_ID = "server-instance-A"


SERVER_BASE_URL = "http://localhost:50080"


CLIENT_NONCE = base64.urlsafe_b64encode(bytes([3]) * 32).rstrip(b"=").decode()


def _credential() -> tuple[
    BrowserBridgePairingStore,
    dict[str, Any],
    Ed25519PrivateKey,
]:
    state: dict[str, Any] = {}

    def load() -> Any:
        return state.get("document")

    def save(value: dict[str, Any]) -> None:
        state["document"] = value

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
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
            "display_name": "Taylor's browser host",
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
            "created_at_ms": 1_788_492_400_000,
            "last_authenticated_at_ms": None,
            "revoked_at_ms": None,
        }
    )
    return BrowserBridgePairingStore(repository=repository), state, private_key


def _challenge_store(
    pairing: BrowserBridgePairingStore,
    *,
    clock: list[int] | None = None,
) -> tuple[BrowserBridgeChallengeStore, list[int]]:
    now = clock or [1_788_492_445_000]
    identifiers = iter(
        (
            "33333333-3333-4333-8333-333333333333",
            "44444444-4444-4444-8444-444444444444",
            "55555555-5555-4555-8555-555555555555",
        )
    )
    store = BrowserBridgeChallengeStore(
        record_lookup=lambda bridge_id, server_id: pairing.active_bridge_record(
            bridge_id=bridge_id,
            server_instance_id=server_id,
        ),
        record_authenticated=lambda bridge_id, generation, authenticated_at: (
            pairing.mark_bridge_authenticated(
                bridge_id=bridge_id,
                key_generation=generation,
                authenticated_at_ms=authenticated_at,
            )
        ),
        clock_ms=lambda: now[0],
        random_bytes=lambda size: bytes([7]) * size,
        id_factory=lambda: next(identifiers),
    )
    return store, now


def _issue(store: BrowserBridgeChallengeStore):
    return store.issue(
        {
            "trust_version": 1,
            "bridge_id": BRIDGE_ID,
            "client_nonce": CLIENT_NONCE,
        },
        source_key=coarse_source_key("127.0.0.1"),
        server_instance_id=SERVER_ID,
        server_base_url=SERVER_BASE_URL,
    )


def _proof(challenge) -> dict[str, Any]:
    return {
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


def _signature(private_key: Ed25519PrivateKey, proof: dict[str, Any]) -> str:
    signature = private_key.sign(canonical_proof_bytes(proof))
    return base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def test_challenge_is_60_second_memory_only_and_response_is_bounded() -> None:
    pairing, state, _ = _credential()
    store, clock = _challenge_store(pairing)
    before = json.loads(json.dumps(state["document"]))

    challenge = _issue(store)
    public = challenge.as_public_dict()

    assert public == {
        "trust_version": 1,
        "challenge_id": "33333333-3333-4333-8333-333333333333",
        "server_nonce": base64.urlsafe_b64encode(bytes([7]) * 32)
        .rstrip(b"=")
        .decode(),
        "server_instance_id": SERVER_ID,
        "server_base_url": SERVER_BASE_URL,
        "expires_at_ms": clock[0] + CHALLENGE_TTL_MS,
    }
    assert state["document"] == before
    assert CLIENT_NONCE not in repr(store._pending)
    assert public["server_nonce"] not in repr(store._pending)


def test_real_ed25519_proof_is_single_use_and_updates_last_authentication() -> None:
    pairing, state, private_key = _credential()
    store, clock = _challenge_store(pairing)
    challenge = _issue(store)
    proof = _proof(challenge)

    principal = store.verify(proof=proof, signature=_signature(private_key, proof))

    assert principal.as_security_context_dict() == {
        "principal_type": "browser_bridge",
        "bridge_id": BRIDGE_ID,
        "server_instance_id": SERVER_ID,
        "subject_id": "single_user",
        "extension_id": EXTENSION_ID,
        "companion_instance_id": "companion-instance-A",
        "key_generation": 1,
        "scopes": list(FIXED_BROWSER_BRIDGE_SCOPES),
        "authenticated_at_ms": clock[0],
    }
    assert state["document"]["bridges"][0]["last_authenticated_at_ms"] == clock[0]
    with pytest.raises(BrowserBridgeChallengeFailed, match="authentication failed"):
        store.verify(proof=proof, signature=_signature(private_key, proof))


@pytest.mark.parametrize(
    "field_update",
    [
        {"handler": "plugins/_a0_connector/other"},
        {"protocol": "a0-connector.v2"},
        {"aud": "different-server"},
        {"server_base_url": "https://different.example.test"},
        {"trust_version": True},
        {"unexpected": "field"},
    ],
)
def test_first_invalid_proof_attempt_consumes_challenge(
    field_update: dict[str, Any],
) -> None:
    pairing, state, private_key = _credential()
    store, _ = _challenge_store(pairing)
    challenge = _issue(store)
    valid_proof = _proof(challenge)
    invalid_proof = dict(valid_proof)
    invalid_proof.update(field_update)

    with pytest.raises(BrowserBridgeChallengeFailed, match="authentication failed"):
        store.verify(
            proof=invalid_proof,
            signature=_signature(private_key, valid_proof),
        )
    with pytest.raises(BrowserBridgeChallengeFailed, match="authentication failed"):
        store.verify(
            proof=valid_proof,
            signature=_signature(private_key, valid_proof),
        )
    assert state["document"]["bridges"][0]["last_authenticated_at_ms"] is None


def test_wrong_signature_and_expiry_each_consume_or_remove_challenge() -> None:
    pairing, state, private_key = _credential()
    store, clock = _challenge_store(pairing)
    first = _issue(store)
    first_proof = _proof(first)
    wrong_key = Ed25519PrivateKey.generate()

    with pytest.raises(BrowserBridgeChallengeFailed, match="authentication failed"):
        store.verify(proof=first_proof, signature=_signature(wrong_key, first_proof))

    second = _issue(store)
    second_proof = _proof(second)
    clock[0] += CHALLENGE_TTL_MS
    with pytest.raises(BrowserBridgeChallengeFailed, match="authentication failed"):
        store.verify(proof=second_proof, signature=_signature(private_key, second_proof))
    assert state["document"]["bridges"][0]["last_authenticated_at_ms"] is None


def test_challenge_requires_active_exact_server_record_and_bounds_source_rate() -> None:
    pairing, state, _ = _credential()
    store, _ = _challenge_store(pairing)
    invalid = {
        "trust_version": 1,
        "bridge_id": "unknown-bridge",
        "client_nonce": CLIENT_NONCE,
    }

    for _ in range(CHALLENGE_SOURCE_RATE_MAX):
        with pytest.raises(BrowserBridgeChallengeFailed, match="challenge failed"):
            store.issue(
                invalid,
                source_key=coarse_source_key("198.51.100.8"),
                server_instance_id=SERVER_ID,
                server_base_url=SERVER_BASE_URL,
            )
    with pytest.raises(BrowserBridgeChallengeFailed, match="challenge failed"):
        store.issue(
            {
                "trust_version": 1,
                "bridge_id": BRIDGE_ID,
                "client_nonce": CLIENT_NONCE,
            },
            source_key=coarse_source_key("198.51.100.8"),
            server_instance_id=SERVER_ID,
            server_base_url=SERVER_BASE_URL,
        )

    state["document"]["bridges"][0]["state"] = "revoked"
    state["document"]["bridges"][0]["revoked_at_ms"] = 1_788_492_446_000
    with pytest.raises(BrowserBridgeChallengeFailed, match="challenge failed"):
        _issue(store)


def test_canonical_proof_bytes_match_frozen_jcs_order_without_padding() -> None:
    pairing, _, _ = _credential()
    store, _ = _challenge_store(pairing)
    proof = _proof(_issue(store))
    encoded = canonical_proof_bytes(proof)

    assert encoded == json.dumps(
        proof,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert encoded.startswith(b'{"aud":')
    assert b'"trust_version":1}' in encoded


class _FakePublicApiHandler:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False


@contextmanager
def _endpoint_module(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    module_name = "plugins._a0_connector.api.browser_bridge_challenge"
    api_stub = ModuleType("helpers.api")
    api_stub.Request = object
    api_stub.Response = _FakeResponse
    base_stub = ModuleType("plugins._a0_connector.api.v1.base")
    base_stub.PublicConnectorApiHandler = _FakePublicApiHandler
    v1_stub = ModuleType("plugins._a0_connector.api.v1")
    v1_stub.base = base_stub
    runtime_stub = ModuleType("helpers.runtime")
    runtime_stub.get_persistent_id = lambda: SERVER_ID
    previous = sys.modules.pop(module_name, None)
    previous_base = sys.modules.get("plugins._a0_connector.api.v1.base")
    previous_v1 = sys.modules.get("plugins._a0_connector.api.v1")
    try:
        with monkeypatch.context() as context:
            import helpers

            context.setitem(sys.modules, "helpers.api", api_stub)
            context.setitem(sys.modules, "helpers.runtime", runtime_stub)
            # `from helpers import runtime` may use the package attribute when
            # framework integration tests have already imported the real module.
            context.setattr(helpers, "runtime", runtime_stub, raising=False)
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


def test_public_challenge_endpoint_is_generic_no_store_and_unadvertised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pairing, _, _ = _credential()
    challenge_store, _ = _challenge_store(pairing)
    raw = json.dumps(
        {
            "trust_version": 1,
            "bridge_id": BRIDGE_ID,
            "client_nonce": CLIENT_NONCE,
        }
    ).encode()
    request = type(
        "Request",
        (),
        {
            "headers": {"Origin": SERVER_BASE_URL},
            "script_root": "",
            "url_root": f"{SERVER_BASE_URL}/",
            "remote_addr": "127.0.0.1",
            "data": raw,
            "content_length": len(raw),
            "is_json": True,
            "stream": io.BytesIO(raw),
        },
    )()
    with _endpoint_module(monkeypatch) as endpoint:
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_gate",
            lambda: BrowserBridgeGate.from_value("preview"),
        )
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_challenge_store",
            lambda: challenge_store,
        )
        handler = endpoint.BrowserBridgeChallenge(None, None)
        response = asyncio.run(handler.handle_request(request))

        duplicate = b'{"trust_version":1,"bridge_id":"a","bridge_id":"b"}'
        duplicate_request = type(
            "Request",
            (),
            {
                "content_length": len(duplicate),
                "is_json": True,
                "stream": io.BytesIO(duplicate),
            },
        )()
        duplicate_response = asyncio.run(handler.handle_request(duplicate_request))

    assert handler.requires_auth() is False
    assert handler.requires_csrf() is False
    assert response.status == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert set(json.loads(response.response)) == {
        "trust_version",
        "challenge_id",
        "server_nonce",
        "server_instance_id",
        "server_base_url",
        "expires_at_ms",
    }
    assert duplicate_response.status == 400
    assert json.loads(duplicate_response.response) == {
        "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
        "trust_version": 1,
        "error": "bridge_challenge_failed",
    }
    assert duplicate_response.headers["Cache-Control"] == "no-store"


def test_record_store_shape_remains_public_key_only() -> None:
    _, state, _ = _credential()
    assert state["document"]["schema_version"] == BROWSER_BRIDGE_RECORD_SCHEMA_VERSION
    assert "private_key" not in repr(state["document"])
    assert "signature" not in repr(state["document"])
