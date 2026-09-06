from __future__ import annotations

import asyncio
import io
import json
import threading
from typing import Any

import pytest

from plugins._a0_connector.helpers.browser_bridge_policy import (
    BROWSER_BRIDGE_POLICY_CONTRACT,
    BrowserBridgePolicyError,
    BrowserBridgePolicyRepository,
    BrowserBridgePolicyUnavailable,
    normalize_site_origin,
)


SERVER_ID = "server-instance-A"
BRIDGE_ID = "22222222-2222-4222-8222-222222222222"
SUBJECT_ID = "single_user"


def _repository() -> tuple[BrowserBridgePolicyRepository, dict[str, Any]]:
    state: dict[str, Any] = {}
    sequence = iter(
        (
            "11111111-1111-4111-8111-111111111111",
            "22222222-2222-4222-8222-222222222222",
            "33333333-3333-4333-8333-333333333333",
        )
    )

    def load() -> Any:
        return state.get("document")

    def save(value: dict[str, Any]) -> None:
        state["document"] = value

    return (
        BrowserBridgePolicyRepository(
            load=load,
            save=save,
            clock_ms=lambda: 1_788_492_400_000,
            id_factory=lambda: next(sequence),
        ),
        state,
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("HTTPS://Example.COM:443/", "https://example.com"),
        ("https://x", "https://x"),
        ("http://localhost:50080", "http://localhost:50080"),
        ("https://bücher.example", "https://xn--bcher-kva.example"),
        ("http://[0:0::1]:80/", "http://[::1]"),
    ],
)
def test_site_origin_normalizes_exact_http_origins(raw: str, expected: str) -> None:
    assert normalize_site_origin(raw) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " https://example.com",
        "ftp://example.com",
        "https://*.example.com",
        "https://user@example.com",
        "https://example.com/path",
        "https://example.com?query=secret",
        "https://example.com#fragment",
        "https://\ud800.example",
        "https://example.com\\@evil.example",
        "https://127.0.0.999",
        "https://0x7f000001",
        "https://017700000001",
        "https://example.123",
        "http://[fe80::1%25en0]",
        "https://example..com",
        "https://-example.com",
        "chrome://settings",
    ],
)
def test_site_origin_rejects_non_origin_and_ambiguous_values(value: str) -> None:
    with pytest.raises(BrowserBridgePolicyError):
        normalize_site_origin(value)


def test_policy_is_default_deny_idempotent_and_exactly_scoped() -> None:
    repository, state = _repository()
    identity = {
        "server_instance_id": SERVER_ID,
        "bridge_id": BRIDGE_ID,
        "subject_id": SUBJECT_ID,
    }
    assert repository.active_grant(**identity, origin="https://example.com") is None
    assert state == {}
    first = repository.allow(**identity, origin="HTTPS://Example.COM:443/")
    repeated = repository.allow(**identity, origin="https://example.com")
    assert repeated == first
    assert first.origin == "https://example.com"
    assert len(state["document"]["grants"]) == 1
    stored = state["document"]["grants"][0]
    assert stored["server_instance_id"] == SERVER_ID
    assert stored["bridge_id"] == BRIDGE_ID
    assert stored["subject_id"] == SUBJECT_ID
    assert repository.active_grant(**identity, origin="https://example.com") == first
    assert repository.list_grants(
        server_instance_id="server-instance-B",
        bridge_id=BRIDGE_ID,
        subject_id=SUBJECT_ID,
    ) == ()

    assert repository.revoke(**identity, origin="https://example.com") is True
    assert repository.revoke(**identity, origin="https://example.com") is False
    assert repository.active_grant(**identity, origin="https://example.com") is None


def test_all_websites_is_explicit_persistent_scoped_and_revocable_without_origin_accumulation():
    repository, state = _repository()
    identity = dict(server_instance_id=SERVER_ID, bridge_id=BRIDGE_ID, subject_id=SUBJECT_ID)
    assert repository.site_mode(**identity) == "ask_per_site"
    repository.set_site_mode(**identity, site_mode="allow_all_websites")
    assert state["document"]["schema_version"] == 2
    loaded = BrowserBridgePolicyRepository(load=lambda: state["document"])
    grant = loaded.active_grant(**identity, origin="https://one.example")
    assert grant.origin == "https://one.example"
    assert grant == loaded.active_grant(**identity, origin="https://one.example")
    assert grant.grant_id != loaded.active_grant(**identity, origin="https://two.example").grant_id
    assert loaded.list_grants(**identity) == ()
    for key in identity:
        assert loaded.active_grant(**{**identity, key: "other"}, origin="https://one.example") is None
    for origin in ("chrome://settings", "file:///private", "https://*.example", "https://u:p@example.com"):
        with pytest.raises(BrowserBridgePolicyError):
            loaded.active_grant(**identity, origin=origin)
    saved = repository.allow(**identity, origin="https://saved.example")
    repository.set_site_mode(**identity, site_mode="ask_per_site")
    assert repository.active_grant(**identity, origin="https://one.example") is None
    assert repository.active_grant(**identity, origin="https://saved.example") == saved
    assert state["document"]["schema_version"] == 1


