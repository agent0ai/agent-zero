"""Real Ed25519 rotation with synthetic public-record persistence only."""
import base64
import copy
import asyncio
import threading
from dataclasses import replace
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from plugins._a0_connector.helpers.browser_bridge_credentials import BrowserBridgeCredentialStore, ROTATION_TTL_MS
from plugins._a0_connector.helpers.browser_bridge_pairing import BrowserBridgePairingUnavailable
from plugins._a0_connector.helpers.browser_bridge_auth import BrowserBridgeChallengeStore, BrowserBridgeChallengeFailed
from plugins._a0_connector.helpers import browser_bridge_auth
from plugins._a0_connector.helpers.browser_bridge_credential_control import BrowserBridgeCredentialController
from plugins._a0_connector.helpers.browser_bridge_context import BrowserBridgeContextRoute
from plugins._a0_connector.helpers.browser_bridge_runtime import BrowserBridgeRuntimeDenied
from test_browser_bridge_challenge_foundation import _credential, _issue, _proof, _signature, BRIDGE_ID, SERVER_ID
from test_browser_bridge_runtime_foundation import _principal


def setup_rotation():
    pairing, state, old = _credential()
    now = [1000]
    pairing._clock_ms = lambda: now[0]
    owner = BrowserBridgeCredentialStore(pairing)
    new = Ed25519PrivateKey.generate()
    public = {"algorithm":"Ed25519","encoding":"raw-base64url","value":base64.urlsafe_b64encode(
        new.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).rstrip(b"=").decode()}
    args = dict(bridge_id=BRIDGE_ID, server_id=SERVER_ID, subject_id="single_user", key_generation=1,
                rotation_id="rotation-1", public_key=public)
    return pairing, owner, state, now, old, new, args


def challenge_owner(pairing, owner, now):
    return BrowserBridgeChallengeStore(
        record_lookup=lambda bridge, server: pairing.active_bridge_record(bridge_id=bridge,server_instance_id=server),
        record_candidates=owner.authentication_records, record_verified=owner.accept_verified_key,
        clock_ms=lambda:now[0])


def test_rotation_keeps_old_key_until_exact_fresh_proof_and_survives_reconstruction():
    pairing, owner, state, now, old, new, args = setup_rotation()
    original = copy.deepcopy(state)
    pending = owner.begin(**args)
    assert pending["status"] == "pending"
    assert owner.begin(**args) == pending
    assert state["document"]["bridges"][0]["public_key"] == original["document"]["bridges"][0]["public_key"]
    auth = challenge_owner(pairing, BrowserBridgeCredentialStore(pairing), now)
    proof = _proof(_issue(auth))
    assert auth.verify(proof=proof, signature=_signature(old, proof)).key_generation == 1
    proof = _proof(_issue(auth))
    assert auth.verify(proof=proof, signature=_signature(new, proof)).key_generation == 2
    record = pairing.active_bridge_record(bridge_id=BRIDGE_ID, server_instance_id=SERVER_ID)
    assert record["rotation"]["status"] == "active"
    assert record["public_key"] == args["public_key"]
    assert record["scopes"] == original["document"]["bridges"][0]["scopes"]
    with pytest.raises(BrowserBridgePairingUnavailable):
        owner.self_revoke(bridge_id=BRIDGE_ID, server_id=SERVER_ID, subject_id="single_user", key_generation=1)
    proof = _proof(_issue(auth))
    with pytest.raises(BrowserBridgeChallengeFailed):
        auth.verify(proof=proof, signature=_signature(old, proof))


def test_pending_expiry_bad_proof_and_changed_payload_leave_old_key_active():
    pairing, owner, state, now, old, new, args = setup_rotation()
    owner.begin(**args)
    with pytest.raises(BrowserBridgePairingUnavailable):
        owner.begin(**{**args,"public_key":state["document"]["bridges"][0]["public_key"]})
    auth = challenge_owner(pairing, owner, now)
    proof = _proof(_issue(auth))
    with pytest.raises(BrowserBridgeChallengeFailed):
        auth.verify(proof=proof, signature=_signature(Ed25519PrivateKey.generate(), proof))
    now[0] += ROTATION_TTL_MS
    assert owner.begin(**args)["status"] == "expired"
    proof = _proof(_issue(auth))
    with pytest.raises(BrowserBridgeChallengeFailed):
        auth.verify(proof=proof, signature=_signature(new, proof))
    proof = _proof(_issue(auth))
    assert auth.verify(proof=proof, signature=_signature(old, proof)).key_generation == 1


