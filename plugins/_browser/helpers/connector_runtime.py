from __future__ import annotations

import asyncio
import base64
import hashlib
import re
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from helpers import files

try:
    from helpers.ws import NAMESPACE
except Exception:
    NAMESPACE = "/ws"

try:
    from helpers.ws_manager import ConnectionNotFoundError, get_shared_ws_manager
except Exception:
    class ConnectionNotFoundError(RuntimeError):
        pass

    def get_shared_ws_manager():
        raise ConnectionNotFoundError("WebSocket manager is unavailable")

from plugins._a0_connector.helpers.ws_runtime import (
    clear_pending_browser_op,
    host_browser_metadata_for_context,
    host_browser_metadata_for_sid,
    select_host_browser_candidate_sid,
    select_host_browser_target_sid,
    store_pending_browser_op,
)
from plugins._browser.helpers import config as browser_config
from plugins._browser.helpers.url import normalize_url


BROWSER_OP_EVENT = "connector_browser_op"
BROWSER_OP_TIMEOUT = 120.0
HOST_BROWSER_SCREENSHOT_DIR = ("tmp", "browser", "host-screenshots")
CONTENT_HELPER_PATH = Path(__file__).resolve().parents[1] / "assets" / "browser-page-content.js"
MAX_ARTIFACT_SIZE_BYTES = 25 * 1024 * 1024
BASE64_DECODE_CHARS_PER_CHUNK = 64 * 1024
HOST_BROWSER_PRIVACY_POLICY_KEY = getattr(
    browser_config,
    "HOST_BROWSER_PRIVACY_POLICY_KEY",
    "host_browser_privacy_policy",
)
DEFAULT_HOST_BROWSER_PRIVACY_POLICY = getattr(
    browser_config,
    "DEFAULT_HOST_BROWSER_PRIVACY_POLICY",
    "allow",
)
HOST_BROWSER_PROFILE_MODE_KEY = getattr(
    browser_config,
    "HOST_BROWSER_PROFILE_MODE_KEY",
    "host_browser_profile_mode",
)
get_browser_config = browser_config.get_browser_config
_LOCAL_PROVIDERS = {"ollama", "lm_studio"}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "host.docker.internal"}
_SENSITIVE_ACTIONS = {"content", "detail", "evaluate", "screenshot", "screenshot_file"}
_KEY_ALIASES = {
    "cmd": "Meta",
    "command": "Meta",
    "control": "Control",
    "ctrl": "Control",
    "escape": "Escape",
    "esc": "Escape",
    "meta": "Meta",
    "option": "Alt",
    "return": "Enter",
    "space": "Space",
}
_REQUIRED_API_NAMES_RE = re.compile(
    r"const\s+REQUIRED_API_NAMES\s*=\s*Object\.freeze\(\[(?P<body>.*?)\]\);",
    re.S,
)
_HOST_BROWSER_REMOTE_DEBUGGING_HELP = (
    'For an already-open Chrome-family browser, open `chrome://inspect/#remote-debugging`, '
    'enable "Allow remote debugging for this browser instance", run `/browser host on`, '
    "and retry."
)
_REMOTE_DEBUGGING_ERROR_TOKENS = (
    "remote debugging",
    "remote-debugging",
    "devtoolsactiveport",
    "devtools endpoint",
    "cdp endpoint",
    "cannot connect to the host browser",
    "127.0.0.1:9222",
    "localhost:9222",
    "blocks playwright remote debugging",
)


