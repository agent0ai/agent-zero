"""Public setup links; never installation, pairing or runtime authority."""
from __future__ import annotations

from typing import Mapping

from plugins._a0_connector.helpers.browser_bridge_pairing import configured_extension_id
from plugins._a0_connector.helpers.browser_companion_release import browser_companion_release_status
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


def browser_bridge_setup_status(*, environ: Mapping[str, str] | None = None) -> dict:
    extension_id = configured_extension_id(environ=environ)
    enabled = get_browser_bridge_gate(environ=environ).state == "available" and extension_id is not None
    release = browser_companion_release_status(environ=environ)
    artifacts = release["artifacts"] if enabled and release["state"] == "available" else []
    return {
        "contract": "a0.browser-bridge.setup.v1",
        "setup_enabled": enabled,
        "browser_control_ready": False,
        "install_target": "browser_host",
        "host_verification_required": True,
        "extension_id": extension_id if enabled else None,
        "extension_url": f"https://chromewebstore.google.com/detail/{extension_id}" if enabled else None,
        "companion_version": release["release"]["version"] if artifacts else None,
        "installers": [
            {"platform": item["platform"], "arch": item["arch"], "url": item["download_url"]}
            for item in artifacts if item["kind"] in {"installer", "bootstrap"}
        ],
    }
