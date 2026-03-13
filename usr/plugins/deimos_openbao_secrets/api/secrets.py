"""Secrets CRUD API for Deimos OpenBao plugin.

Endpoint: POST /api/plugins/deimos_openbao_secrets/secrets

Actions: list, get, set, delete

LLM Isolation: This endpoint runs entirely between browser and OpenBao.
No LLM is involved at any point.
"""
import importlib
import logging
import os
import subprocess
import sys
from helpers.api import ApiHandler, Request, Response

logger = logging.getLogger(__name__)


def _ensure_hvac() -> bool:
    """Ensure hvac is installed."""
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


def _get_client():
    """Create an authenticated hvac client from config + env vars."""
    import hvac
    from helpers.plugins import find_plugin_dir
    import importlib.util

    plugin_dir = find_plugin_dir("deimos_openbao_secrets")
    if not plugin_dir:
        raise RuntimeError("Plugin directory not found")

    # Load config
    config_path = os.path.join(plugin_dir, "helpers", "config.py")
    spec = importlib.util.spec_from_file_location("openbao_cfg", config_path)
    cfg_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg_mod)
    config = cfg_mod.load_config(plugin_dir)

    if not config.enabled:
        raise RuntimeError("OpenBao plugin is not enabled")

    verify = config.tls_ca_cert if config.tls_ca_cert else config.tls_verify
    client = hvac.Client(url=config.url, verify=verify, timeout=config.timeout)

    # Auth from env vars
    token = os.environ.get("OPENBAO_TOKEN", "")
    if token:
        client.token = token
    else:
        role_id = os.environ.get("OPENBAO_ROLE_ID", "")
        secret_id = os.environ.get("OPENBAO_SECRET_ID", "")
        if role_id:
            result = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = result["auth"]["client_token"]
        else:
            raise RuntimeError(
                "No credentials found. Set OPENBAO_TOKEN or OPENBAO_ROLE_ID/OPENBAO_SECRET_ID "
                "as Docker environment variables."
            )

    if not client.is_authenticated():
        raise RuntimeError("OpenBao authentication failed")

    return client, config


def _get_path(config, project_name: str = "") -> str:
    """Build the secrets path, optionally scoped to a project."""
    path = config.secrets_path
    if project_name:
        path = f"{path}/{project_name}"
    return path


class SecretsManager(ApiHandler):
    """CRUD operations for OpenBao secrets."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not _ensure_hvac():
            return {"ok": False, "error": "Failed to install hvac library"}

        try:
            client, config = _get_client()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        import hvac.exceptions

        mount = config.mount_point
        project_name = input.get("project_name", "")
        path = _get_path(config, project_name)
        action = input.get("action", "")

        try:
            if action == "list":
                return self._list(client, mount, path)
            elif action == "get":
                return self._get(client, mount, path, input.get("key", ""))
            elif action == "set":
                return self._set(client, mount, path, input.get("pairs", []))
            elif action == "delete":
                return self._delete(client, mount, path, input.get("key", ""))
            else:
                return {"ok": False, "error": f"Unknown action: {action}"}
        except hvac.exceptions.Forbidden:
            return {"ok": False, "error": "Permission denied. Check token permissions."}
        except hvac.exceptions.InvalidPath:
            if action == "list":
                return {"ok": True, "secrets": []}
            return {"ok": False, "error": "Path not found in OpenBao"}
        except Exception as exc:
            logger.error("Secrets API error (%s): %s", action, exc)
            return {"ok": False, "error": str(exc)}

    def _list(self, client, mount: str, path: str) -> dict:
        """List secret key names (values masked)."""
        try:
            resp = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount, raise_on_deleted_version=False
            )
            data = resp.get("data", {}).get("data", {})
            secrets = []
            for key in sorted(data.keys()):
                secrets.append({"key": key, "has_value": bool(data[key])})
            return {"ok": True, "secrets": secrets}
        except Exception:
            return {"ok": True, "secrets": []}

    def _get(self, client, mount: str, path: str, key: str) -> dict:
        """Read a single secret value (for reveal)."""
        if not key:
            return {"ok": False, "error": "Key is required"}
        resp = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount, raise_on_deleted_version=False
        )
        data = resp.get("data", {}).get("data", {})
        if key not in data:
            return {"ok": False, "error": f"Key not found: {key}"}
        return {"ok": True, "key": key, "value": data[key]}

    def _set(self, client, mount: str, path: str, pairs: list) -> dict:
        """Write key-value pairs (read-modify-write to preserve existing)."""
        if not pairs:
            return {"ok": False, "error": "No key-value pairs provided"}
        # Read existing
        try:
            resp = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount, raise_on_deleted_version=False
            )
            current = resp.get("data", {}).get("data", {})
        except Exception:
            current = {}
        # Merge
        for pair in pairs:
            k = pair.get("key", "").strip()
            v = pair.get("value", "")
            if k:
                current[k] = v
        # Write
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=current, mount_point=mount
        )
        return {"ok": True, "message": f"Saved {len(pairs)} secret(s)"}

    def _delete(self, client, mount: str, path: str, key: str) -> dict:
        """Delete a key (read-modify-write)."""
        if not key:
            return {"ok": False, "error": "Key is required"}
        resp = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount, raise_on_deleted_version=False
        )
        data = resp.get("data", {}).get("data", {})
        if key not in data:
            return {"ok": False, "error": f"Key not found: {key}"}
        del data[key]
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=data, mount_point=mount
        )
        return {"ok": True, "message": f"Deleted: {key}"}
