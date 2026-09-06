from __future__ import annotations

import asyncio
import importlib
import sys
from types import ModuleType

from plugins._browser.helpers.bridge_foundation import (
    BROWSER_BRIDGE_FOUNDATION_CONTRACT,
    BROWSER_BRIDGE_ROLLOUT_ENV,
    BROWSER_BRIDGE_STATUS_CONTRACT,
    BrowserBridgeGate,
    build_browser_bridge_status,
    get_browser_bridge_gate,
)
from plugins._a0_connector.helpers.browser_bridge_cutover import (
    LegacyBridgeDetection,
    LegacyDetectionState,
)


def test_rollout_gate_accepts_only_frozen_states_and_fails_closed() -> None:
    default = BrowserBridgeGate.from_value(None)
    assert default.state == "disabled"
    assert default.configured is False
    assert BrowserBridgeGate.from_value("preview").state == "preview"
    assert BrowserBridgeGate.from_value("AVAILABLE").state == "available"

    invalid = BrowserBridgeGate.from_value("enabled")
    assert invalid.state == "disabled"
    assert invalid.reason_code == "invalid_rollout_defaulted_disabled"
    assert "enabled" not in repr(invalid.as_dict())


def test_rollout_gate_is_instance_scoped_and_off_by_default() -> None:
    assert get_browser_bridge_gate(environ={}).state == "disabled"
    assert get_browser_bridge_gate(
        environ={BROWSER_BRIDGE_ROLLOUT_ENV: " PREVIEW "}
    ).state == "preview"
    invalid = get_browser_bridge_gate(
        environ={BROWSER_BRIDGE_ROLLOUT_ENV: "enabled"}
    )
    assert invalid.state == "disabled"
    assert invalid.reason_code == "invalid_rollout_defaulted_disabled"


def test_foundation_status_is_redacted_and_does_not_infer_remote_health() -> None:
    secret_bridge_id = "bridge-private-123"
    status = build_browser_bridge_status(
        {
            "runtime_backend": "host_required",
            "host_browser_selection": f"extension:{secret_bridge_id}",
        },
        BrowserBridgeGate.from_value("available"),
        checked_at="2026-09-04T12:00:00Z",
    )

    assert status["foundation_contract"] == BROWSER_BRIDGE_FOUNDATION_CONTRACT
    assert status["status_contract"] == BROWSER_BRIDGE_STATUS_CONTRACT
    assert status["scope"] == "extension_bridge_foundation"
    assert status["selection"]["runtime_backend"] == "host_required"
    assert status["selection"]["browser_selection"] == "extension:<redacted>"
    assert status["selection"]["configured_backend_id"] == "chrome_extension"
    assert status["selection"]["state"] == "configured"
    assert secret_bridge_id not in repr(status)
    assert status["layers"]["server"]["state"] == "configured"
    for name in (
        "credential",
        "companion",
        "browser_registration",
        "extension",
        "chrome_permission",
        "site_policy",
        "runtime",
    ):
        assert status["layers"][name]["state"] == "unknown"
        assert status["layers"][name]["checked_at"] is None
    assert status["actions"] == []


def test_disabled_foundation_reports_remote_layers_not_checked() -> None:
    status = build_browser_bridge_status(
        {"runtime_backend": "container", "host_browser_selection": ""},
        BrowserBridgeGate.from_value("disabled"),
        checked_at="2026-09-04T12:00:00Z",
    )

    assert status["gate"]["state"] == "disabled"
    assert status["layers"]["server"]["state"] == "blocked"
    assert status["layers"]["runtime"]["state"] == "not_checked"
    assert status["selection"]["configured_backend_id"] == "container"


def test_malformed_extension_selection_is_blocked_and_never_an_effective_backend() -> None:
    status = build_browser_bridge_status(
        {
            "runtime_backend": "host_required",
            "host_browser_selection": "extension:",
        },
        BrowserBridgeGate.from_value("available"),
        checked_at="2026-09-04T12:00:00Z",
    )

    assert status["selection"]["state"] == "blocked"
    assert status["selection"]["configured_backend_id"] is None
    assert status["layers"]["runtime"]["state"] == "not_checked"
    assert (
        status["layers"]["runtime"]["reason_code"]
        == "invalid_extension_browser_selection"
    )


def test_untrusted_runtime_backend_is_not_projected() -> None:
    secret = "https://example.test/?token=do-not-project"
    status = build_browser_bridge_status(
        {"runtime_backend": secret, "host_browser_selection": "chrome"},
        BrowserBridgeGate.from_value("available"),
        checked_at="2026-09-04T12:00:00Z",
    )

    assert secret not in repr(status)
    assert status["selection"]["runtime_backend"] is None
    assert status["selection"]["configured_backend_id"] is None
    assert status["selection"]["reason_code"] == "invalid_runtime_backend"
    assert status["layers"]["runtime"]["reason_code"] == "invalid_runtime_backend"


