from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace
import base64
import json
import threading
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from plugins._a0_connector.helpers import browser_bridge_release_policy as policy
from plugins._a0_connector.helpers import browser_bridge_runtime_owner as owner_module
from plugins._a0_connector.helpers.browser_bridge_runtime import normalize_bridge_hello
from test_browser_bridge_runtime_foundation import _principal, _active, _hello


def _signed_policy(monkeypatch):
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setattr(policy, "TRUSTED_RELEASE_KEYS", {"test-root": base64.b64encode(public).decode()})
    principal = _principal()
    hello = normalize_bridge_hello(principal, _active(principal), _hello(principal))
    payload = {
        "contract": policy.POLICY_CONTRACT, "issued_at_ms": 1000,
        "expires_at_ms": 100000,
        "releases": [{key: getattr(hello, key) for key in policy._ENTRY_FIELDS}],
    }
    signed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    envelope = {"key_id": "test-root", "policy": payload,
                "signature": base64.b64encode(private.sign(signed)).decode()}
    return envelope


def test_release_policy_verifies_real_signature_and_rejects_tamper_expiry_unknown_root(monkeypatch):
    envelope = _signed_policy(monkeypatch)
    raw = json.dumps(envelope).encode()
    assert len(policy.verify_policy_document(raw, now_ms=2000)) == 1
    with pytest.raises(ValueError):
        policy.verify_policy_document(raw, now_ms=100000)
    envelope["policy"]["releases"][0]["companion_version"] = "2.13.0"
    with pytest.raises(Exception):
        policy.verify_policy_document(json.dumps(envelope).encode(), now_ms=2000)
    monkeypatch.setattr(policy, "TRUSTED_RELEASE_KEYS", {})
    with pytest.raises(ValueError):
        policy.verify_policy_document(raw, now_ms=2000)


def test_release_policy_rejects_duplicate_keys_and_symlink(monkeypatch, tmp_path):
    envelope = _signed_policy(monkeypatch)
    raw = json.dumps(envelope).encode()
    duplicate = raw.replace(b'"key_id": "test-root"', b'"key_id": "test-root", "key_id": "test-root"')
    with pytest.raises(ValueError):
        policy.verify_policy_document(duplicate, now_ms=2000)
    target = tmp_path / "policy.json"
    target.write_bytes(raw)
    link = tmp_path / "alias.json"
    link.symlink_to(target)
    monkeypatch.setenv(policy.POLICY_ENV, str(link))
    with pytest.raises(OSError):
        policy._read_owned_policy()


def test_release_policy_pins_only_genuine_publisher_and_rejects_fixture_signatures():
    assert dict(policy.TRUSTED_RELEASE_KEYS) == {
        "publisher-2026": "GEOygP0rBYlVYZEx+bgDhUZ3sVpfVyedoI9Jo+bcYII="}
    with pytest.raises(TypeError):
        policy.TRUSTED_RELEASE_KEYS["fixture"] = "not-a-root"
    payload = {"contract": policy.POLICY_CONTRACT, "issued_at_ms": 1000,
               "expires_at_ms": 100000, "releases": [{
                   "extension_id": "nhliclifilepdkoolioacpjpijomfplj",
                   "extension_version": "0.1.0", "companion_version": "2.12.0",
                   "companion_platform": "darwin", "companion_arch": "aarch64"}]}
    fixture = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    signature = base64.b64encode(fixture.sign(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())).decode()
    for key_id in ("publisher-2026", "test-root", "development", "fixture"):
        envelope = {"key_id": key_id, "policy": payload, "signature": signature}
        with pytest.raises(Exception):
            policy.verify_policy_document(json.dumps(envelope).encode(), now_ms=2000)


