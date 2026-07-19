from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from plugins._orchestrator.helpers.adapters.base import TerminalAgentAdapter

# Codex CLI's public OAuth client (same constants the official CLI uses;
# see also plugins/_oauth for the reference implementation).
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
ISSUER = "https://auth.openai.com"
TOKEN_URL = "https://auth.openai.com/oauth/token"
AUTH_FILENAME = "auth.json"
DEVICE_CODE_TIMEOUT_SECONDS = 15 * 60


class CodexAdapter(TerminalAgentAdapter):
    id = "codex"
    title = "OpenAI Codex CLI"
    binary = "codex"
    install_hint = "npm install -g @openai/codex"
    description = "OpenAI Codex CLI for autonomous coding tasks in a workdir."

    # --- authentication ----------------------------------------------------

    def _plugin_auth_path(self) -> Path:
        return self.data_dir() / AUTH_FILENAME

    def _external_auth_path(self) -> Path:
        codex_home = os.environ.get("CODEX_HOME", "").strip()
        if codex_home:
            return Path(codex_home).expanduser() / AUTH_FILENAME
        return Path.home() / ".codex" / AUTH_FILENAME

    def auth_status(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        plugin_path = self._plugin_auth_path()
        if _has_chatgpt_tokens(plugin_path):
            return {
                "connected": True,
                "mode": "plugin",
                "auth_path": str(plugin_path),
            }
        external_path = self._external_auth_path()
        if _has_chatgpt_tokens(external_path):
            return {
                "connected": True,
                "mode": "external",
                "auth_path": str(external_path),
            }
        return {"connected": False, "mode": "", "auth_path": ""}

    def supports_device_login(self) -> bool:
        return True

    def start_device_login(self) -> dict[str, Any]:
        response = requests.post(
            f"{ISSUER}/api/accounts/deviceauth/usercode",
            headers={"Content-Type": "application/json"},
            json={"client_id": CLIENT_ID},
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(_oauth_error(response))
        payload = response.json() if isinstance(response.json(), dict) else {}
        device_auth_id = str(payload.get("device_auth_id") or "")
        user_code = str(payload.get("user_code") or payload.get("usercode") or "")
        if not device_auth_id or not user_code:
            raise RuntimeError("Device authorization response did not include a code.")
        return {
            "device_auth_id": device_auth_id,
            "user_code": user_code,
            "interval": _safe_int(payload.get("interval"), 5),
            "expires_at": time.time() + DEVICE_CODE_TIMEOUT_SECONDS,
            "verification_url": f"{ISSUER}/codex/device",
        }

    def poll_device_login(self, payload: dict[str, Any]) -> dict[str, Any]:
        device_auth_id = str(payload.get("device_auth_id") or "")
        user_code = str(payload.get("user_code") or "")
        if not device_auth_id or not user_code:
            raise RuntimeError("Missing device_auth_id or user_code.")
        response = requests.post(
            f"{ISSUER}/api/accounts/deviceauth/token",
            headers={"Content-Type": "application/json"},
            json={"device_auth_id": device_auth_id, "user_code": user_code},
            timeout=30,
        )
        if response.status_code in {403, 404}:
            return {"completed": False}
        if not response.ok:
            raise RuntimeError(_oauth_error(response))
        data = response.json() if isinstance(response.json(), dict) else {}
        authorization_code = str(data.get("authorization_code") or "")
        verifier = str(data.get("code_verifier") or "")
        if not authorization_code or not verifier:
            raise RuntimeError("Device authorization response missing exchange data.")
        tokens = _exchange_code(
            authorization_code, f"{ISSUER}/deviceauth/callback", verifier
        )
        account_id = _derive_account_id(tokens["id_token"])
        self._write_auth(tokens, account_id)
        return {"completed": True, "account_id": account_id}

    def can_disconnect(self, config: dict[str, Any] | None = None) -> bool:
        status = self.auth_status(config)
        return bool(status.get("connected"))

    def disconnect(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        status = self.auth_status(config)
        path = self._plugin_auth_path()
        if status.get("mode") == "plugin" and path.exists():
            path.unlink()
            return {"removed": True, "mode": "plugin"}
        if status.get("mode") == "external":
            result = subprocess.run(
                [self.resolve_binary(config), "logout"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout).strip())
            return {"removed": True, "mode": "external"}
        return {"removed": False, "message": "No Codex credentials found."}

    def _write_auth(self, tokens: dict[str, str], account_id: str) -> None:
        auth_data = {
            "auth_mode": "chatgpt",
            "OPENAI_API_KEY": None,
            "tokens": {
                "id_token": tokens["id_token"],
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "account_id": account_id,
            },
            "last_refresh": _utc_now_iso(),
        }
        path = self._plugin_auth_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(auth_data, indent=2))
        os.chmod(tmp, 0o600)
        tmp.replace(path)


def _has_chatgpt_tokens(path: Path) -> bool:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    tokens = data.get("tokens") if isinstance(data, dict) else None
    if not isinstance(tokens, dict):
        return False
    return bool(tokens.get("access_token") and tokens.get("refresh_token"))


def _exchange_code(code: str, redirect_uri: str, verifier: str) -> dict[str, str]:
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": CLIENT_ID,
            "code_verifier": verifier,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(_oauth_error(response))
    payload = response.json() if isinstance(response.json(), dict) else {}
    tokens = {
        "id_token": str(payload.get("id_token") or ""),
        "access_token": str(payload.get("access_token") or ""),
        "refresh_token": str(payload.get("refresh_token") or ""),
    }
    missing = [key for key, value in tokens.items() if not value]
    if missing:
        raise RuntimeError(f"OAuth token response is missing: {', '.join(missing)}")
    return tokens


def _derive_account_id(id_token: str) -> str:
    claims = _parse_jwt_claims(id_token)
    auth_claims = claims.get("https://api.openai.com/auth")
    if isinstance(auth_claims, dict):
        value = auth_claims.get("chatgpt_account_id")
        if isinstance(value, str):
            return value
    return ""


def _parse_jwt_claims(token: str) -> dict[str, Any]:
    import base64

    try:
        payload_part = token.split(".")[1]
        padded = payload_part + "=" * (-len(payload_part) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _oauth_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = None
    if isinstance(payload, dict):
        for key in ("error_description", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return f"OAuth endpoint returned status {response.status_code}."


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
