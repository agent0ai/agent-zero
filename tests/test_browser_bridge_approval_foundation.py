from __future__ import annotations

import asyncio
from dataclasses import replace
import io
import importlib
import json
import threading
from typing import Any

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_approval import (
    BROWSER_BRIDGE_APPROVAL_CONTRACT,
    MAX_APPROVAL_TTL_MS,
    ApprovalConsumeStatus,
    ApprovalDecisionStatus,
    BrowserActionDataClassification,
    BrowserApprovalBinding,
    BrowserApprovalRoute,
    BrowserBridgeApprovalError,
    BrowserBridgeApprovalRepository,
    BrowserBridgeApprovalUnavailable,
    NO_ACTION_DATA_CLASSIFICATION,
    parse_action_data_classification,
)


SERVER_ID = "server-instance-A"
BRIDGE_ID = "22222222-2222-4222-8222-222222222222"
SUBJECT_ID = "single_user"
PARAMETER_HASH = "a" * 64
TARGET_FINGERPRINT = "b" * 64


def _principal() -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=BRIDGE_ID,
        subject_id=SUBJECT_ID,
        scopes=frozenset({"browser.approval", "browser.control"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector",
        inbound_events=frozenset({"connector_browser_approval_decision"}),
        outbound_events=frozenset({"connector_browser_control"}),
        key_generation=1,
    )


def _route(
    *,
    principal: WsPrincipal | None = None,
    action_id: str = "action-A",
    op_id: str = "op-A",
) -> BrowserApprovalRoute:
    return BrowserApprovalRoute(
        server_instance_id=SERVER_ID,
        principal=principal or _principal(),
        connector_sid="sid-A",
        load_generation_id="generation-A",
        context_id="context-A",
        browser_session_id="session-A",
        turn_id="turn-A",
        action_id=action_id,
        op_id=op_id,
        tab_handle="tab-A",
        document_id="document-A",
        document_epoch=1,
    )


def _binding(
    *,
    route: BrowserApprovalRoute | None = None,
    parameter_hash: str = PARAMETER_HASH,
    target_fingerprint: str = TARGET_FINGERPRINT,
    origin: str = "https://example.com",
    action_class: str = "external_side_effect",
    data_classification: BrowserActionDataClassification = (
        NO_ACTION_DATA_CLASSIFICATION
    ),
) -> BrowserApprovalBinding:
    return BrowserApprovalBinding(
        route=route or _route(),
        canonical_parameter_hash=parameter_hash,
        target_fingerprint=target_fingerprint,
        origin=origin,
        action_class=action_class,
        data_classification=data_classification,
    )


def _repository(
    *,
    route_authorizer=None,
    record_active: list[bool] | None = None,
    max_pending_challenges: int = 128,
    max_pending_receipts: int = 128,
) -> tuple[BrowserBridgeApprovalRepository, list[int]]:
    now = [1_788_492_400_000]
    active = record_active or [True]

    def active_record(server_id: str, bridge_id: str) -> dict[str, Any] | None:
        if not active[0] or server_id != SERVER_ID or bridge_id != BRIDGE_ID:
            return None
        return {
            "state": "active",
            "server_instance_id": SERVER_ID,
            "bridge_id": BRIDGE_ID,
            "subject_id": SUBJECT_ID,
            "key_generation": 1,
            "scopes": ["browser.approval", "browser.control"],
        }

    receipts = iter(f"receipt-{index}" for index in range(1, 20))
    return (
        BrowserBridgeApprovalRepository(
            route_authorizer=route_authorizer or (lambda _route: True),
            active_record_loader=active_record,
            server_instance_id_loader=lambda: SERVER_ID,
            clock_ms=lambda: now[0],
            receipt_id_factory=lambda: next(receipts),
            max_pending_challenges=max_pending_challenges,
            max_pending_receipts=max_pending_receipts,
        ),
        now,
    )


def test_binding_accepts_only_consequential_exact_redacted_values() -> None:
    binding = _binding(origin="HTTPS://Example.COM:443/")
    assert binding.origin == "https://example.com"
    assert set(binding.__slots__) == {
        "route",
        "canonical_parameter_hash",
        "target_fingerprint",
        "origin",
        "action_class",
        "data_classification",
    }
    for field_name, value in (
        ("parameter_hash", "A" * 64),
        ("target_fingerprint", "short"),
        ("origin", "https://example.com/path"),
        ("action_class", "observe"),
    ):
        kwargs = {field_name: value}
        with pytest.raises(BrowserBridgeApprovalError):
            _binding(**kwargs)

    text_classification = parse_action_data_classification(
        {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": "c" * 64,
        }
    )
    assert hash(text_classification)
    assert text_classification.as_wire_value()["text_sha256"] == "c" * 64
    typed = _binding(
        action_class="sensitive_input",
        data_classification=text_classification,
    )
    assert typed.data_classification == text_classification
    with pytest.raises(BrowserBridgeApprovalError):
        _binding(data_classification=text_classification)
    for invalid in (
        {"kind": "text", "sensitivity": "sensitive", "text_sha256": "C" * 64},
        {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": "c" * 64,
            "length": 1,
        },
        {"kind": "text", "sensitivity": "public", "text_sha256": "c" * 64},
    ):
        with pytest.raises(BrowserBridgeApprovalError):
            parse_action_data_classification(invalid)


def test_repository_default_route_authority_is_fail_closed() -> None:
    repository = BrowserBridgeApprovalRepository(
        active_record_loader=lambda _server, _bridge: {},
        server_instance_id_loader=lambda: SERVER_ID,
    )
    with pytest.raises(BrowserBridgeApprovalUnavailable):
        repository.register_challenge(
            "challenge-A",
            _binding(),
            timeout_ms=1_000,
        )


def test_repository_rejects_route_for_a_noncurrent_server_instance() -> None:
    repository = BrowserBridgeApprovalRepository(
        route_authorizer=lambda _route: True,
        active_record_loader=lambda _server, _bridge: {
            "state": "active",
            "server_instance_id": SERVER_ID,
            "bridge_id": BRIDGE_ID,
            "subject_id": SUBJECT_ID,
            "key_generation": 1,
            "scopes": ["browser.approval", "browser.control"],
        },
        server_instance_id_loader=lambda: "replacement-server-instance",
    )
    with pytest.raises(BrowserBridgeApprovalUnavailable):
        repository.register_challenge(
            "challenge-A",
            _binding(),
            timeout_ms=1_000,
        )


def test_approval_is_exact_expiring_and_consumed_once() -> None:
    repository, now = _repository()
    binding = _binding()
    challenge = repository.register_challenge(
        "challenge-A",
        binding,
        timeout_ms=30_000,
    )
    assert challenge.expires_at_ms == now[0] + 30_000
    assert repository.register_challenge(
        "challenge-A",
        binding,
        timeout_ms=1,
    ) is challenge

    decision = repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=binding.route,
        surface="webui",
    )
    assert decision.status == ApprovalDecisionStatus.APPROVED
    assert decision.receipt is not None
    assert decision.receipt.approving_surface == "webui"
    assert decision.receipt.expires_at_ms == now[0] + MAX_APPROVAL_TTL_MS
    assert repository.pending_challenge_count == 0
    assert repository.pending_receipt_count == 1
    assert repository.consume(
        decision.receipt.receipt_id,
        binding=binding,
    ) == ApprovalConsumeStatus.CONSUMED
    assert repository.consume(
        decision.receipt.receipt_id,
        binding=binding,
    ) == ApprovalConsumeStatus.ALREADY_CONSUMED
    assert repository.decide(
        "challenge-A",
        choice="decline",
        current_route=binding.route,
        surface="side_panel",
    ).status == ApprovalDecisionStatus.ALREADY_RESOLVED