def test_release_policy_supports_exact_both_mac_runtime_slices_without_schema_relaxation(monkeypatch):
    envelope = _signed_policy(monkeypatch)  # Test-only root; never publisher signing.
    entry = {"extension_id": "nhliclifilepdkoolioacpjpijomfplj", "extension_version": "0.1.0",
             "companion_version": "2.12.0", "companion_platform": "darwin", "companion_arch": "aarch64"}
    payload = envelope["policy"]
    payload["releases"] = [entry, {**entry, "companion_arch": "x86_64"}]
    fixture = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))

    def encoded():
        envelope["signature"] = base64.b64encode(fixture.sign(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())).decode()
        return json.dumps(envelope).encode()

    assert [row["companion_arch"] for row in policy.verify_policy_document(encoded(), now_ms=2000)] == ["aarch64", "x86_64"]
    payload["releases"].append(dict(entry))
    with pytest.raises(ValueError):
        policy.verify_policy_document(encoded(), now_ms=2000)
    payload["releases"].pop()
    payload["releases"][0]["companion_version"] = "2.12.0-dev"
    with pytest.raises(ValueError):
        policy.verify_policy_document(encoded(), now_ms=2000)
    payload["releases"][0]["companion_version"] = "2.12.0"
    payload["platforms"] = ["macos"]
    with pytest.raises(ValueError):
        policy.verify_policy_document(encoded(), now_ms=2000)


def test_owner_admission_rechecks_release_activity_selection_and_missing_transport(monkeypatch):
    principal = _principal()
    active = _active(principal)
    hello = normalize_bridge_hello(principal, active, _hello(principal))
    owner = object.__new__(owner_module.BrowserBridgeRuntimeOwner)
    owner._closed = False
    connection = SimpleNamespace(principal=principal, last_activity=datetime.now(timezone.utc))
    owner.manager = SimpleNamespace(
        lock=threading.RLock(), connections={("/ws", "sid-A"): connection},
        principal_for_sid=lambda namespace, sid: principal,
    )
    owner.application = SimpleNamespace(installed=True, runtime_boundaries=lambda: owner_module.REQUIRED_BOUNDARIES)
    owner.verify_principal = lambda candidate: active if candidate is principal else None
    owner._selected = lambda bridge: True
    evidence = owner_module.VerifiedBrowserRelease(
        principal=principal, server_instance_id=active.server_instance_id,
        connector_sid="sid-A", load_generation_id=hello.load_generation_id,
        install_instance_id=hello.install_instance_id,
        **{key: getattr(hello, key) for key in policy._ENTRY_FIELDS},
    )
    owner._release_verifier = lambda *_args: evidence
    monkeypatch.setattr(owner_module, "configured_extension_id", lambda: active.extension_id)
    monkeypatch.setattr(owner_module, "get_browser_bridge_gate", lambda: SimpleNamespace(state="available"))
    monkeypatch.setattr(owner_module, "detect_installed_legacy_browser_bridge", lambda: SimpleNamespace(state=owner_module.LegacyDetectionState.ABSENT))
    admitted = owner.evaluate_admission(active, "sid-A", hello)
    assert admitted is not None
    assert admitted.activation.expires_at_ms - admitted.activation.issued_at_ms == 30000
    owner._release_verifier = lambda *_args: replace(evidence, connector_sid="other")
    assert owner.evaluate_admission(active, "sid-A", hello) is None
    owner._release_verifier = lambda *_args: evidence
    connection.last_activity = datetime.fromtimestamp(time.time() - 31, timezone.utc)
    assert owner.evaluate_admission(active, "sid-A", hello) is None
    connection.last_activity = datetime.now(timezone.utc)
    owner._selected = lambda bridge: False
    assert owner.evaluate_admission(active, "sid-A", hello) is None
    owner._selected = lambda bridge: True
    owner.application.runtime_boundaries = lambda: owner_module.REQUIRED_BOUNDARIES - {"artifact"}
    assert owner.evaluate_admission(active, "sid-A", hello) is None