def test_browser_status_preserves_existing_keys_and_adds_foundation(monkeypatch) -> None:
    class FakeApiHandler:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    api_stub = ModuleType("helpers.api")
    api_stub.ApiHandler = FakeApiHandler
    api_stub.Request = object

    config_stub = ModuleType("plugins._browser.helpers.config")
    config_stub.get_browser_config = lambda: {
        "runtime_backend": "container",
        "host_browser_selection": "",
    }
    config_stub.build_browser_launch_config = lambda config: {
        "browser_mode": "chromium",
        "extensions": {"enabled": False},
        "requires_full_browser": False,
    }

    view_stub = ModuleType("plugins._browser.helpers.interactive_view")
    view_stub.collect_status = lambda: {"ready": False}
    playwright_stub = ModuleType("plugins._browser.helpers.playwright")
    playwright_stub.get_playwright_binary = lambda: None
    playwright_stub.get_playwright_cache_dir = lambda: "/cache"
    playwright_stub.get_playwright_cache_dirs = lambda: []
    runtime_stub = ModuleType("plugins._browser.helpers.runtime")
    runtime_stub.known_context_ids = lambda: []
    connector_stub = ModuleType("plugins._a0_connector.helpers.ws_runtime")
    connector_stub.all_host_browser_metadata = lambda: []

    status_module_name = "plugins._browser.api.status"
    previous_status_module = sys.modules.pop(status_module_name, None)
    with monkeypatch.context() as context:
        for name, module in {
            "helpers.api": api_stub,
            "plugins._browser.helpers.config": config_stub,
            "plugins._browser.helpers.interactive_view": view_stub,
            "plugins._browser.helpers.playwright": playwright_stub,
            "plugins._browser.helpers.runtime": runtime_stub,
            "plugins._a0_connector.helpers.ws_runtime": connector_stub,
        }.items():
            context.setitem(sys.modules, name, module)
        status_api = importlib.import_module(status_module_name)
        context.setattr(
            status_api,
            "get_browser_bridge_gate",
            lambda: BrowserBridgeGate.from_value("disabled"),
        )
        context.setattr(
            status_api,
            "detect_installed_legacy_browser_bridge",
            lambda: LegacyBridgeDetection(
                state=LegacyDetectionState.ABSENT,
                reason_code="legacy_bridge_absent",
                manifest_matched=False,
            ),
        )

        response = asyncio.run(status_api.Status(None, None).process({}, request=None))

        sys.modules.pop(status_module_name, None)
        if previous_status_module is not None:
            sys.modules[status_module_name] = previous_status_module

    assert {
        "plugin",
        "playwright",
        "extensions",
        "host_browser",
        "interactive_view",
        "contexts",
    }.issubset(response)
    assert response["extension_bridge"]["status_contract"] == BROWSER_BRIDGE_STATUS_CONTRACT
    assert response["extension_bridge"]["scope"] == "extension_bridge_foundation"
    assert response["extension_bridge"]["gate"]["state"] == "disabled"
    assert response["extension_bridge"]["selection"]["state"] == "not_checked"
    assert response["extension_bridge"]["cutover"]["state"] == "not_detected"


def test_connector_discovery_does_not_imply_installation_or_runtime_admission(monkeypatch) -> None:
    api_stub = ModuleType("helpers.api")
    api_stub.Request = object
    api_stub.Response = object

    base_stub = ModuleType("plugins._a0_connector.api.v1.base")
    base_stub.PublicConnectorApiHandler = object
    version_stub = ModuleType("plugins._a0_connector.helpers.version")
    version_stub.agent_zero_version = lambda: "test"

    module_name = "plugins._a0_connector.api.v1.capabilities"
    previous = sys.modules.pop(module_name, None)
    with monkeypatch.context() as context:
        context.setitem(sys.modules, "helpers.api", api_stub)
        context.setitem(sys.modules, "plugins._a0_connector.api.v1.base", base_stub)
        context.setitem(sys.modules, "plugins._a0_connector.helpers.version", version_stub)
        capabilities = importlib.import_module(module_name)
        features = capabilities._feature_list()

        sys.modules.pop(module_name, None)
        if previous is not None:
            sys.modules[module_name] = previous

    # One discovery boundary replaces six copies of the same import/stub check.
    assert {
        "browser_extension_bridge_foundation", "browser_extension_mv3_runtime_foundation",
        "browser_bridge_pairing_v1", "browser_companion_release_metadata",
    }.issubset(features)
    assert {
        "browser_extension_pairing", "browser_extension_runtime",
        "browser_extension_bridge_v1", "connector_browser_control",
        "browser_bridge_challenge_v1", "browser_bridge_approval_v1",
        "browser_bridge_policy_v1", "browser_companion_install", "browser_companion_pairing",
    }.isdisjoint(features)
