"""Health check and connection test API for Deimos OpenBao plugin.

Endpoint: POST /api/plugins/deimos_openbao_secrets/health
"""
import importlib
import logging
import os
import subprocess
import sys
from helpers.api import ApiHandler, Request, Response

logger = logging.getLogger(__name__)


def _ensure_hvac() -> bool:
    """Ensure hvac is installed in the current Python environment."""
    try:
        importlib.import_module("hvac")
        return True
    except ImportError:
        pass

    logger.info("Installing hvac for OpenBao connection test...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "hvac>=2.1.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        importlib.import_module("hvac")
        return True
    except Exception as exc:
        logger.error("Failed to install hvac: %s", exc)
        return False


class TestConnection(ApiHandler):
    """Test OpenBao connectivity from the plugin config UI."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        config_data = input.get("config", {})
        url = config_data.get("url", "http://127.0.0.1:8200")
        timeout = float(config_data.get("timeout", 10.0))
        tls_verify = config_data.get("tls_verify", True)
        tls_ca_cert = config_data.get("tls_ca_cert", "")

        # Auto-install hvac if needed
        if not _ensure_hvac():
            return {
                "ok": False,
                "error": "Failed to install hvac library. Check pip permissions.",
            }

        try:
            import hvac

            verify = tls_ca_cert if tls_ca_cert else tls_verify
            client = hvac.Client(url=url, verify=verify, timeout=timeout)

            # Health check doesn't require authentication
            health = client.sys.read_health_status(method="GET")

            if isinstance(health, dict):
                status = "healthy"
                if health.get("sealed"):
                    status = "sealed"
                return {
                    "ok": True,
                    "data": {
                        "status": status,
                        "initialized": health.get("initialized"),
                        "sealed": health.get("sealed"),
                        "standby": health.get("standby"),
                    },
                }
            else:
                return {"ok": True, "data": {"status": "reachable"}}

        except Exception as exc:
            logger.debug("OpenBao connection test failed: %s", exc)
            return {"ok": False, "error": str(exc)}