@pytest.mark.parametrize(
    "changed",
    [
        "principal",
        "connector_sid",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "tab_handle",
        "document_id",
        "document_epoch",
    ],
)
def test_decision_route_mismatch_atomically_denies_challenge(changed: str) -> None:
    repository, _now = _repository()
    binding = _binding()
    repository.register_challenge("challenge-A", binding, timeout_ms=30_000)
    replacement: Any
    if changed == "principal":
        replacement = _principal()
    elif changed == "document_epoch":
        replacement = 2
    else:
        replacement = f"other-{changed}"
    mismatched = replace(binding.route, **{changed: replacement})

    denied = repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=mismatched,
        surface="webui",
    )
    assert denied.status == ApprovalDecisionStatus.INVALIDATED
    assert repository.pending_challenge_count == 0
    assert repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=binding.route,
        surface="webui",
    ).status == ApprovalDecisionStatus.ALREADY_RESOLVED


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("canonical_parameter_hash", "c" * 64),
        ("target_fingerprint", "d" * 64),
        ("origin", "https://other.example"),
        ("action_class", "sensitive_input"),
    ],
)
def test_receipt_binding_mismatch_destroys_authority(
    field_name: str,
    replacement: str,
) -> None:
    repository, _now = _repository()
    binding = _binding()
    repository.register_challenge("challenge-A", binding, timeout_ms=30_000)
    decision = repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=binding.route,
        surface="side_panel",
    )
    assert decision.receipt is not None
    mismatched = replace(binding, **{field_name: replacement})
    assert repository.consume(
        decision.receipt.receipt_id,
        binding=mismatched,
    ) == ApprovalConsumeStatus.INVALIDATED
    assert repository.consume(
        decision.receipt.receipt_id,
        binding=binding,
    ) == ApprovalConsumeStatus.INVALIDATED