def test_normal_startup_remains_inert_without_gate_and_never_supplies_fake_release(monkeypatch):
    monkeypatch.setattr(owner_module, "get_browser_bridge_gate", lambda: SimpleNamespace(state="disabled"))
    assert owner_module.install_configured_browser_runtime(object()) is False
    with pytest.raises(TypeError):
        owner_module.configure_verified_browser_releases(None)


def test_admission_heartbeat_snapshot_cannot_precede_concurrent_authenticated_activity(monkeypatch):
    principal = _principal()
    active = _active(principal)
    hello = normalize_bridge_hello(principal, active, _hello(principal))
    owner = object.__new__(owner_module.BrowserBridgeRuntimeOwner)
    owner._closed = False
    now = [2_000_000]
    connection = SimpleNamespace(principal=principal, last_activity=datetime.fromtimestamp(now[0] / 1000, timezone.utc))
    owner.manager = SimpleNamespace(lock=threading.RLock(), connections={("/ws", "sid-A"): connection},
                                    principal_for_sid=lambda namespace, sid: principal)
    owner.application = SimpleNamespace(installed=True, runtime_boundaries=lambda: owner_module.REQUIRED_BOUNDARIES)
    def verify(candidate):
        # Another authenticated receive can advance activity after admission
        # starts but before it acquires the manager's heartbeat snapshot lock.
        with owner.manager.lock:
            now[0] += 11
            connection.last_activity = datetime.fromtimestamp(now[0] / 1000, timezone.utc)
        return active if candidate is principal else None
    owner.verify_principal = verify
    owner._selected = lambda bridge: True
    owner._release_verifier = lambda *_args: owner_module.VerifiedBrowserRelease(
        principal=principal, server_instance_id=active.server_instance_id, connector_sid="sid-A",
        load_generation_id=hello.load_generation_id, install_instance_id=hello.install_instance_id,
        **{key: getattr(hello, key) for key in policy._ENTRY_FIELDS})
    monkeypatch.setattr(owner_module.time, "time_ns", lambda: now[0] * 1_000_000)
    monkeypatch.setattr(owner_module, "configured_extension_id", lambda: active.extension_id)
    monkeypatch.setattr(owner_module, "get_browser_bridge_gate", lambda: SimpleNamespace(state="available"))
    monkeypatch.setattr(owner_module, "detect_installed_legacy_browser_bridge", lambda: SimpleNamespace(state=owner_module.LegacyDetectionState.ABSENT))
    assert owner.evaluate_admission(active, "sid-A", hello) is not None
    # The fix must not clamp genuinely future/stale timestamps into freshness.
    owner.verify_principal = lambda candidate: active
    for timestamp in (now[0] + 1, now[0] - 30_000):
        connection.last_activity = datetime.fromtimestamp(timestamp / 1000, timezone.utc)
        assert owner.evaluate_admission(active, "sid-A", hello) is None