def test_all_websites_rejects_corruption_and_unconfirmed_writes():
    identity = dict(server_instance_id=SERVER_ID, bridge_id=BRIDGE_ID, subject_id=SUBJECT_ID)
    no_save = BrowserBridgePolicyRepository(load=lambda: None, save=lambda value: None)
    with pytest.raises(BrowserBridgePolicyUnavailable):
        no_save.set_site_mode(**identity, site_mode="allow_all_websites")
    broken = BrowserBridgePolicyRepository(load=lambda: {"schema_version": 2, "grants": [], "all_websites": [True]})
    with pytest.raises(BrowserBridgePolicyUnavailable):
        broken.active_grant(**identity, origin="https://example.com")


def test_protected_all_websites_action_derives_authority_and_readback(monkeypatch):
    from plugins._a0_connector.api import browser_bridge_policy as endpoint
    repository, state = _repository()
    pairing = _PairingStore()
    monkeypatch.setattr(endpoint.runtime, "get_persistent_id", lambda: SERVER_ID)
    monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: pairing)
    monkeypatch.setattr(endpoint, "get_browser_bridge_policy_repository", lambda: repository)
    handler = endpoint.BrowserBridgePolicy(None, None)
    body = {"action": "set_mode", "bridge_id": BRIDGE_ID, "site_mode": "allow_all_websites"}
    response = asyncio.run(handler.process(body, request=None))
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    assert json.loads(response.get_data()) ["site_mode"] == "allow_all_websites"
    assert state["document"]["all_websites"][0]["subject_id"] == SUBJECT_ID
    assert asyncio.run(handler.process({**body, "subject_id": "other"}, request=None)).status_code == 400
    pairing.active = False
    assert asyncio.run(handler.process(body, request=None)).status_code == 409


def test_policy_read_modify_write_is_atomic_for_duplicate_allows() -> None:
    repository, state = _repository()
    grants = []

    def allow() -> None:
        grants.append(
            repository.allow(
                server_instance_id=SERVER_ID,
                bridge_id=BRIDGE_ID,
                subject_id=SUBJECT_ID,
                origin="https://example.com",
            )
        )

    threads = [threading.Thread(target=allow) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(grants) == 8
    assert len({grant.grant_id for grant in grants}) == 1
    assert len(state["document"]["grants"]) == 1


def test_corrupt_or_oversized_policy_store_fails_closed() -> None:
    repository, state = _repository()
    state["document"] = {"schema_version": 1, "grants": [{}]}
    with pytest.raises(BrowserBridgePolicyUnavailable):
        repository.list_grants(
            server_instance_id=SERVER_ID,
            bridge_id=BRIDGE_ID,
            subject_id=SUBJECT_ID,
        )
    with pytest.raises(BrowserBridgePolicyUnavailable):
        repository.allow(
            server_instance_id=SERVER_ID,
            bridge_id=BRIDGE_ID,
            subject_id=SUBJECT_ID,
            origin="https://example.com",
        )


class _PairingStore:
    def __init__(self, *, active: bool = True) -> None:
        self.active = active
        self.calls: list[tuple[str, str]] = []

    def active_bridge_record(
        self,
        *,
        bridge_id: str,
        server_instance_id: str,
    ) -> dict[str, Any] | None:
        self.calls.append((bridge_id, server_instance_id))
        if not self.active or bridge_id != BRIDGE_ID or server_instance_id != SERVER_ID:
            return None
        return {"subject_id": SUBJECT_ID, "state": "active"}


def test_policy_api_is_protected_no_store_and_non_activating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_policy as endpoint

    repository, state = _repository()
    pairing = _PairingStore()
    monkeypatch.setattr(endpoint.runtime, "get_persistent_id", lambda: SERVER_ID)
    monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: pairing)
    monkeypatch.setattr(endpoint, "get_browser_bridge_policy_repository", lambda: repository)
    handler = endpoint.BrowserBridgePolicy(None, None)

    response = asyncio.run(
        handler.process(
            {"action": "allow", "bridge_id": BRIDGE_ID, "origin": "https://example.com/"},
            request=None,
        )
    )
    payload = json.loads(response.get_data(as_text=True))
    assert handler.requires_auth() is True
    assert handler.requires_csrf() is True
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["contract"] == BROWSER_BRIDGE_POLICY_CONTRACT
    assert payload["site_mode"] == "ask_per_site"
    assert payload["operation_grants_enabled"] is False
    assert payload["browser_control_ready"] is False
    assert payload["grants"][0]["origin"] == "https://example.com"
    assert set(payload) == {
        "contract",
        "policy_version",
        "site_mode",
        "bridge_id",
        "grants",
        "operation_grants_enabled",
        "browser_control_ready",
    }
    assert set(payload["grants"][0]) == {
        "grant_id",
        "origin",
        "created_at_ms",
        "updated_at_ms",
    }
    assert pairing.calls == [(BRIDGE_ID, SERVER_ID)]
    assert state["document"]["grants"][0]["subject_id"] == SUBJECT_ID

    listed = asyncio.run(
        handler.process(
            {"action": "list", "bridge_id": BRIDGE_ID},
            request=None,
        )
    )
    assert json.loads(listed.get_data(as_text=True)) == payload

    revoked = asyncio.run(
        handler.process(
            {"action": "revoke", "bridge_id": BRIDGE_ID, "origin": "https://example.com"},
            request=None,
        )
    )
    revoked_payload = json.loads(revoked.get_data(as_text=True))
    assert revoked_payload["revoked"] is True
    assert revoked_payload["grants"] == []
    assert set(revoked_payload) == {*payload, "revoked"}


