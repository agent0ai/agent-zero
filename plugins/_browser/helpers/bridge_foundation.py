from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from plugins._browser.helpers.mv3_runtime_foundation import (
    build_mv3_runtime_foundation_status,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    build_browser_bridge_pairing_foundation_status,
)


BROWSER_BRIDGE_ROLLOUT_KEY = "browser_bridge_rollout"
BROWSER_BRIDGE_ROLLOUT_ENV = "A0_BROWSER_BRIDGE_ROLLOUT"
BROWSER_BRIDGE_FOUNDATION_CONTRACT = "a0.browser-bridge.foundation.v1"
BROWSER_BRIDGE_GATE_CONTRACT = "a0.browser-bridge.rollout.v1"
BROWSER_BRIDGE_STATUS_CONTRACT = "a0.browser-bridge.status.v1"
BROWSER_BRIDGE_ROLLOUT_STATES = frozenset({"disabled", "preview", "available"})
DEFAULT_BROWSER_BRIDGE_ROLLOUT = "disabled"

_REMOTE_LAYER_NAMES = (
    "credential",
    "companion",
    "browser_registration",
    "extension",
    "chrome_permission",
    "site_policy",
    "runtime",
)


def _checked_at_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class BrowserBridgeGate:
    state: str
    reason_code: str
    configured: bool

    @classmethod
    def from_value(cls, value: Any) -> BrowserBridgeGate:
        configured = value is not None
        normalized = str(value or "").strip().lower()
        if normalized in BROWSER_BRIDGE_ROLLOUT_STATES:
            return cls(
                state=normalized,
                reason_code=f"rollout_{normalized}",
                configured=configured,
            )
        return cls(
            state=DEFAULT_BROWSER_BRIDGE_ROLLOUT,
            reason_code=(
                "rollout_disabled"
                if not normalized
                else "invalid_rollout_defaulted_disabled"
            ),
            configured=configured,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_contract": BROWSER_BRIDGE_GATE_CONTRACT,
            "state": self.state,
            "reason_code": self.reason_code,
            "configured": self.configured,
        }


@dataclass(frozen=True, slots=True)
class BrowserBridgeStatusLayer:
    state: str
    reason_code: str
    message: str
    checked_at: str | None
    source: str
    action_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "state": self.state,
            "reason_code": self.reason_code,
            "message": self.message,
            "checked_at": self.checked_at,
            "source": self.source,
        }
        if self.action_id:
            result["action_id"] = self.action_id
        return result


def get_browser_bridge_gate(
    *, environ: Mapping[str, str] | None = None
) -> BrowserBridgeGate:
    """Read the instance gate without consulting project-scoped Browser config."""

    source = os.environ if environ is None else environ
    return BrowserBridgeGate.from_value(source.get(BROWSER_BRIDGE_ROLLOUT_ENV))


def _redacted_selection(browser_config: dict[str, Any] | None) -> dict[str, Any]:
    if browser_config is None:
        return {
            "runtime_backend": None,
            "browser_selection": "",
            "configured_backend_id": None,
            "state": "not_checked",
            "reason_code": "project_selection_scope_unavailable",
            "source": "not_checked",
        }

    runtime_backend = str(browser_config.get("runtime_backend", "container") or "container")
    configured_selection = str(browser_config.get("host_browser_selection", "") or "")

    if runtime_backend not in {"container", "host_required"}:
        runtime_backend = None
        selection = ""
        configured_backend_id = None
        state = "blocked"
        reason_code = "invalid_runtime_backend"
    elif runtime_backend != "host_required":
        selection = ""
        configured_backend_id: str | None = "container"
        state = "selected"
        reason_code = "container_selected"
    else:
        from plugins._browser.helpers.config import parse_extension_browser_selection

        try:
            extension_selection = parse_extension_browser_selection(configured_selection)
        except ValueError:
            selection = "extension:<invalid>"
            configured_backend_id = None
            state = "blocked"
            reason_code = "invalid_extension_browser_selection"
        else:
            if extension_selection is not None:
                selection = "extension:<redacted>"
                configured_backend_id = "chrome_extension"
                state = "configured"
                reason_code = "extension_selection_configured"
            elif configured_selection:
                selection = "legacy:<redacted>"
                configured_backend_id = "legacy_cdp"
                state = "selected"
                reason_code = "legacy_selection_configured"
            else:
                selection = ""
                configured_backend_id = None
                state = "not_selected"
                reason_code = "host_selection_automatic"

    return {
        "runtime_backend": runtime_backend,
        "browser_selection": selection,
        "configured_backend_id": configured_backend_id,
        "state": state,
        "reason_code": reason_code,
        "source": "supplied_project_config",
    }


