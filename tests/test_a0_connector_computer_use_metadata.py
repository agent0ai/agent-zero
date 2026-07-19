from __future__ import annotations

from plugins._a0_connector.helpers import ws_runtime


def test_computer_use_metadata_preserves_structured_capabilities() -> None:
    sid = "sid-capabilities"
    ws_runtime.clear_sid_computer_use_metadata(sid)

    ws_runtime.store_sid_computer_use_metadata(
        sid,
        {
            "supported": True,
            "enabled": True,
            "trust_mode": "allow",
            "status": "active",
            "last_error": "",
            "restore_token_present": True,
            "artifact_root": "/a0/tmp/_a0_connector/computer_use",
            "backend_id": "windows",
            "backend_family": "windows",
            "features": ["native-window-list", "element-index-targeting"],
            "contract_version": 1,
            "capabilities": {
                "contract_version": 1,
                "identity": {
                    "pid": True,
                    "window_id": True,
                    "element_index": True,
                },
                "dispatch": {
                    "default": "background",
                    "background": True,
                },
            },
            "support_reason": "Windows UIA backend is available.",
        },
    )

    metadata = ws_runtime.computer_use_metadata_for_sid(sid)

    assert metadata is not None
    assert metadata["contract_version"] == 1
    assert metadata["capabilities"]["identity"]["element_index"] is True
    assert metadata["capabilities"]["dispatch"]["default"] == "background"

    metadata["capabilities"]["dispatch"]["default"] = "foreground"
    fresh_metadata = ws_runtime.computer_use_metadata_for_sid(sid)
    assert fresh_metadata is not None
    assert fresh_metadata["capabilities"]["dispatch"]["default"] == "background"

    ws_runtime.clear_sid_computer_use_metadata(sid)
