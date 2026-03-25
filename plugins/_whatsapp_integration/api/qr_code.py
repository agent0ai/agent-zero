"""WhatsApp QR code pairing endpoint."""

from helpers.api import ApiHandler, Request
from helpers.errors import format_error
from helpers import files, plugins


PLUGIN_NAME = "_whatsapp_integration"


class QrCode(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        port = int(config.get("bridge_port", 3100))
        session_dir = files.get_abs_path("usr/whatsapp/sessions")
        cache_dir = files.get_abs_path("usr/whatsapp/media")
        allowed_users = config.get("allowed_users") or []
        mode = config.get("mode", "dedicated")

        from plugins._whatsapp_integration.helpers.bridge_manager import (
            ensure_bridge_http_up,
            get_bridge_url,
            is_process_alive,
        )
        from plugins._whatsapp_integration.helpers.wa_client import get_qr

        base_url = get_bridge_url(port)

        # Start bridge if not running
        if not is_process_alive():
            try:
                ok = await ensure_bridge_http_up(
                    port, session_dir, cache_dir, allowed_users, mode=mode,
                )
                if not ok:
                    return {
                        "status": "error",
                        "message": "Failed to start bridge",
                        "qr": None,
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": format_error(e),
                    "qr": None,
                }

        # Fetch QR status from bridge
        try:
            data = await get_qr(base_url)
            status = data.get("status", "error")
            qr = data.get("qr")

            if status == "connected":
                return {
                    "status": "connected",
                    "message": "WhatsApp is already connected",
                    "qr": None,
                }

            if status == "waiting_scan" and qr:
                return {
                    "status": "waiting_scan",
                    "message": "Scan the QR code with WhatsApp",
                    "qr": qr,
                }

            return {
                "status": "waiting_qr",
                "message": "Generating QR code...",
                "qr": None,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Bridge not reachable: {format_error(e)}",
                "qr": None,
            }