def _server_layer(gate: BrowserBridgeGate, checked_at: str) -> BrowserBridgeStatusLayer:
    if gate.reason_code == "invalid_rollout_defaulted_disabled":
        return BrowserBridgeStatusLayer(
            state="blocked",
            reason_code=gate.reason_code,
            message="The configured bridge rollout is invalid; the server failed closed.",
            checked_at=checked_at,
            source="server_environment",
        )
    if gate.state == "disabled":
        return BrowserBridgeStatusLayer(
            state="blocked",
            reason_code="rollout_disabled",
            message="The extension bridge server gate is disabled.",
            checked_at=checked_at,
            source="server_environment",
        )
    return BrowserBridgeStatusLayer(
        state="configured",
        reason_code=gate.reason_code,
        message=(
            "The extension bridge preview gate is configured; remote readiness is not checked."
            if gate.state == "preview"
            else (
                "The extension bridge availability gate is configured; "
                "remote readiness is not checked."
            )
        ),
        checked_at=checked_at,
        source="server_environment",
    )


def _remote_layer(
    gate: BrowserBridgeGate,
    *,
    extension_selected: bool,
    selection_block_reason: str,
    selection_checked: bool,
) -> BrowserBridgeStatusLayer:
    if gate.state == "disabled":
        return BrowserBridgeStatusLayer(
            state="not_checked",
            reason_code="rollout_disabled",
            message="This remote layer was not checked because the server gate is disabled.",
            checked_at=None,
            source="not_checked",
        )
    if not selection_checked:
        return BrowserBridgeStatusLayer(
            state="not_checked",
            reason_code="project_selection_scope_unavailable",
            message="This remote layer was not checked without a project selection scope.",
            checked_at=None,
            source="not_checked",
        )
    if selection_block_reason:
        return BrowserBridgeStatusLayer(
            state="not_checked",
            reason_code=selection_block_reason,
            message=(
                "This remote layer was not checked because the project "
                "configuration is invalid."
            ),
            checked_at=None,
            source="not_checked",
        )
    if not extension_selected:
        return BrowserBridgeStatusLayer(
            state="not_checked",
            reason_code="extension_not_selected",
            message="This remote layer was not checked because no extension bridge is selected.",
            checked_at=None,
            source="not_checked",
        )
    return BrowserBridgeStatusLayer(
        state="unknown",
        reason_code="status_source_unavailable",
        message="No authenticated remote status source is available for this layer.",
        checked_at=None,
        source="unavailable",
    )


def build_browser_bridge_status(
    browser_config: dict[str, Any] | None,
    gate: BrowserBridgeGate,
    *,
    checked_at: str | None = None,
) -> dict[str, Any]:
    safe_checked_at = checked_at or _checked_at_now()
    selection = _redacted_selection(browser_config)
    remote_layer = _remote_layer(
        gate,
        extension_selected=selection["configured_backend_id"] == "chrome_extension",
        selection_block_reason=(
            selection["reason_code"] if selection["state"] == "blocked" else ""
        ),
        selection_checked=selection["state"] != "not_checked",
    )
    layers = {"server": _server_layer(gate, safe_checked_at).as_dict()}
    layers.update({name: remote_layer.as_dict() for name in _REMOTE_LAYER_NAMES})

    return {
        "scope": "extension_bridge_foundation",
        "foundation_contract": BROWSER_BRIDGE_FOUNDATION_CONTRACT,
        "status_contract": BROWSER_BRIDGE_STATUS_CONTRACT,
        "gate": gate.as_dict(),
        "selection": selection,
        "layers": layers,
        "trust": build_browser_bridge_pairing_foundation_status(gate),
        "mv3_runtime": build_mv3_runtime_foundation_status(),
        "actions": [],
    }