def test_server_hooks_keep_guard_and_await_exact_owner_shutdown(monkeypatch):
    import asyncio
    from contextlib import asynccontextmanager, nullcontext
    from pathlib import Path
    from helpers import extension, subagents, ui_server
    from plugins._a0_connector.helpers import browser_bridge_legacy_retirement as legacy

    root = Path(__file__).resolve().parents[1]
    enabled, events, applications = [True], [], []
    def paths(_agent, prefix, point):
        roots = [root]
        if enabled[0]:
            roots.append(root / "plugins/_a0_connector")
        return [str(base / prefix / point) for base in roots]
    monkeypatch.setattr(subagents, "get_paths", paths)
    monkeypatch.setattr(extension.cache, "get", lambda *_args: None)
    monkeypatch.setattr(extension.cache, "add", lambda *_args: None)
    monkeypatch.setattr(ui_server.UiServerRuntime, "refresh_runtime_settings", lambda self: None)
    monkeypatch.setattr(ui_server, "set_shared_ws_manager", lambda manager: events.append("manager"))
    monkeypatch.setattr(legacy, "install_legacy_retirement_guard", lambda app: events.append("guard"))
    monkeypatch.setattr(owner_module, "install_configured_browser_runtime", lambda manager: events.append("install") or True)
    async def retire(*, manager):
        await asyncio.sleep(0)
        events.append(("retired", manager))
    monkeypatch.setattr(owner_module, "retire_configured_browser_runtime", retire)
    monkeypatch.setattr(ui_server.mcp_server.DynamicMcpProxy, "get_instance", lambda: object())
    monkeypatch.setattr(ui_server.fasta2a_server.DynamicA2AProxy, "get_instance", lambda: object())
    original_starlette = ui_server.Starlette
    def starlette(**kwargs):
        app = original_starlette(**kwargs)
        applications.append(app)
        return app
    monkeypatch.setattr(ui_server, "Starlette", starlette)
    @asynccontextmanager
    async def lifespan(app):
        yield
    monitor = SimpleNamespace(lifespan=lambda: lifespan, stage=lambda *_args: nullcontext())

    server = ui_server.UiServerRuntime.create()
    assert events == ["manager", "guard"]
    assert not server._routes_registered and not server._transport_registered
    async def attempt():
        with pytest.raises(RuntimeError, match="serving failed"):
            async with applications[-1].router.lifespan_context(applications[-1]):
                assert events == ["install"]
                enabled[0] = False  # Cleanup must not depend on current discovery.
                raise RuntimeError("serving failed")
    for _ in range(2):  # Uvicorn retries reuse this same server, not create().
        events.clear()
        enabled[0] = True
        server.build_asgi_app(monitor)
        assert events == []  # No service installed before lifespan entry.
        asyncio.run(attempt())
        assert events == ["install", ("retired", server.ws_manager)]

    original_start = ui_server.call_extensions_async
    async def fail_after_install(*args, **kwargs):
        await original_start(*args, **kwargs)
        raise RuntimeError("later startup hook failed")
    monkeypatch.setattr(ui_server, "call_extensions_async", fail_after_install)
    events.clear()
    enabled[0] = True
    async def failed_start():
        with pytest.raises(RuntimeError, match="later startup hook failed"):
            async with applications[-1].router.lifespan_context(applications[-1]):
                pytest.fail("failed startup must not begin serving")
    asyncio.run(failed_start())
    assert events == ["install", ("retired", server.ws_manager)]
    monkeypatch.setattr(ui_server, "call_extensions_async", original_start)

    events.clear()
    enabled[0] = False
    ui_server.UiServerRuntime.create()
    assert events == ["manager", "guard"]
    async def disabled_start():
        async with applications[-1].router.lifespan_context(applications[-1]):
            pass
    asyncio.run(disabled_start())
    assert events == ["manager", "guard"]
    events.clear()
    enabled[0] = True
    def fail_settings(self):
        raise RuntimeError("settings unavailable")
    monkeypatch.setattr(ui_server.UiServerRuntime, "refresh_runtime_settings", fail_settings)
    with pytest.raises(RuntimeError, match="settings unavailable"):
        ui_server.UiServerRuntime.create()
    assert events == ["manager"]  # No service installed for a failed construction.


def test_shutdown_cannot_retire_a_different_servers_owner(monkeypatch):
    import asyncio

    manager, other, closed = object(), object(), []
    async def close():
        await asyncio.sleep(0)
        closed.append(True)
        return True
    owner = SimpleNamespace(manager=manager, close=close)
    monkeypatch.setattr(owner_module, "_owner", owner)
    monkeypatch.setattr(owner_module, "_retiring", False)
    assert asyncio.run(owner_module.retire_configured_browser_runtime(manager=other)) is False
    assert owner_module._owner is owner and not closed
    assert asyncio.run(owner_module.retire_configured_browser_runtime(manager=manager)) is True
    assert owner_module._owner is None and closed == [True]
