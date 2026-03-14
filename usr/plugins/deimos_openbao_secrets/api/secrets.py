"""Secrets CRUD API for Deimos OpenBao plugin.

Endpoint: POST /api/plugins/deimos_openbao_secrets/secrets

Actions: list, get, set, delete, bulk_set

LLM Isolation: This endpoint runs entirely between browser and OpenBao.
No LLM is involved at any point.
"""
import importlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from helpers.api import ApiHandler, Request, Response

logger = logging.getLogger(__name__)

# Plugin directory — resolved from this file's location
_PLUGIN_DIR = Path(__file__).resolve().parent.parent


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


def _load_config():
    """Load plugin config from config.json + default_config.yaml + env vars."""
    import yaml

    # Defaults
    defaults = {}
    default_path = _PLUGIN_DIR / "default_config.yaml"
    if default_path.exists():
        with open(default_path) as f:
            defaults = yaml.safe_load(f) or {}

    # Saved config
    saved = {}
    config_path = _PLUGIN_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                saved = json.load(f) or {}
        except Exception:
            saved = {}

    # Merge: saved overrides defaults
    cfg = {**defaults, **saved}

    # Env vars override everything
    env_map = {
        "OPENBAO_ENABLED": ("enabled", lambda v: v.lower() in ("true", "1", "yes")),
        "OPENBAO_URL": ("url", str),
        "OPENBAO_AUTH_METHOD": ("auth_method", str),
        "OPENBAO_MOUNT_POINT": ("mount_point", str),
        "OPENBAO_SECRETS_PATH": ("secrets_path", str),
        "OPENBAO_FALLBACK_TO_ENV": ("fallback_to_env", lambda v: v.lower() in ("true", "1", "yes")),
        "OPENBAO_TIMEOUT": ("timeout", float),
        "OPENBAO_TLS_VERIFY": ("tls_verify", lambda v: v.lower() in ("true", "1", "yes")),
        "OPENBAO_TLS_CA_CERT": ("tls_ca_cert", str),
    }
    for env_key, (cfg_key, converter) in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            try:
                cfg[cfg_key] = converter(val)
            except (ValueError, TypeError):
                pass

    return cfg


def _get_client():
    """Create an authenticated hvac client from config + env vars."""
    import hvac

    cfg = _load_config()

    url = cfg.get("url", "")
    if not url:
        raise RuntimeError("OpenBao URL not configured")

    tls_verify = cfg.get("tls_verify", True)
    tls_ca_cert = cfg.get("tls_ca_cert", "")
    timeout = cfg.get("timeout", 10)

    verify = tls_ca_cert if tls_ca_cert else tls_verify
    client = hvac.Client(url=url, verify=verify, timeout=timeout)

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

    return client, cfg


def _get_path(cfg, project_name: str = "") -> str:
    """Build the secrets path, optionally scoped to a project."""
    path = cfg.get("secrets_path", "agentzero")
    if project_name:
        path = f"{path}/{project_name}"
    return path


class SecretsManager(ApiHandler):
    """CRUD operations for OpenBao secrets."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not _ensure_hvac():
            return {"ok": False, "error": "Failed to install hvac library"}

        try:
            client, cfg = _get_client()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        import hvac.exceptions

        mount = cfg.get("mount_point", "secret")
        project_name = input.get("project_name", "")
        path = _get_path(cfg, project_name)
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
            elif action == "bulk_set":
                return self._bulk_set(client, mount, path, input.get("text", ""))
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

    def _read_all(self, client, mount: str, path: str) -> dict:
        """Read all secrets at path. Returns empty dict if path doesn't exist."""
        import hvac.exceptions
        try:
            resp = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount, raise_on_deleted_version=False
            )
            return resp.get("data", {}).get("data", {}) or {}
        except (hvac.exceptions.InvalidPath, Exception):
            return {}

    def _list(self, client, mount: str, path: str) -> dict:
        """List secret key names (values masked)."""
        data = self._read_all(client, mount, path)
        secrets = [{"key": k, "has_value": bool(data[k])} for k in sorted(data.keys())]
        return {"ok": True, "secrets": secrets}

    def _get(self, client, mount: str, path: str, key: str) -> dict:
        """Read a single secret value (for reveal)."""
        if not key:
            return {"ok": False, "error": "Key is required"}
        data = self._read_all(client, mount, path)
        if key not in data:
            return {"ok": False, "error": f"Key not found: {key}"}
        return {"ok": True, "key": key, "value": data[key]}

    def _set(self, client, mount: str, path: str, pairs: list) -> dict:
        """Write key-value pairs (read-modify-write to preserve existing)."""
        if not pairs:
            return {"ok": False, "error": "No key-value pairs provided"}
        current = self._read_all(client, mount, path)
        for pair in pairs:
            k = pair.get("key", "").strip()
            v = pair.get("value", "")
            if k:
                current[k] = v
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=current, mount_point=mount
        )
        return {"ok": True, "message": f"Saved {len(pairs)} secret(s)"}

    def _delete(self, client, mount: str, path: str, key: str) -> dict:
        """Delete a key (read-modify-write)."""
        if not key:
            return {"ok": False, "error": "Key is required"}
        data = self._read_all(client, mount, path)
        if key not in data:
            return {"ok": False, "error": f"Key not found: {key}"}
        del data[key]
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=data, mount_point=mount
        )
        return {"ok": True, "message": f"Deleted: {key}"}

    def _bulk_set(self, client, mount: str, path: str, text: str) -> dict:
        """Parse KEY=VALUE pairs from text (one per line) and write to OpenBao."""
        if not text or not text.strip():
            return {"ok": False, "error": "No text provided"}
        pairs = []
        errors = []
        for i, line in enumerate(text.strip().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                errors.append(f"Line {i}: no ‘=’ found")
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if not key:
                errors.append(f"Line {i}: empty key")
                continue
            pairs.append({"key": key, "value": value})
        if errors:
            return {"ok": False, "error": "Parse errors: " + "; ".join(errors)}
        if not pairs:
            return {"ok": False, "error": "No valid KEY=VALUE pairs found"}
        return self._set(client, mount, path, pairs)