def test_receipt_binds_the_complete_type_data_classification() -> None:
    repository, _now = _repository()
    classification = BrowserActionDataClassification(
        "text", "sensitive", "c" * 64
    )
    binding = _binding(
        action_class="sensitive_input",
        data_classification=classification,
    )
    repository.register_challenge("challenge-A", binding, timeout_ms=30_000)
    decision = repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=binding.route,
        surface="webui",
    )
    assert decision.receipt is not None
    assert repository.consume(
        decision.receipt.receipt_id,
        binding=replace(
            binding, data_classification=NO_ACTION_DATA_CLASSIFICATION
        ),
    ) == ApprovalConsumeStatus.INVALIDATED


def test_expiry_active_record_and_route_authority_deny() -> None:
    active = [True]
    current = [True]
    repository, now = _repository(
        route_authorizer=lambda _route: current[0],
        record_active=active,
    )
    binding = _binding()
    with pytest.raises(BrowserBridgeApprovalError):
        repository.register_challenge(
            "challenge-too-long",
            binding,
            timeout_ms=MAX_APPROVAL_TTL_MS + 1,
        )
    repository.register_challenge("challenge-expiring", binding, timeout_ms=10)
    now[0] += 10
    assert repository.decide(
        "challenge-expiring",
        choice="approve_once",
        current_route=binding.route,
        surface="webui",
    ).status == ApprovalDecisionStatus.EXPIRED

    current[0] = False
    with pytest.raises(BrowserBridgeApprovalUnavailable):
        repository.register_challenge(
            "challenge-stale-route",
            replace(binding, route=_route(action_id="action-B", op_id="op-B")),
            timeout_ms=10,
        )
    current[0] = True
    active[0] = False
    with pytest.raises(BrowserBridgeApprovalUnavailable):
        repository.register_challenge(
            "challenge-revoked",
            replace(binding, route=_route(action_id="action-C", op_id="op-C")),
            timeout_ms=10,
        )


def test_receipt_expires_and_live_credential_revocation_blocks_consumption() -> None:
    active = [True]
    repository, now = _repository(record_active=active)
    binding_a = _binding()
    repository.register_challenge("challenge-A", binding_a, timeout_ms=30_000)
    approved_a = repository.decide(
        "challenge-A",
        choice="approve_once",
        current_route=binding_a.route,
        surface="webui",
    )
    assert approved_a.receipt is not None
    now[0] += MAX_APPROVAL_TTL_MS
    assert repository.consume(
        approved_a.receipt.receipt_id,
        binding=binding_a,
    ) == ApprovalConsumeStatus.EXPIRED

    binding_b = _binding(route=_route(action_id="action-B", op_id="op-B"))
    repository.register_challenge("challenge-B", binding_b, timeout_ms=30_000)
    approved_b = repository.decide(
        "challenge-B",
        choice="approve_once",
        current_route=binding_b.route,
        surface="webui",
    )
    assert approved_b.receipt is not None
    active[0] = False
    assert repository.consume(
        approved_b.receipt.receipt_id,
        binding=binding_b,
    ) == ApprovalConsumeStatus.INVALIDATED


def test_lifecycle_invalidation_covers_cancel_turn_disconnect_and_revoke() -> None:
    repository, _now = _repository()
    route_a = _route(action_id="action-A", op_id="op-A")
    route_b = replace(route_a, action_id="action-B", op_id="op-B")
    binding_a = _binding(route=route_a)
    binding_b = _binding(route=route_b, target_fingerprint="c" * 64)

    repository.register_challenge("challenge-A", binding_a, timeout_ms=30_000)
    assert repository.cancel_operation(route_a).challenges == 1

    repository.register_challenge("challenge-B", binding_b, timeout_ms=30_000)
    approved = repository.decide(
        "challenge-B",
        choice="approve_once",
        current_route=route_b,
        surface="webui",
    )
    repository.register_challenge("challenge-A2", binding_a, timeout_ms=30_000)
    summary = repository.finalize_turn(route_a)
    assert summary.challenges == 1
    assert summary.receipts == 1
    assert approved.receipt is not None
    assert repository.consume(
        approved.receipt.receipt_id,
        binding=binding_b,
    ) == ApprovalConsumeStatus.INVALIDATED

    route_c = replace(route_a, turn_id="turn-C", action_id="action-C", op_id="op-C")
    binding_c = _binding(route=route_c, target_fingerprint="d" * 64)
    repository.register_challenge("challenge-C", binding_c, timeout_ms=30_000)
    assert repository.disconnect(
        principal=route_c.principal,
        connector_sid=route_c.connector_sid,
        load_generation_id=route_c.load_generation_id,
    ).challenges == 1

    route_d = replace(route_a, turn_id="turn-D", action_id="action-D", op_id="op-D")
    binding_d = _binding(route=route_d, target_fingerprint="e" * 64)
    repository.register_challenge("challenge-D", binding_d, timeout_ms=30_000)
    assert repository.revoke_bridge(
        server_instance_id=SERVER_ID,
        bridge_id=BRIDGE_ID,
        subject_id=SUBJECT_ID,
    ).challenges == 1