class ConnectorBrowserRuntime:
    def __init__(self, context_id: str, agent: Any):
        self.context_id = str(context_id or "").strip()
        self.agent = agent

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        payload = self._payload_for_call(method, *args, **kwargs)
        warning = self._privacy_warning(payload)
        result = await self._dispatch(payload)
        result = self._materialize_artifact(result)
        if warning:
            if isinstance(result, dict):
                result.setdefault("privacy_warning", warning)
            else:
                result = {"result": result, "privacy_warning": warning}
        return result

    def _payload_for_call(self, method: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        action = str(method or "").strip().lower().replace("-", "_")
        payload: dict[str, Any] = {
            "op_id": str(uuid.uuid4()),
            "context_id": self.context_id,
            "action": action,
            "profile_mode": self._host_browser_profile_mode(),
        }

        if action == "open":
            payload["url"] = self._normalize_open_url(args[0] if args else "")
        elif action in {"state", "set_active", "back", "forward", "reload"}:
            payload["browser_id"] = args[0] if args else None
        elif action == "navigate":
            payload["browser_id"] = args[0] if args else None
            payload["url"] = normalize_url(args[1] if len(args) > 1 else "")
        elif action == "screenshot_file":
            payload["action"] = "screenshot"
            payload["browser_id"] = args[0] if args else None
            payload["quality"] = kwargs.get("quality", 80)
            payload["full_page"] = kwargs.get("full_page", False)
            payload["path"] = kwargs.get("path", "")
        elif action == "list":
            payload["include_content"] = kwargs.get("include_content", False)
        elif action == "content":
            payload["browser_id"] = args[0] if args else None
            payload["payload"] = args[1] if len(args) > 1 and isinstance(args[1], dict) else None
        elif action == "detail":
            payload["browser_id"] = args[0] if args else None
            payload["ref"] = args[1] if len(args) > 1 else None
        elif action == "evaluate":
            payload["browser_id"] = args[0] if args else None
            payload["script"] = args[1] if len(args) > 1 else ""
        elif action == "click":
            payload["browser_id"] = args[0] if args else None
            payload["ref"] = args[1] if len(args) > 1 else None
            payload["modifiers"] = kwargs.get("modifiers")
            payload["focus_popup"] = kwargs.get("focus_popup")
        elif action in {"type", "submit", "type_submit", "scroll"}:
            payload["browser_id"] = args[0] if args else None
            payload["ref"] = args[1] if len(args) > 1 else None
            if action in {"type", "type_submit"}:
                payload["text"] = args[2] if len(args) > 2 else ""
        elif action in {"hover", "double_click", "right_click", "drag"}:
            payload["browser_id"] = args[0] if args else None
            payload.update(kwargs)
        elif action == "wheel":
            payload["browser_id"] = args[0] if args else None
            payload["x"] = args[1] if len(args) > 1 else 0
            payload["y"] = args[2] if len(args) > 2 else 0
            payload["delta_x"] = args[3] if len(args) > 3 else 0
            payload["delta_y"] = args[4] if len(args) > 4 else 0
        elif action == "mouse":
            payload["browser_id"] = args[0] if args else None
            payload["event_type"] = args[1] if len(args) > 1 else "click"
            payload["x"] = args[2] if len(args) > 2 else 0
            payload["y"] = args[3] if len(args) > 3 else 0
            payload["button"] = kwargs.get("button", args[4] if len(args) > 4 else "left")
            payload["modifiers"] = kwargs.get("modifiers")
        elif action == "keyboard":
            payload["browser_id"] = args[0] if args else None
            payload["key"] = kwargs.get("key", "")
            payload["text"] = kwargs.get("text", "")
        elif action == "key_chord":
            payload["browser_id"] = args[0] if args else None
            payload["keys"] = self._normalize_keys(args[1] if len(args) > 1 else [])
        elif action == "clipboard":
            payload["browser_id"] = args[0] if args else None
            payload["clipboard_action"] = kwargs.get("action", "")
            payload["text"] = kwargs.get("text", "")
        elif action == "set_viewport":
            payload["browser_id"] = args[0] if args else None
            payload["width"] = args[1] if len(args) > 1 else 0
            payload["height"] = args[2] if len(args) > 2 else 0
        elif action in {"select_option", "set_checked", "upload_file"}:
            payload["browser_id"] = args[0] if args else None
            payload["ref"] = args[1] if len(args) > 1 else None
            payload.update(kwargs)
        elif action == "multi":
            payload["calls"] = self._normalize_multi_calls(args[0] if args else [])
        elif action == "close_browser":
            payload["action"] = "close"
            payload["browser_id"] = args[0] if args else None
        elif action == "close_all_browsers":
            payload["action"] = "close_all"
        else:
            payload.update(kwargs)

        return payload

    @staticmethod
    def _normalize_open_url(value: Any) -> str:
        raw = str(value or "").strip()
        return normalize_url(raw) if raw else ""

    @classmethod
    def _normalize_multi_calls(cls, calls: Any) -> Any:
        if not isinstance(calls, list):
            return calls
        normalized_calls: list[Any] = []
        for call in calls:
            if not isinstance(call, dict):
                normalized_calls.append(call)
                continue
            normalized = dict(call)
            action = str(normalized.get("action") or "").strip().lower().replace("-", "_")
            if action == "open":
                normalized["url"] = cls._normalize_open_url(normalized.get("url"))
            elif action == "navigate":
                normalized["url"] = normalize_url(normalized.get("url", ""))
            elif action == "click" and not normalized.get("ref") and (
                normalized.get("x") or normalized.get("y")
            ):
                normalized["action"] = "mouse"
                normalized.setdefault("event_type", "click")
                normalized.setdefault("button", "left")
            elif action == "type" and not normalized.get("ref"):
                normalized["action"] = "keyboard"
                normalized.setdefault("key", "")
            elif action in {"key_chord", "keychord"}:
                normalized["keys"] = cls._normalize_keys(normalized.get("keys"))
            elif action == "multi" or isinstance(normalized.get("calls"), list):
                normalized["calls"] = cls._normalize_multi_calls(normalized.get("calls", []))
            normalized_calls.append(normalized)
        return normalized_calls

    @staticmethod
    def _normalize_keys(keys: Any) -> list[str]:
        if keys is None:
            return []
        if isinstance(keys, str):
            raw = re.split(r"\s*\+\s*|\s*,\s*", keys.strip())
        elif isinstance(keys, list):
            raw = keys
        else:
            raw = [str(keys)]
        normalized: list[str] = []
        for key in raw:
            value = str(key or "").strip()
            if not value:
                continue
            normalized.append(
                _KEY_ALIASES.get(
                    value.lower(),
                    value.upper() if len(value) == 1 and value.isalpha() else value,
                )
            )
        return normalized

    async def _dispatch(self, payload: dict[str, Any]) -> Any:
        payload.setdefault("profile_mode", self._host_browser_profile_mode())
        self._enforce_privacy(payload)
        sid = self._select_sid()
        if not sid:
            statuses = host_browser_metadata_for_context(self.context_id)
            raise RuntimeError(self._host_browser_unavailable_message(statuses))

        if self._needs_prepare(sid, payload):
            await self._send_browser_op(
                sid,
                self._with_content_helper(
                    sid,
                    {
                        "op_id": str(uuid.uuid4()),
                        "context_id": self.context_id,
                        "action": "ensure",
                        "profile_mode": self._host_browser_profile_mode(),
                    },
                ),
            )
            sid = self._select_sid() or sid

        return await self._send_browser_op(sid, self._with_content_helper(sid, payload))

    def _host_browser_profile_mode(self) -> str:
        config = get_browser_config(self.agent)
        mode = str(config.get(HOST_BROWSER_PROFILE_MODE_KEY) or "existing").strip().lower()
        return "agent" if mode == "agent" else "existing"

    def _with_content_helper(self, sid: str, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = host_browser_metadata_for_sid(sid) or {}
        if str(metadata.get("content_helper_sha256") or "").strip().lower() == _content_helper_sha256():
            return payload
        payload = dict(payload)
        payload["content_helper"] = _content_helper_payload()
        return payload

    async def _send_browser_op(self, sid: str, payload: dict[str, Any]) -> Any:
        op_id = str(payload["op_id"])
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        store_pending_browser_op(
            op_id,
            sid=sid,
            future=future,
            loop=loop,
            context_id=self.context_id,
        )
        try:
            await get_shared_ws_manager().emit_to(
                NAMESPACE,
                sid,
                BROWSER_OP_EVENT,
                payload,
                handler_id=f"{self.__class__.__module__}.{self.__class__.__name__}",
            )
            response = await asyncio.wait_for(future, timeout=BROWSER_OP_TIMEOUT)
        except ConnectionNotFoundError as exc:
            raise RuntimeError(
                "The selected A0 CLI disconnected before the host browser request could be delivered."
            ) from exc
        except asyncio.TimeoutError as exc:
            raise RuntimeError(
                f"Timed out waiting for A0 CLI host browser action={payload.get('action')!r}."
            ) from exc
        finally:
            clear_pending_browser_op(op_id)

        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected host browser response: {response!r}")
        if not response.get("ok"):
            raise RuntimeError(
                self._host_browser_error_message(
                    response.get("error") or "Host browser operation failed"
                )
            )
        return response.get("result")

    def _select_sid(self) -> str | None:
        return (
            select_host_browser_target_sid(self.context_id)
            or select_host_browser_candidate_sid(self.context_id)
        )

    def _needs_prepare(self, sid: str, payload: dict[str, Any]) -> bool:
        action = str(payload.get("action") or "").strip().lower().replace("-", "_")
        if action in {"status", "ensure"}:
            return False
        metadata = host_browser_metadata_for_sid(sid) or {}
        return not (
            metadata.get("enabled")
            and str(metadata.get("status") or "").strip() in {"ready", "active"}
        )

    def _enforce_privacy(self, payload: dict[str, Any]) -> None:
        policy = str(
            get_browser_config(agent=self.agent).get(HOST_BROWSER_PRIVACY_POLICY_KEY)
            or DEFAULT_HOST_BROWSER_PRIVACY_POLICY
        ).strip()
        if not self._payload_is_sensitive(payload) or policy != "enforce_local":
            return
        if _agent_uses_local_chat_model(self.agent):
            return
        raise RuntimeError(
            "Host-browser content is blocked by Browser privacy policy. "
            "Switch this project to a local chat model, or change Browser settings from "
            "enforce_local to warn/allow."
        )

    def _privacy_warning(self, payload: dict[str, Any]) -> str:
        policy = str(
            get_browser_config(agent=self.agent).get(HOST_BROWSER_PRIVACY_POLICY_KEY)
            or DEFAULT_HOST_BROWSER_PRIVACY_POLICY
        ).strip()
        if policy != "warn" or not self._payload_is_sensitive(payload):
            return ""
        if _agent_uses_local_chat_model(self.agent):
            return ""
        return (
            "Browser privacy policy is warn: host-browser content was returned while "
            "the active chat model does not appear local."
        )

    def _payload_is_sensitive(self, payload: dict[str, Any]) -> bool:
        action = str(payload.get("action") or "").strip().lower().replace("-", "_")
        if action in _SENSITIVE_ACTIONS:
            return True
        if action == "list" and bool(payload.get("include_content")):
            return True
        if action == "multi":
            calls = payload.get("calls")
            if isinstance(calls, list):
                return any(
                    self._payload_is_sensitive(call)
                    for call in calls
                    if isinstance(call, dict)
                )
        return False

    def _materialize_artifact(self, result: Any) -> Any:
        if isinstance(result, list):
            materialized_list = []
            for item in result:
                if isinstance(item, dict) and isinstance(item.get("result"), dict):
                    next_item = dict(item)
                    next_item["result"] = self._materialize_artifact(next_item["result"])
                    materialized_list.append(next_item)
                else:
                    materialized_list.append(item)
            return materialized_list
        if not isinstance(result, dict):
            return result
        artifact = result.get("artifact")
        if not isinstance(artifact, dict):
            return result
        if str(artifact.get("encoding", "")).lower() != "base64":
            return result
        data = str(artifact.get("data") or "")
        if not data:
            return result
        estimated_size = _estimated_base64_decoded_size(data)
        if estimated_size > MAX_ARTIFACT_SIZE_BYTES:
            raise RuntimeError(
                "Host browser artifact is too large to materialize safely "
                f"({estimated_size} bytes, limit {MAX_ARTIFACT_SIZE_BYTES} bytes)."
            )
        filename = _safe_filename(str(artifact.get("filename") or "host-browser.jpg"))
        target_dir = Path(files.get_abs_path(*HOST_BROWSER_SCREENSHOT_DIR, self.context_id))
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        try:
            _write_base64_to_path(data, target_path)
        except Exception as exc:
            target_path.unlink(missing_ok=True)
            raise RuntimeError("Host browser artifact could not be decoded.") from exc
        materialized = dict(result)
        materialized.pop("artifact", None)
        local_path = str(target_path)
        materialized["path"] = local_path
        materialized["a0_path"] = files.normalize_a0_path(local_path)
        materialized["vision_load"] = {
            "tool_name": "vision_load",
            "tool_args": {"paths": [local_path]},
        }
        return materialized

    @staticmethod
    def _format_statuses(statuses: list[dict[str, Any]]) -> str:
        parts = []
        for status in statuses:
            parts.append(
                f"sid={status.get('sid')} status={status.get('status')} "
                f"supported={status.get('supported')} can_prepare={status.get('can_prepare')} "
                f"enabled={status.get('enabled')} "
                f"reason={status.get('support_reason') or 'none'}"
            )
        return "; ".join(parts)

    @classmethod
    def _host_browser_unavailable_message(cls, statuses: list[dict[str, Any]]) -> str:
        detail = cls._format_statuses(statuses)
        message = (
            "Host browser is required but no subscribed A0 CLI advertises host-browser support"
            + (f": {detail}" if detail else ".")
        )
        return cls._host_browser_error_message(message)

    @staticmethod
    def _host_browser_error_message(error: Any) -> str:
        message = str(error or "Host browser operation failed").strip()
        if not message:
            message = "Host browser operation failed"
        normalized = message.lower()
        if "chrome://inspect/#remote-debugging" in normalized:
            return message
        if any(token in normalized for token in _REMOTE_DEBUGGING_ERROR_TOKENS):
            return f"{message}\n\n{_HOST_BROWSER_REMOTE_DEBUGGING_HELP}"
        return message


@lru_cache(maxsize=1)
def _content_helper_payload() -> dict[str, Any]:
    try:
        source = CONTENT_HELPER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Host-browser content helper could not be read from {CONTENT_HELPER_PATH}: {exc}"
        ) from exc
    return {
        "required_apis": _content_helper_required_apis(source),
        "source": source,
        "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


def _content_helper_sha256() -> str:
    return str(_content_helper_payload()["sha256"])


def _content_helper_required_apis(source: str) -> list[str]:
    match = _REQUIRED_API_NAMES_RE.search(source)
    if not match:
        raise RuntimeError(
            f"Host-browser content helper from {CONTENT_HELPER_PATH} does not declare REQUIRED_API_NAMES."
        )
    names = re.findall(r'"([^"]+)"', match.group("body"))
    if not names:
        raise RuntimeError(
            f"Host-browser content helper from {CONTENT_HELPER_PATH} declares no required API names."
        )
    return names


def _agent_uses_local_chat_model(agent: Any) -> bool:
    try:
        from plugins._model_config.helpers import model_config

        cfg = model_config.get_chat_model_config(agent)
    except Exception:
        cfg = {}
    if not isinstance(cfg, dict):
        return False
    provider = str(cfg.get("provider", "") or "").strip().lower()
    if provider in _LOCAL_PROVIDERS:
        return True
    api_base = str(cfg.get("api_base", "") or cfg.get("base_url", "") or "").strip()
    if not api_base:
        kwargs = cfg.get("kwargs")
        if isinstance(kwargs, dict):
            api_base = str(kwargs.get("api_base", "") or kwargs.get("base_url", "") or "").strip()
    return _api_base_is_local(api_base)


def _api_base_is_local(api_base: str) -> bool:
    if not api_base:
        return False
    parsed = urlparse(api_base if "://" in api_base else f"http://{api_base}")
    hostname = (parsed.hostname or "").strip().lower()
    return hostname in _LOCAL_HOSTS


def _safe_filename(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value)
    cleaned = cleaned.strip("._") or f"host-browser-{uuid.uuid4().hex}.jpg"
    if "." not in cleaned:
        cleaned += ".jpg"
    return cleaned


def _estimated_base64_decoded_size(data: str) -> int:
    compact_length = sum(1 for char in data if not char.isspace())
    return (compact_length * 3) // 4


def _write_base64_to_path(data: str, target_path: Path) -> None:
    pending = ""
    with target_path.open("wb") as target:
        for offset in range(0, len(data), BASE64_DECODE_CHARS_PER_CHUNK):
            chunk = pending + "".join(
                char
                for char in data[offset : offset + BASE64_DECODE_CHARS_PER_CHUNK]
                if not char.isspace()
            )
            ready_length = (len(chunk) // 4) * 4
            if ready_length:
                target.write(base64.b64decode(chunk[:ready_length], validate=True))
            pending = chunk[ready_length:]
        if pending:
            target.write(base64.b64decode(pending, validate=True))
