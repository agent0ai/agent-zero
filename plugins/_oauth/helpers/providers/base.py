from __future__ import annotations

import json
import os
import tempfile
import importlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


CODEX_PROVIDER_ID = "codex_oauth"
GITHUB_COPILOT_PROVIDER_ID = "github_copilot_oauth"
GEMINI_API_PROVIDER_ID = "gemini_api_oauth"
XAI_GROK_PROVIDER_ID = "xai_grok_oauth"
DUMMY_API_KEY = "oauth"


class ProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "provider_error",
        status: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "error": self.message,
            "code": self.code,
            "status": self.status,
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class OAuthProviderMetadata:
    provider_id: str
    display_name: str
    short_name: str
    model_provider_id: str
    icon: str
    auth_flow: str
    default_model: str
    default_models: list[str] = field(default_factory=list)
    proxy_base_path: str = ""
    callback_path: str = ""
    supports_manual_callback: bool = False
    supports_enterprise_domain: bool = False
    supports_oauth_client_config: bool = False
    supports_quota_project: bool = False
    note: str = ""
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LoginStartResult:
    ok: bool
    provider_id: str
    flow: str
    auth_url: str = ""
    redirect_uri: str = ""
    attempt_id: str = ""
    verification_url: str = ""
    user_code: str = ""
    interval: int = 5
    expires_at: float = 0
    message: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LoginPollResult:
    ok: bool
    provider_id: str
    completed: bool = False
    account_label: str = ""
    account_id: str = ""
    interval: int = 5
    expires_at: float = 0
    expired: bool = False
    error: str = ""
    warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CallbackResult:
    ok: bool
    provider_id: str
    account_label: str = ""
    account_id: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OAuthProvider(Protocol):
    provider_id: str

    def metadata(self) -> OAuthProviderMetadata:
        ...

    def status(self) -> dict[str, Any]:
        ...

    def start_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginStartResult:
        ...

    def poll_login(self, input: dict[str, Any] | None = None, request: Any = None) -> LoginPollResult:
        ...

    def complete_callback(self, args: dict[str, Any], request: Any) -> CallbackResult:
        ...

    def manual_callback(self, input: dict[str, Any], request: Any) -> LoginPollResult:
        ...

    def models(self) -> list[str]:
        ...

    def disconnect(self) -> dict[str, Any]:
        ...

    def api_key(self) -> str:
        ...

    def register_routes(self, app: Any) -> None:
        ...


def provider_data_dir(provider_slug: str) -> Path:
    if not _valid_provider_slug(provider_slug):
        raise ProviderError(
            "Invalid OAuth provider storage slug.",
            code="invalid_provider_slug",
        )

    files = importlib.import_module("helpers.files")

    path = Path(
        files.get_abs_path(
            files.USER_DIR,
            files.PLUGINS_DIR,
            "_oauth",
            provider_slug,
        )
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def provider_auth_path(provider_slug: str) -> Path:
    return provider_data_dir(provider_slug) / "auth.json"


def _valid_provider_slug(provider_slug: str) -> bool:
    if not isinstance(provider_slug, str):
        return False
    if not provider_slug or provider_slug in {".", ".."}:
        return False
    if "/" in provider_slug or "\\" in provider_slug:
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in provider_slug)


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def write_private_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = ""
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        os.chmod(tmp_name, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)
        raise
    try:
        path.chmod(0o600)
    except OSError:
        pass


def public_error(exc: Exception) -> str:
    return str(exc) or exc.__class__.__name__