def test_registry_bounds_and_first_concurrent_decision_win() -> None:
    repository, _now = _repository(max_pending_challenges=1)
    binding = _binding()
    repository.register_challenge("challenge-A", binding, timeout_ms=30_000)
    with pytest.raises(BrowserBridgeApprovalUnavailable):
        repository.register_challenge(
            "challenge-B",
            _binding(route=_route(action_id="action-B", op_id="op-B")),
            timeout_ms=30_000,
        )

    results = []

    def decide() -> None:
        results.append(
            repository.decide(
                "challenge-A",
                choice="approve_once",
                current_route=binding.route,
                surface="webui",
            ).status
        )

    threads = [threading.Thread(target=decide) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results.count(ApprovalDecisionStatus.APPROVED) == 1
    assert results.count(ApprovalDecisionStatus.ALREADY_RESOLVED) == 7
    assert repository.pending_receipt_count == 1


def test_uncomposed_approval_api_is_protected_no_store_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_approval as endpoint

    handler = endpoint.BrowserBridgeApproval(None, None)
    response = asyncio.run(
        handler.process(
            {"challenge_id": "challenge-A", "choice": "approve_once"},
            request=None,
        )
    )
    payload = json.loads(response.get_data(as_text=True))
    assert handler.requires_auth() is True
    assert handler.requires_csrf() is True
    assert response.status_code == 409
    assert response.headers["Cache-Control"] == "no-store"
    assert payload["contract"] == BROWSER_BRIDGE_APPROVAL_CONTRACT
    assert set(payload) == {
        "contract",
        "approval_version",
        "browser_control_ready",
        "error",
    }


def test_bridge_decision_apis_reject_non_string_enums_before_state_access():
    endpoints = (
        ("approval", "BrowserBridgeApproval", "choice", {"challenge_id": "challenge-A"}),
        ("policy", "BrowserBridgePolicy", "action", {}),
        ("bridges", "BrowserBridgeBridges", "action", {}),
        ("selection", "BrowserBridgeSelection", "action", {}),
    )
    for suffix, class_name, field, base in endpoints:
        endpoint = importlib.import_module(f"plugins._a0_connector.api.browser_bridge_{suffix}")
        handler = getattr(endpoint, class_name)(None, None)
        for malformed in ([], {}, None, True, 1):
            raw = json.dumps({**base, field: malformed}).encode()
            request = type("Request", (), {"content_length": len(raw), "is_json": True,
                                           "stream": io.BytesIO(raw)})()
            response = asyncio.run(handler.handle_request(request))
            assert response.status_code == 400
            assert response.headers["Cache-Control"] == "no-store"


def test_approval_api_rejects_binding_injection_duplicate_and_oversized_bodies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_approval as endpoint

    authority_calls = []

    class Authority:
        async def decide(self, **kwargs):
            authority_calls.append(kwargs)

    monkeypatch.setattr(
        endpoint,
        "get_browser_bridge_action_authority",
        lambda: Authority(),
    )
    handler = endpoint.BrowserBridgeApproval(None, None)

    injected = asyncio.run(
        handler.process(
            {
                "challenge_id": "challenge-A",
                "choice": "approve_once",
                "origin": "https://evil.example",
            },
            request=None,
        )
    )
    assert injected.status_code == 400
    assert authority_calls == []
    raw = b'{"challenge_id":"challenge-A","choice":"approve_once","choice":"decline"}'
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
    assert authority_calls == []

    oversized = type(
        "Request",
        (),
        {
            "content_length": endpoint.MAX_APPROVAL_REQUEST_BYTES + 1,
            "is_json": True,
            "stream": io.BytesIO(b"{}"),
        },
    )()
    too_large = asyncio.run(handler.handle_request(oversized))
    assert too_large.status_code == 400
    assert authority_calls == []
