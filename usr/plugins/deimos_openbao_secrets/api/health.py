"""Health check and connection test API for Deimos OpenBao plugin.

Endpoint: POST /api/plugins/deimos_openbao_secrets/health

Verifies both connectivity AND credentials.
"""
import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from helpers.api import ApiHandler, Request, Response

logger = logging.getLogger(__name__)


def _ensure_hvac() -> bool:
    try:
        importlib.import_module("hvac")
        return True
    except ImportError:
        pass
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "hvac>=2.1.0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120,
        )
        importlib.import_module("hvac")
        return True
    except Exception as exc:
        logger.error("Failed to install hvac: %s", exc)
        return False


class TestConnection(ApiHandler):
    """Test OpenBao connectivity and authentication."""

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not _ensure_hvac():
            return {"ok": False, "error": "hvac library not installed"}

        import hvac

        cfg_input = input.get("config", {})
        url = cfg_input.get("url", "")
        timeout = cfg_input.get("timeout", 10)
        tls_verify = cfg_input.get("tls_verify", True)
        tls_ca_cert = cfg_input.get("tls_ca_cert", "")

        if not url:
            return {"ok": False, "error": "No OpenBao URL configured"}

        try:
            verify = tls_ca_cert if tls_ca_cert else tls_verify
            client = hvac.Client(url=url, verify=verify, timeout=timeout)

            # Step 1: Health check (no auth required)
            health = client.sys.read_health_status(method="GET")
            health_info = {}
            if isinstance(health, dict):
                health_info = {
                    "initialized": health.get("initialized"),
                    "sealed": health.get("sealed"),
                    "version": health.get("version", "unknown"),
                }
                if health.get("sealed"):
                    return {
                        "ok": True,
                        "data": {"status": "reachable but SEALED", **health_info, "authenticated": False}
                    }

            # Step 2: Verify credentials
            token = os.environ.get("OPENBAO_TOKEN", "")
            role_id = os.environ.get("OPENBAO_ROLE_ID", "")
            secret_id = os.environ.get("OPENBAO_SECRET_ID", "")

            if token:
                client.token = token
                auth_method = "token"
            elif role_id:
                try:
                    result = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
                    client.token = result["auth"]["client_token"]
                    auth_method = "approle"
                except Exception as auth_exc:
                    return {
                        "ok": True,
                        "data": {
                            "status": "reachable but auth failed",
                            **health_info,
                            "authenticated": False,
                            "auth_error": str(auth_exc)
                        }
                    }
            else:
                return {
                    "ok": True,
                    "data": {
                        "status": "reachable but no credentials",
                        **health_info,
                        "authenticated": False,
                        "auth_error": "No OPENBAO_TOKEN or OPENBAO_ROLE_ID set as Docker env vars"
                    }
                }

            if client.is_authenticated():
                return {
                    "ok": True,
                    "data": {
                        "status": "connected and authenticated",
                        **health_info,
                        "authenticated": True,
                        "auth_method": auth_method
                    }
                }
            else:
                return {
                    "ok": True,
                    "data": {
                        "status": "reachable but token invalid",
                        **health_info,
                        "authenticated": False,
                        "auth_error": "Token is not valid or has expired"
                    }
                }

        except Exception as exc:
            return {"ok": False, "error": str(exc)}