def test_verified_pending_key_cannot_promote_replacement_or_resurrect_revocation():
    pairing, owner, state, now, old, new, args = setup_rotation()
    owner.begin(**args)
    verified = owner.authentication_records(BRIDGE_ID, SERVER_ID)[1]
    now[0] += ROTATION_TTL_MS
    owner.begin(**{**args,"rotation_id":"rotation-2"})
    with pytest.raises(BrowserBridgePairingUnavailable):
        owner.accept_verified_key(verified, now[0])
    verified = owner.authentication_records(BRIDGE_ID, SERVER_ID)[1]
    pairing.revoke_bridge(bridge_id=BRIDGE_ID, server_instance_id=SERVER_ID, subject_id="single_user")
    assert owner.authentication_records(BRIDGE_ID, SERVER_ID) == ()
    assert "rotation" not in state["document"]["bridges"][0]
    with pytest.raises(BrowserBridgePairingUnavailable):
        owner.accept_verified_key(verified, now[0])


def test_failed_public_key_commit_never_returns_authenticated_principal():
    pairing, owner, state, now, old, new, args = setup_rotation()
    owner.begin(**args)
    before = copy.deepcopy(state)
    def unavailable(_):
        raise OSError("synthetic storage failure")
    pairing._repository._save = unavailable
    auth = challenge_owner(pairing, owner, now)
    proof = _proof(_issue(auth))
    with pytest.raises(BrowserBridgeChallengeFailed):
        auth.verify(proof=proof, signature=_signature(new, proof))
    assert state == before


@pytest.mark.parametrize("notification_fails", [False, True])
def test_self_revoke_survives_caller_cancellation_and_disconnects_only_its_subject(monkeypatch, notification_fails):
    async def scenario():
        pairing, credentials, state, now, old, new, args = setup_rotation()
        credentials.begin(**args)
        auth = challenge_owner(pairing, credentials, now)
        proof = _proof(_issue(auth))
        monkeypatch.setattr(browser_bridge_auth, "get_browser_bridge_challenge_store", lambda: auth)
        principal = _principal(BRIDGE_ID)
        route = BrowserBridgeContextRoute(principal, "sid-current", "load-current")
        started, release = asyncio.Event(), asyncio.Event()
        retired, disconnected = [], []

        async def emit(namespace, sid, event, data, **kwargs):
            assert credentials.authentication_records(BRIDGE_ID, SERVER_ID) == ()
            assert retired == [BRIDGE_ID]
            assert (namespace, sid, event) == ("/ws", "sid-current", "connector_bridge_credential_status")
            assert data == {"contract_version": 1, "action": "revoke", "rotation_id": None,
                            "key_generation": 1, "status": "revoked", "expires_at_ms": None}
            assert kwargs == {"handler_id": principal.handler_id, "expected_principal": principal}
            started.set()
            await release.wait()
            if notification_fails:
                raise OSError("synthetic notification loss")

        async def disconnect(sid, *, namespace):
            disconnected.append((namespace, sid))

        manager = SimpleNamespace(
            lock=threading.RLock(), emit_to=emit, socketio=SimpleNamespace(disconnect=disconnect),
            connections={
                ("/ws", sid): SimpleNamespace(principal=peer)
                for sid, peer in [
                    ("sid-current", principal), ("sid-same-subject", replace(principal)),
                    ("sid-other-subject", replace(principal, subject_id="another-user")),
                    ("sid-other-bridge", _principal("another-bridge")), ("sid-legacy", None),
                ]
            },
        )
        controller = BrowserBridgeCredentialController(
            manager=manager, current=lambda candidate: candidate is route,
            server_instance_id=lambda: SERVER_ID, retire_bridge=retired.append, credentials=credentials,
        )
        task = asyncio.create_task(controller.dispatch(route, {"contract_version": 1, "action": "revoke"}))
        try:
            await asyncio.wait_for(started.wait(), timeout=1)
            assert state["document"]["bridges"][0]["state"] == "revoked"
            assert "rotation" not in state["document"]["bridges"][0]
            with pytest.raises(BrowserBridgeChallengeFailed):
                auth.verify(proof=proof, signature=_signature(old, proof))
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            release.set()
            await controller.close()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert set(disconnected) == {("/ws", "sid-current"), ("/ws", "sid-same-subject")}
        assert credentials.authentication_records(BRIDGE_ID, SERVER_ID) == ()

    asyncio.run(scenario())


@pytest.mark.parametrize("denial", ["stale_route", "missing_scope"])
def test_self_revoke_denied_route_cannot_change_credentials(denial):
    pairing, credentials, state, now, old, new, args = setup_rotation()
    before = copy.deepcopy(state)
    principal = _principal(BRIDGE_ID)
    if denial == "missing_scope":
        principal = replace(principal, scopes=principal.scopes - {"bridge.connect"})
    route = BrowserBridgeContextRoute(principal, "sid-current", "load-current")
    retired = []
    controller = BrowserBridgeCredentialController(
        manager=None, current=lambda _: denial != "stale_route",
        server_instance_id=lambda: SERVER_ID, retire_bridge=retired.append, credentials=credentials,
    )
    with pytest.raises(BrowserBridgeRuntimeDenied):
        asyncio.run(controller.dispatch(route, {"contract_version": 1, "action": "revoke"}))
    assert state == before
    assert retired == []
