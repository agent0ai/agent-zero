from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests

from helpers import files
from plugins._oauth.helpers.config import codex_config


AUTH_FILENAME = "auth.json"
ACCESS_EXPIRY_MARGIN = timedelta(minutes=5)
REFRESH_INTERVAL = timedelta(minutes=55)
FALLBACK_CODEX_VERSION = "0.124.0"
OAUTH_ERROR_KEYS = {"error", "error_description"}
DEVICE_CODE_TIMEOUT_SECONDS = 15 * 60
USAGE_ENDPOINT_PATHS = (
    "/backend-api/codex/usage",
    "/backend-api/wham/usage",
    "/api/codex/usage",
)


@dataclass(frozen=True)
class PkcePair:
    verifier: str
    challenge: str


@dataclass(frozen=True)
class EffectiveAuth:
    access_token: str
    account_id: str
    id_token: str = ""
    refresh_token: str = ""
    source_path: str = ""
    last_refresh: str = ""


def generate_pkce() -> PkcePair:
    verifier = _base64url(secrets.token_bytes(64))
    challenge = _base64url(hashlib.sha256(verifier.encode("utf-8")).digest())
    return PkcePair(verifier=verifier, challenge=challenge)


def generate_state() -> str:
    return _base64url(secrets.token_bytes(32))


def build_authorize_url(redirect_uri: str, state: str, pkce: PkcePair) -> str:
    cfg = codex_config()
    query = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": " ".join(cfg["scopes"]),
        "code_challenge": pkce.challenge,
        "code_challenge_method": "S256",
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "state": state,
        "originator": "codex_cli_rs",
    }
    if cfg["forced_workspace_id"]:
        query["allowed_workspace_id"] = cfg["forced_workspace_id"]

    return f'{cfg["issuer"]}/oauth/authorize?{urlencode(query)}'


