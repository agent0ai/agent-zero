import pytest

from plugins._browser.helpers.bridge_foundation import (
    BrowserBridgeGate,
    build_browser_bridge_status,
)
from plugins._browser.helpers.mv3_runtime_foundation import (
    BRIDGE_CONTRACT_VERSION,
    BRIDGE_PROTOCOL_CONTRACT,
    CORE_ADAPTER_CONTRACT,
    MV3_RUNTIME_CONTRACT,
    build_mv3_runtime_foundation_status,
)


def test_mv3_status_projects_exact_contracts_but_remains_disabled() -> None:
    assert build_mv3_runtime_foundation_status() == {
        "contract": MV3_RUNTIME_CONTRACT,
        "adapter_contract": CORE_ADAPTER_CONTRACT,
        "protocol_contract": BRIDGE_PROTOCOL_CONTRACT,
        "contract_version": BRIDGE_CONTRACT_VERSION,
        "state": "disabled",
        "reason_code": "mv3_runtime_foundation_only",
        "runtime_ready": False,
        "pairing_enabled": False,
        "dispatch_enabled": False,
        "browser_mutation_enabled": False,
        "validation": {
            "mode": "schema_only",
            "task_lease_binding": False,
            "turn_finalization": False,
        },
        "native_runtime_location": "user_browser_host",
        "docker_browser_host_access": False,
    }


@pytest.mark.parametrize("gate_state", ["disabled", "preview", "available"])
def test_rollout_gate_never_activates_mv3_foundation(gate_state: str) -> None:
    bridge_status = build_browser_bridge_status(
        None,
        BrowserBridgeGate.from_value(gate_state),
        checked_at="2026-09-04T12:00:00Z",
    )
    assert bridge_status["gate"]["state"] == gate_state
    assert bridge_status["mv3_runtime"] == build_mv3_runtime_foundation_status()
