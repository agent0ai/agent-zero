"""Health check and connection test API for Deimos OpenBao plugin.

Endpoint: POST /api/plugins/deimos_openbao_secrets/health

Verifies connectivity AND credentials using ONLY the configured auth method.
"""
import importlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from helpers.api import ApiHandler, Request, Response

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent.parent


def _ensure_hvac():
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


def _load_plugin_config():
    """Load plugin config to get auth_method."""
    import yaml
    defaults = {}
    dp = _PLUGIN_DIR / "default_config.yaml"
    if dp.exists():
        with open(dp) as f:
            defaults = yaml.safe_load(f) or {}
    saved = {}
    cp = _PLUGIN_DIR / "config.json"
    if cp.exists():
        try:
            with open(cp) as f:
                saved = json.load(f) or {}
        except Exception:
            saved = {}
    return {**defaults, **saved}


class TestConnection(ApiHandler):
    """Test OpenBao connectivity and authentication."""

    @classmethod
    def requires_api_key(cls):
        return False

    @classmethod
    def requires_auth(cls):
        return True

    @classmethod
    def requires_csrf(cls):
        return False

    async def process(self, input, request):
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
                        "ok": False,
                        "error": "OpenBao is SEALED",
                        "data": {**health_info, "authenticated": False}
                    }

            # Step 2: Auth using ONLY the configured method
            plugin_cfg = _load_plugin_config()
            auth_method = plugin_cfg.get("auth_method", "token")

            if auth_method == "token":
                token = os.environ.get("OPENBAO_TOKEN", "")
                if not token:
                    return {
                        "ok": False,
                        "error": "OPENBAO_TOKEN not set in Docker environment",
                        "data": {**health_info, "authenticated": False, "auth_method": "token"}
                    }
                client.token = token

            elif auth_method == "approle":
                role_id = os.environ.get("OPENBAO_ROLE_ID", "")
                secret_id = os.environ.get("OPENBAO_SECRET_ID", "")
                if not role_id:
                    return {
                        "ok": False,
                        "error": "OPENBAO_ROLE_ID not set in Docker environment",
                        "data": {**health_info, "authenticated": False, "auth_method": "approle"}
                    }
                try:
                    result = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
                    client.token = result["auth"]["client_token"]
                except Exception as auth_exc:
                    return {
                        "ok": False,
                        "error": "AppRole login failed: " + str(auth_exc),
                        "data": {**health_info, "authenticated": False, "auth_method": "approle"}
                    }
            else:
                return {
                    "ok": False,
                    "error": "Unknown auth method: " + str(auth_method),
                    "data": {**health_info, "authenticated": False}
                }

            # Verify the token works
            if client.is_authenticated():
                return {
                    "ok": True,
                    "data": {
                        "status": "connected and authenticated",
                        **health_info,
                        "authenticated": True,
                        "auth_method": auth_method,
                    }
                }
            else:
                return {
                    "ok": False,
                    "error": "Authentication failed (token invalid or expired)",
                    "data": {**health_info, "authenticated": False, "auth_method": auth_method}
                }

        except Exception as exc:
            return {"ok": False, "error": str(exc)}