def exchange_code_for_tokens(
    code: str,
    redirect_uri: str,
    verifier: str,
) -> dict[str, str]:
    cfg = codex_config()
    response = requests.post(
        cfg["token_url"],
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": cfg["client_id"],
            "code_verifier": verifier,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(_token_error_message(response))

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("OAuth token endpoint returned a malformed response.")

    tokens = {
        "id_token": str(payload.get("id_token") or ""),
        "access_token": str(payload.get("access_token") or ""),
        "refresh_token": str(payload.get("refresh_token") or ""),
    }
    missing = [key for key, value in tokens.items() if not value]
    if missing:
        raise RuntimeError(f"OAuth token response is missing: {', '.join(missing)}")

    return tokens


def obtain_api_key(id_token: str) -> str:
    cfg = codex_config()
    response = requests.post(
        cfg["token_url"],
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "client_id": cfg["client_id"],
            "requested_token": "openai-api-key",
            "subject_token": id_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"API-key token exchange failed with status {response.status_code}.")
    payload = response.json()
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError("API-key token exchange returned a malformed response.")
    return str(payload["access_token"])


def complete_login(code: str, redirect_uri: str, verifier: str) -> EffectiveAuth:
    tokens = exchange_code_for_tokens(code, redirect_uri, verifier)
    return persist_exchanged_tokens(tokens)


def persist_exchanged_tokens(tokens: dict[str, str]) -> EffectiveAuth:
    id_token = tokens["id_token"]
    account_id = derive_account_id(id_token)
    if not account_id:
        raise RuntimeError("OAuth ID token did not include a ChatGPT account id.")

    cfg = codex_config()
    if cfg["forced_workspace_id"] and account_id != cfg["forced_workspace_id"]:
        raise RuntimeError(
            f'Login is restricted to workspace id {cfg["forced_workspace_id"]}.'
        )

    try:
        api_key = obtain_api_key(id_token)
    except Exception:
        api_key = ""

    auth_data = {
        "auth_mode": "chatgpt",
        "OPENAI_API_KEY": api_key or None,
        "tokens": {
            "id_token": id_token,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "account_id": account_id,
        },
        "last_refresh": utc_now_iso(),
    }
    path = resolve_auth_write_path()
    write_auth_file(path, auth_data)
    return load_auth(ensure_fresh=False)


def request_device_code() -> dict[str, Any]:
    cfg = codex_config()
    base_url = cfg["issuer"].rstrip("/")
    response = requests.post(
        f"{base_url}/api/accounts/deviceauth/usercode",
        headers={"Content-Type": "application/json"},
        json={"client_id": cfg["client_id"]},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(_token_error_message(response))

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Device authorization returned a malformed response.")

    device_auth_id = _string(payload.get("device_auth_id"))
    user_code = _string(payload.get("user_code") or payload.get("usercode"))
    if not device_auth_id or not user_code:
        raise RuntimeError("Device authorization response did not include a code.")

    interval = _safe_int(payload.get("interval"), 5)
    expires_at = _device_expires_at(payload.get("expires_at"))
    return {
        "device_auth_id": device_auth_id,
        "user_code": user_code,
        "interval": interval,
        "expires_at": expires_at,
        "verification_url": f"{base_url}/codex/device",
    }


def poll_device_authorization(device_auth_id: str, user_code: str) -> dict[str, Any]:
    cfg = codex_config()
    base_url = cfg["issuer"].rstrip("/")
    response = requests.post(
        f"{base_url}/api/accounts/deviceauth/token",
        headers={"Content-Type": "application/json"},
        json={"device_auth_id": device_auth_id, "user_code": user_code},
        timeout=30,
    )

    if response.status_code in {403, 404}:
        return {"completed": False}
    if not response.ok:
        raise RuntimeError(_token_error_message(response))

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Device authorization token response was malformed.")
    authorization_code = _string(payload.get("authorization_code"))
    verifier = _string(payload.get("code_verifier"))
    if not authorization_code or not verifier:
        raise RuntimeError("Device authorization response was missing token exchange data.")

    tokens = exchange_code_for_tokens(
        authorization_code,
        f"{base_url}/deviceauth/callback",
        verifier,
    )
    auth = persist_exchanged_tokens(tokens)
    return {"completed": True, "account_id": auth.account_id}


def load_auth(*, ensure_fresh: bool = True) -> EffectiveAuth:
    path, data = read_auth_file()
    tokens = data.get("tokens") if isinstance(data, dict) else {}
    tokens = tokens if isinstance(tokens, dict) else {}

    access_token = _string(tokens.get("access_token"))
    id_token = _string(tokens.get("id_token"))
    refresh_token = _string(tokens.get("refresh_token"))
    account_id = _string(tokens.get("account_id")) or derive_account_id(id_token)
    last_refresh = _string(data.get("last_refresh")) if isinstance(data, dict) else ""

    if ensure_fresh and refresh_token and should_refresh(access_token, last_refresh):
        refreshed = refresh_tokens(refresh_token)
        access_token = refreshed.get("access_token") or access_token
        id_token = refreshed.get("id_token") or id_token
        refresh_token = refreshed.get("refresh_token") or refresh_token
        account_id = derive_account_id(id_token) or account_id
        last_refresh = utc_now_iso()
        data["tokens"] = {
            "id_token": id_token,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "account_id": account_id,
        }
        data["last_refresh"] = last_refresh
        write_auth_file(path, data)

    if not access_token:
        raise RuntimeError("Codex/ChatGPT account access token not found. Connect the account first.")
    if not account_id:
        raise RuntimeError("Codex/ChatGPT account id not found. Connect the account again.")

    return EffectiveAuth(
        access_token=access_token,
        account_id=account_id,
        id_token=id_token,
        refresh_token=refresh_token,
        source_path=str(path),
        last_refresh=last_refresh,
    )


def status() -> dict[str, Any]:
    candidates = resolve_auth_file_candidates()
    existing = [str(path) for path in candidates if path.is_file()]
    result: dict[str, Any] = {
        "connected": False,
        "auth_file_path": str(resolve_auth_write_path()),
        "discovered_auth_files": existing,
    }
    try:
        auth = load_auth(ensure_fresh=False)
    except Exception as exc:
        result["message"] = str(exc)
        return result

    id_claims = parse_jwt_claims(auth.id_token)
    access_claims = parse_jwt_claims(auth.access_token)
    auth_claims = _auth_claims(id_claims)
    result.update(
        {
            "connected": True,
            "auth_file_path": auth.source_path,
            "account_id": auth.account_id,
            "email": id_claims.get("email")
            or _record(id_claims.get("https://api.openai.com/profile")).get("email"),
            "plan_type": auth_claims.get("chatgpt_plan_type"),
            "user_id": auth_claims.get("chatgpt_user_id") or auth_claims.get("user_id"),
            "access_expires_at": _jwt_expiration_iso(access_claims),
            "last_refresh": auth.last_refresh,
        }
    )
    try:
        result["usage"] = fetch_usage()
    except Exception as exc:
        result["usage"] = {"available": False, "error": str(exc)}
    return result


def disconnect_auth() -> dict[str, Any]:
    cleared_paths: list[str] = []
    removed_paths: list[str] = []
    preserved_paths: list[str] = []

    for path in resolve_auth_file_candidates():
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue
        if not isinstance(data, dict) or not _contains_chatgpt_auth(data):
            continue

        cleaned = dict(data)
        cleaned.pop("tokens", None)
        cleaned.pop("last_refresh", None)
        if _string(cleaned.get("auth_mode")).lower() == "chatgpt":
            cleaned.pop("auth_mode", None)

        cleared_paths.append(str(path))
        if _has_meaningful_auth_data(cleaned):
            write_auth_file(path, cleaned)
            preserved_paths.append(str(path))
            continue

        path.unlink(missing_ok=True)
        removed_paths.append(str(path))

    return {
        "disconnected": bool(cleared_paths),
        "cleared_auth_files": cleared_paths,
        "removed_auth_files": removed_paths,
        "preserved_auth_files": preserved_paths,
    }


def fetch_usage() -> dict[str, Any]:
    cfg = codex_config()
    auth = load_auth()
    errors: list[str] = []
    headers = {
        "Authorization": f"Bearer {auth.access_token}",
        "ChatGPT-Account-Id": auth.account_id,
        "Accept": "application/json",
        "User-Agent": "codex-cli",
    }

    for url in usage_endpoint_candidates(cfg["upstream_base_url"]):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=max(5, min(cfg["request_timeout_seconds"], 30)),
            )
        except Exception as exc:
            errors.append(str(exc))
            continue

        if not response.ok:
            errors.append(upstream_error_message(response, "Failed to load Codex usage."))
            continue

        try:
            payload = response.json()
        except Exception:
            payload = {}
        usage = normalize_usage_payload(payload, response.headers)
        if usage["available"]:
            usage["endpoint_path"] = urlparse(url).path
            return usage
        errors.append("Usage endpoint returned no rate-limit data.")

    suffix = f" {' '.join(errors[-2:])}" if errors else ""
    raise RuntimeError(f"Failed to load Codex usage.{suffix}")


def usage_endpoint_candidates(upstream_base_url: str) -> list[str]:
    parsed = urlparse(upstream_base_url)
    if not parsed.scheme or not parsed.netloc:
        return []

    root = f"{parsed.scheme}://{parsed.netloc}"
    paths = list(USAGE_ENDPOINT_PATHS)
    upstream_path = parsed.path.rstrip("/")
    if upstream_path and upstream_path.endswith("/codex"):
        paths.insert(0, f"{upstream_path}/usage")

    result: list[str] = []
    seen: set[str] = set()
    for path in paths:
        url = urljoin(root.rstrip("/") + "/", path.lstrip("/"))
        if url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def normalize_usage_payload(
    payload: Mapping[str, Any] | None,
    headers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = payload if isinstance(payload, Mapping) else {}
    rate_limit = _record(body.get("rate_limit")) or _record(body.get("rateLimits"))
    header_usage = _normalize_usage_headers(headers or {})

    primary = (
        _normalize_usage_window(rate_limit.get("primary_window"))
        or _normalize_usage_window(rate_limit.get("primary"))
        or _normalize_usage_window(body.get("primary_window"))
        or header_usage.get("primary")
    )
    secondary = (
        _normalize_usage_window(rate_limit.get("secondary_window"))
        or _normalize_usage_window(rate_limit.get("secondary"))
        or _normalize_usage_window(body.get("secondary_window"))
        or header_usage.get("secondary")
    )
    code_review = _normalize_code_review_usage(body.get("code_review_rate_limit"))
    additional = _normalize_additional_rate_limits(rate_limit.get("additional_rate_limits"))
    credits = _normalize_credits(body.get("credits"))
    plan_type = (
        _string(body.get("plan_type"))
        or _string(body.get("planType"))
        or _string(header_usage.get("plan_type"))
    )

    return {
        "available": bool(primary or secondary or code_review or additional),
        "plan_type": plan_type,
        "primary": primary,
        "secondary": secondary,
        "code_review": code_review,
        "additional": additional,
        "credits": credits,
        "rate_limit_reached_type": _string(
            rate_limit.get("rate_limit_reached_type")
            or rate_limit.get("rateLimitReachedType")
            or body.get("rate_limit_reached_type")
            or body.get("rateLimitReachedType")
        ),
    }


def refresh_tokens(refresh_token: str) -> dict[str, str]:
    cfg = codex_config()
    response = requests.post(
        cfg["token_url"],
        headers={"Content-Type": "application/json"},
        json={
            "client_id": cfg["client_id"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(_token_error_message(response))

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("OAuth refresh endpoint returned a malformed response.")

    return {
        "id_token": _string(payload.get("id_token")),
        "access_token": _string(payload.get("access_token")),
        "refresh_token": _string(payload.get("refresh_token")) or refresh_token,
    }


def should_refresh(access_token: str, last_refresh: str) -> bool:
    if not access_token:
        return True

    claims = parse_jwt_claims(access_token)
    exp = claims.get("exp")
    if isinstance(exp, (int, float)):
        expires_at = datetime.fromtimestamp(float(exp), tz=timezone.utc)
        if expires_at <= datetime.now(timezone.utc) + ACCESS_EXPIRY_MARGIN:
            return True

    refreshed_at = parse_iso(last_refresh)
    if refreshed_at is not None:
        return refreshed_at <= datetime.now(timezone.utc) - REFRESH_INTERVAL
    return False


def request_codex(
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | str | None = None,
    stream: bool = False,
    params: dict[str, str] | None = None,
) -> requests.Response:
    cfg = codex_config()
    auth = load_auth()
    target = build_upstream_url(path, cfg["upstream_base_url"])
    request_headers = sanitize_forward_headers(headers or {})
    request_headers.update(
        {
            "Authorization": f"Bearer {auth.access_token}",
            "chatgpt-account-id": auth.account_id,
            "OpenAI-Beta": "responses=experimental",
        }
    )

    return requests.request(
        method,
        target,
        headers=request_headers,
        data=body,
        params=params,
        timeout=max(5, cfg["request_timeout_seconds"]),
        stream=stream,
    )


def fetch_models() -> list[str]:
    cfg = codex_config()
    configured = cfg["models"]
    if configured:
        return configured

    response = request_codex(
        "/models",
        params={"client_version": resolve_codex_version()},
    )
    if not response.ok:
        raise RuntimeError(upstream_error_message(response, "Failed to load Codex models."))

    payload = response.json()
    raw_models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(raw_models, list):
        raise RuntimeError("Codex returned a malformed models response.")

    models: list[str] = []
    seen: set[str] = set()
    for item in raw_models:
        slug = item.get("slug") if isinstance(item, dict) else None
        if isinstance(slug, str) and slug and slug not in seen:
            seen.add(slug)
            models.append(slug)
    if not models:
        raise RuntimeError("Codex returned an empty models list.")
    return models


def prepare_responses_body(body: dict[str, Any], *, force_stream: bool) -> dict[str, Any]:
    normalized = dict(body)
    normalized.setdefault("instructions", "")
    normalized.setdefault("store", False)
    if force_stream:
        normalized["stream"] = True
    normalized.pop("max_output_tokens", None)
    return normalized


def collect_completed_response(response: requests.Response) -> dict[str, Any]:
    latest_response: dict[str, Any] | None = None
    latest_error: Any = None
    text_pieces: list[str] = []
    latest_usage: dict[str, Any] | None = None
    for event in iter_sse_events(response):
        data = event.get("data")
        if not data:
            continue
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        if event.get("event") == "error":
            latest_error = parsed
            continue
        text_pieces.extend(extract_sse_text_deltas(parsed, event.get("event", "")))
        usage = parsed.get("usage")
        if isinstance(usage, dict):
            latest_usage = usage
        candidate = parsed.get("response")
        if isinstance(candidate, dict):
            latest_response = candidate

    if text_pieces:
        text = "".join(text_pieces)
        if latest_response is not None:
            completed = dict(latest_response)
            if not response_text(completed):
                completed["output_text"] = text
            return completed
        result: dict[str, Any] = {"output_text": "".join(text_pieces)}
        if latest_usage:
            result["usage"] = latest_usage
        return result
    if latest_response is not None:
        return latest_response
    suffix = f" Last error: {json.dumps(latest_error)}" if latest_error else ""
    raise RuntimeError(f"No completed response found in Codex SSE stream.{suffix}")


def iter_sse_events(response: requests.Response) -> Iterable[dict[str, str]]:
    buffer = ""
    for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
        if not chunk:
            continue
        if isinstance(chunk, bytes):
            chunk = chunk.decode(response.encoding or "utf-8", errors="replace")
        buffer += chunk
        while "\n\n" in buffer or "\r\n\r\n" in buffer:
            sep = "\r\n\r\n" if "\r\n\r\n" in buffer else "\n\n"
            block, buffer = buffer.split(sep, 1)
            event = parse_sse_block(block)
            if event:
                yield event
    event = parse_sse_block(buffer)
    if event:
        yield event


def parse_sse_block(block: str) -> dict[str, str]:
    event: dict[str, str] = {}
    data_lines: list[str] = []
    for line in block.splitlines():
        if line.startswith("event:"):
            event["event"] = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        event["data"] = "\n".join(data_lines)
    return event


def extract_sse_text_deltas(payload: dict[str, Any], event_type: str = "") -> list[str]:
    pieces: list[str] = []

    choices = payload.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            delta = choice.get("delta")
            if isinstance(delta, dict):
                _append_text_value(pieces, delta.get("content"))
            elif isinstance(delta, str):
                pieces.append(delta)

            message = choice.get("message")
            if isinstance(message, dict):
                _append_text_value(pieces, message.get("content"))

    delta = payload.get("delta")
    if isinstance(delta, str):
        pieces.append(delta)
    elif isinstance(delta, dict):
        _append_text_value(pieces, delta.get("content"))
        _append_text_value(pieces, delta.get("text"))

    if (payload.get("type") or event_type) in {
        "response.output_text.delta",
        "response.output_text.done",
        "response.text.delta",
        "response.text.done",
    }:
        _append_text_value(pieces, payload.get("text"))

    return [piece for piece in pieces if piece]


def _append_text_value(pieces: list[str], value: Any) -> None:
    if isinstance(value, str):
        pieces.append(value)
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict):
                _append_text_value(pieces, item.get("text"))
                _append_text_value(pieces, item.get("content"))


def chat_messages_to_response_body(body: dict[str, Any]) -> dict[str, Any]:
    messages = body.get("messages")
    if not isinstance(messages, list):
        raise RuntimeError("`messages` must be an array.")
    if body.get("tools"):
        raise RuntimeError("Codex/ChatGPT account wrapper does not yet support tool calls.")

    instructions: list[str] = []
    response_input: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        content = message.get("content", "")
        text = normalize_message_content(content)
        if role in {"system", "developer"}:
            if text:
                instructions.append(text)
            continue
        response_input.append({"role": role, "content": text})

    response_body: dict[str, Any] = {
        "model": body.get("model") or "gpt-5.2",
        "input": response_input,
        "instructions": "\n\n".join(instructions),
        "store": False,
    }
    if body.get("temperature") is not None:
        response_body["temperature"] = body["temperature"]
    if body.get("top_p") is not None:
        response_body["top_p"] = body["top_p"]
    if body.get("reasoning_effort") is not None:
        response_body["reasoning"] = {"effort": body["reasoning_effort"]}
    return response_body


def normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def response_text(response: dict[str, Any]) -> str:
    value = response.get("output_text")
    if isinstance(value, str):
        return value

    pieces: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            pieces.append(text)
    return "".join(pieces)


def build_upstream_url(path: str, base_url: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        parsed = urlparse(path)
        path = parsed.path
        if parsed.query:
            path = f"{path}?{parsed.query}"
    if path == "/v1":
        path = "/"
    elif path.startswith("/v1/"):
        path = path[3:]
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def sanitize_forward_headers(headers: dict[str, str]) -> dict[str, str]:
    blocked = {
        "authorization",
        "chatgpt-account-id",
        "host",
        "openai-beta",
        "content-length",
        "connection",
    }
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in blocked and value is not None
    }


def response_headers(response: requests.Response) -> dict[str, str]:
    blocked = {
        "connection",
        "content-encoding",
        "content-length",
        "transfer-encoding",
    }
    return {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in blocked
    }


def upstream_error_message(response: requests.Response, fallback: str) -> str:
    text = response.text
    if not text:
        return fallback
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(error, str):
            return error
    return text


def resolve_codex_version() -> str:
    configured = codex_config()["codex_version"]
    if configured:
        return configured
    try:
        result = subprocess.run(
            ["codex", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        version = _extract_semver(result.stdout) or _extract_semver(result.stderr)
        if version:
            return version
    except Exception:
        pass
    return FALLBACK_CODEX_VERSION


def resolve_auth_file_candidates() -> list[Path]:
    cfg = codex_config()
    explicit = cfg["auth_file_path"]
    if explicit:
        return [Path(explicit).expanduser()]

    candidates: list[Path] = []
    for env_name in ("CHATGPT_LOCAL_HOME", "CODEX_HOME"):
        env_home = os.getenv(env_name)
        if env_home:
            candidates.append(Path(env_home).expanduser() / AUTH_FILENAME)

    home = Path.home()
    candidates.extend(
        [
            home / ".codex" / AUTH_FILENAME,
            home / ".chatgpt-local" / AUTH_FILENAME,
            Path(files.get_abs_path("usr", "plugins", "_oauth", "codex", AUTH_FILENAME)),
        ]
    )
    return _unique_paths(candidates)


def resolve_auth_write_path() -> Path:
    for candidate in resolve_auth_file_candidates():
        if candidate.is_file():
            return candidate
    return resolve_auth_file_candidates()[-1]


def read_auth_file() -> tuple[Path, dict[str, Any]]:
    candidates = resolve_auth_file_candidates()
    for candidate in candidates:
        try:
            with candidate.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return candidate, payload
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return resolve_auth_write_path(), {}


def write_auth_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def parse_jwt_claims(token: str) -> dict[str, Any]:
    if not token or token.count(".") != 2:
        return {}
    try:
        payload = token.split(".")[1]
        padding = "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.urlsafe_b64decode((payload + padding).encode("ascii"))
        value = json.loads(decoded)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def derive_account_id(id_token: str) -> str:
    return _string(_auth_claims(parse_jwt_claims(id_token)).get("chatgpt_account_id"))


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _auth_claims(claims: dict[str, Any]) -> dict[str, Any]:
    return _record(claims.get("https://api.openai.com/auth"))


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _jwt_expiration_iso(claims: dict[str, Any]) -> str:
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        return ""
    return datetime.fromtimestamp(float(exp), tz=timezone.utc).isoformat()


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _token_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = None
    if isinstance(payload, dict):
        for key in OAUTH_ERROR_KEYS:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(error, str):
            return error
    return f"OAuth token endpoint returned status {response.status_code}: {response.text}"


def _extract_semver(value: str) -> str:
    import re

    match = re.search(r"\b\d+\.\d+\.\d+\b", value or "")
    return match.group(0) if match else ""


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _device_expires_at(value: Any) -> float:
    if isinstance(value, str):
        parsed = parse_iso(value)
        if parsed is not None:
            return parsed.timestamp()
    return time.time() + DEVICE_CODE_TIMEOUT_SECONDS


def _unique_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _contains_chatgpt_auth(data: dict[str, Any]) -> bool:
    tokens = _record(data.get("tokens"))
    if _string(data.get("auth_mode")).lower() == "chatgpt":
        return True
    return any(
        _string(tokens.get(key))
        for key in ("access_token", "refresh_token", "id_token", "account_id")
    )


def _has_meaningful_auth_data(data: dict[str, Any]) -> bool:
    for value in data.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (dict, list, tuple, set)) and not value:
            continue
        return True
    return False


def _normalize_usage_headers(headers: Mapping[str, Any]) -> dict[str, Any]:
    lowered = {str(key).lower(): value for key, value in headers.items()}
    primary = _normalize_usage_window(
        {
            "used_percent": lowered.get("x-codex-primary-used-percent"),
            "window_minutes": lowered.get("x-codex-primary-window-minutes"),
            "reset_at": lowered.get("x-codex-primary-resets-at")
            or lowered.get("x-codex-primary-reset-at"),
        }
    )
    secondary = _normalize_usage_window(
        {
            "used_percent": lowered.get("x-codex-secondary-used-percent"),
            "window_minutes": lowered.get("x-codex-secondary-window-minutes"),
            "reset_at": lowered.get("x-codex-secondary-resets-at")
            or lowered.get("x-codex-secondary-reset-at"),
        }
    )
    return {
        "primary": primary,
        "secondary": secondary,
        "plan_type": _string(lowered.get("x-codex-plan-type")),
    }


def _normalize_code_review_usage(value: Any) -> dict[str, Any] | None:
    data = _record(value)
    if not data:
        return None
    window = (
        _normalize_usage_window(data.get("primary_window"))
        or _normalize_usage_window(data.get("primary"))
        or _normalize_usage_window(data)
    )
    if window:
        window["name"] = _string(data.get("name")) or "Code review"
    return window


def _normalize_additional_rate_limits(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        data = _record(item)
        if not data:
            continue
        window = (
            _normalize_usage_window(data.get("primary_window"))
            or _normalize_usage_window(data.get("primary"))
            or _normalize_usage_window(data)
        )
        if not window:
            continue
        name = (
            _string(data.get("name"))
            or _string(data.get("model"))
            or _string(data.get("limit_name"))
            or _string(data.get("limitName"))
            or _string(data.get("id"))
        )
        if name:
            window["name"] = name
        result.append(window)
    return result


def _normalize_usage_window(value: Any) -> dict[str, Any] | None:
    data = _record(value)
    used_percent = _number(
        _first_present(
            data.get("used_percent"),
            data.get("usedPercent"),
            data.get("utilization"),
            data.get("usage_percent"),
        )
    )
    if used_percent is None:
        return None

    window_seconds = _number(
        _first_present(
            data.get("limit_window_seconds"),
            data.get("window_seconds"),
            data.get("windowSeconds"),
            data.get("windowDurationSeconds"),
        )
    )
    window_minutes = _number(
        _first_present(
            data.get("window_minutes"),
            data.get("windowMinutes"),
            data.get("windowDurationMins"),
        )
    )
    if window_seconds is None and window_minutes is not None:
        window_seconds = window_minutes * 60
    if window_minutes is None and window_seconds is not None:
        window_minutes = window_seconds / 60

    reset_at = _epoch_seconds(
        _first_present(
            data.get("reset_at"),
            data.get("resets_at"),
            data.get("resetsAt"),
            data.get("resetAt"),
        )
    )
    used = max(0.0, min(100.0, used_percent))
    return {
        "used_percent": _clean_number(used),
        "remaining_percent": _clean_number(max(0.0, 100.0 - used)),
        "reset_at": reset_at,
        "resets_at_iso": _epoch_iso(reset_at),
        "window_seconds": _clean_number(window_seconds) if window_seconds is not None else None,
        "window_minutes": _clean_number(window_minutes) if window_minutes is not None else None,
        "label": _usage_window_label(window_seconds, window_minutes),
    }


def _normalize_credits(value: Any) -> dict[str, Any] | None:
    data = _record(value)
    if not data:
        return None
    balance = _number(data.get("balance"))
    return {
        "has_credits": bool(data.get("has_credits") or data.get("hasCredits")),
        "unlimited": bool(data.get("unlimited")),
        "balance": _clean_number(balance) if balance is not None else None,
    }


def _usage_window_label(seconds: float | None, minutes: float | None) -> str:
    if seconds is None and minutes is not None:
        seconds = minutes * 60
    if seconds is None:
        return ""
    if 17_940 <= seconds <= 18_060:
        return "5h"
    if 604_000 <= seconds <= 605_000:
        return "7d"
    if seconds >= 86_400 and seconds % 86_400 == 0:
        return f"{int(seconds // 86_400)}d"
    if seconds >= 3_600 and seconds % 3_600 == 0:
        return f"{int(seconds // 3_600)}h"
    if seconds >= 60 and seconds % 60 == 0:
        return f"{int(seconds // 60)}m"
    return ""


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().rstrip("%")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        return value
    return None


def _epoch_seconds(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    if number > 1_000_000_000_000:
        number = number / 1000
    return number


def _epoch_iso(value: float | None) -> str:
    if value is None:
        return ""
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    except (OSError, ValueError):
        return ""


def _clean_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    if float(value).is_integer():
        return int(value)
    return round(float(value), 2)
