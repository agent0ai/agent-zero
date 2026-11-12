"""Static MV3 discovery metadata, never a runtime lease validator."""

from typing import Any

MV3_RUNTIME_CONTRACT = "a0.browser-bridge.mv3-runtime.v1"
CORE_ADAPTER_CONTRACT = "a0.browser-bridge.adapter.v1"
BRIDGE_PROTOCOL_CONTRACT = "a0.browser-bridge.v1"
BRIDGE_CONTRACT_VERSION = 1
MV3_RUNTIME_FOUNDATION_FEATURE = "browser_extension_mv3_runtime_foundation"


def build_mv3_runtime_foundation_status() -> dict[str, Any]:
    """Preserve discovery shape without asserting live validation or readiness."""
    return {
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