def test_policy_api_rejects_unknown_bridge_extra_authority_and_duplicate_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_policy as endpoint

    repository, state = _repository()
    pairing = _PairingStore(active=False)
    monkeypatch.setattr(endpoint.runtime, "get_persistent_id", lambda: SERVER_ID)
    monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: pairing)
    monkeypatch.setattr(endpoint, "get_browser_bridge_policy_repository", lambda: repository)
    handler = endpoint.BrowserBridgePolicy(None, None)

    unavailable = asyncio.run(
        handler.process(
            {"action": "allow", "bridge_id": BRIDGE_ID, "origin": "https://example.com"},
            request=None,
        )
    )
    assert unavailable.status_code == 409
    assert state == {}

    extra = asyncio.run(
        handler.process(
            {
                "action": "allow",
                "bridge_id": BRIDGE_ID,
                "origin": "https://example.com",
                "subject_id": "attacker-selected",
            },
            request=None,
        )
    )
    assert extra.status_code == 400

    raw = (
        b'{"action":"allow","bridge_id":"'
        + BRIDGE_ID.encode()
        + b'","origin":"https://example.com","origin":"https://evil.example"}'
    )
    request = type(
        "Request",
        (),
        {
            "content_length": len(raw),
            "is_json": True,
            "stream": io.BytesIO(raw),
        },
    )()
    duplicate = asyncio.run(handler.handle_request(request))
    assert duplicate.status_code == 400
    assert state == {}

    oversized = type(
        "Request",
        (),
        {
            "content_length": endpoint.MAX_POLICY_REQUEST_BYTES + 1,
            "is_json": True,
            "stream": io.BytesIO(b"{}"),
        },
    )()
    too_large = asyncio.run(handler.handle_request(oversized))
    assert too_large.status_code == 400
    assert state == {}


def test_policy_api_fails_closed_when_active_record_has_no_subject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_policy as endpoint

    repository, state = _repository()
    pairing = _PairingStore()
    pairing.active_bridge_record = lambda **_kwargs: {"state": "active"}
    monkeypatch.setattr(endpoint.runtime, "get_persistent_id", lambda: SERVER_ID)
    monkeypatch.setattr(endpoint, "get_browser_bridge_pairing_store", lambda: pairing)
    monkeypatch.setattr(endpoint, "get_browser_bridge_policy_repository", lambda: repository)

    response = asyncio.run(
        endpoint.BrowserBridgePolicy(None, None).process(
            {"action": "allow", "bridge_id": BRIDGE_ID, "origin": "https://example.com"},
            request=None,
        )
    )
    assert response.status_code == 503
    assert state == {}
