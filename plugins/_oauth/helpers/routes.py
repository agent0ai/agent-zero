from __future__ import annotations

import ipaddress
import json
import time
from typing import Any, Callable

from flask import Response, jsonify, request, stream_with_context

from plugins._oauth.helpers import codex
from plugins._oauth.helpers.config import codex_config
from plugins._oauth.helpers.providers import (
    GEMINI_API_PROVIDER_ID,
    GITHUB_COPILOT_PROVIDER_ID,
    XAI_GROK_PROVIDER_ID,
    ProviderError,
    get_provider,
    provider_registry,
)
from plugins._oauth.helpers.state import pop_attempt


def register_oauth_routes(app) -> None:
    cfg = codex_config()
    base = cfg["proxy_base_path"]

    routes = [
        (f"{base}/health", "oauth_codex_health", codex_health, ["GET"]),
        (f"{base}/callback", "oauth_codex_callback", codex_callback, ["GET"]),
        (cfg["callback_path"], "oauth_codex_compat_callback", codex_callback, ["GET"]),
        (f"{base}/v1/models", "oauth_codex_models", codex_models, ["GET", "OPTIONS"]),
        (
            f"{base}/v1/responses",
            "oauth_codex_responses",
            codex_responses,
            ["POST", "OPTIONS"],
        ),
        (
            f"{base}/v1/chat/completions",
            "oauth_codex_chat_completions",
            codex_chat_completions,
            ["POST", "OPTIONS"],
        ),
    ]
    for rule, endpoint, view_func, methods in routes:
        if endpoint in app.view_functions:
            continue
        app.add_url_rule(rule, endpoint, view_func, methods=methods)

    for provider in provider_registry().values():
        provider.register_routes(app)


def codex_health():
    return jsonify({"ok": True, "provider": "codex", "base_path": codex_config()["proxy_base_path"]})


def codex_callback():
    error = request.args.get("error")
    if error:
        description = request.args.get("error_description") or error
        return _html_page("Codex Sign-In Failed", description), 400

    state = request.args.get("state", "")
    code = request.args.get("code", "")
    attempt = pop_attempt(state)
    if not attempt:
        return _html_page("Codex Sign-In Expired", "Return to Agent Zero and start a new Codex connection."), 400
    if not code:
        return _html_page("Codex Sign-In Failed", "The OAuth callback did not include an authorization code."), 400

    try:
        auth = codex.complete_login(code, attempt.redirect_uri, attempt.verifier)
        info = codex.status()
    except Exception as exc:
        return _html_page("Codex Sign-In Failed", str(exc)), 500

    email = info.get("email") or "Connected"
    detail = f"{email}\n{auth.account_id}"
    return _html_page("Codex Connected", detail)


def codex_models():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied
    try:
        models = codex.fetch_models()
        return jsonify(
            {
                "object": "list",
                "data": [
                    {
                        "id": model,
                        "object": "model",
                        "created": 0,
                        "owned_by": "codex-oauth",
                    }
                    for model in models
                ],
            }
        )
    except ProviderError as exc:
        return _json_error(str(exc), status=exc.status, code=exc.code)
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")


def codex_responses():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _json_error("Request body must be a JSON object.")

    wants_stream = body.get("stream") is True
    upstream_body = codex.prepare_responses_body(body, force_stream=True)
    try:
        upstream = codex.request_codex(
            "/responses",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(upstream_body),
            stream=True,
        )
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")

    if not upstream.ok:
        return _copy_upstream_response(upstream)
    if wants_stream:
        return _stream_upstream_sse(upstream)

    try:
        completed = codex.collect_completed_response(upstream)
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")
    return jsonify(completed)


def codex_chat_completions():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _json_error("Request body must be a JSON object.")

    try:
        response_body = codex.chat_messages_to_response_body(body)
    except Exception as exc:
        return _json_error(str(exc))

    wants_stream = body.get("stream") is True
    response_body["stream"] = True
    try:
        upstream = codex.request_codex(
            "/responses",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(codex.prepare_responses_body(response_body, force_stream=True)),
            stream=True,
        )
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")

    if not upstream.ok:
        return _copy_upstream_response(upstream)
    if wants_stream:
        return _stream_chat_completion(upstream, str(body.get("model") or response_body["model"]))

    try:
        completed = codex.collect_completed_response(upstream)
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")

    text = codex.response_text(completed)
    return jsonify(
        {
            "id": f"chatcmpl_{int(time.time() * 1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model") or response_body["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": completed.get("usage") or {},
        }
    )


def github_copilot_health():
    return jsonify(
        {
            "ok": True,
            "provider": GITHUB_COPILOT_PROVIDER_ID,
            "base_path": "/oauth/github-copilot",
        }
    )


def github_copilot_models():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied

    provider = get_provider(GITHUB_COPILOT_PROVIDER_ID)
    return jsonify(
        {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "github-copilot-oauth",
                }
                for model in provider.models()
            ],
        }
    )


def github_copilot_chat_completions():
    if request.method == "OPTIONS":
        return _options_response()
    return _github_copilot_json_proxy("/chat/completions")


def github_copilot_responses():
    if request.method == "OPTIONS":
        return _options_response()
    return _github_copilot_json_proxy("/responses")


def xai_grok_health():
    return jsonify(
        {
            "ok": True,
            "provider": XAI_GROK_PROVIDER_ID,
            "base_path": "/oauth/xai-grok",
        }
    )


def xai_grok_callback():
    provider = get_provider(XAI_GROK_PROVIDER_ID)
    result = provider.complete_callback(dict(request.args), request)
    if result.ok:
        return _html_page("xAI Grok Connected", result.account_label or "Connected")
    return _html_page("xAI Grok Sign-In Failed", result.error or "The OAuth callback failed."), 400


def xai_grok_models():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied

    provider = get_provider(XAI_GROK_PROVIDER_ID)
    return jsonify(
        {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "xai-grok-oauth",
                }
                for model in provider.models()
            ],
        }
    )


def xai_grok_chat_completions():
    if request.method == "OPTIONS":
        return _options_response()
    return _xai_grok_json_proxy("/chat/completions")


def xai_grok_responses():
    if request.method == "OPTIONS":
        return _options_response()
    return _xai_grok_json_proxy("/responses")


def gemini_api_health():
    return jsonify(
        {
            "ok": True,
            "provider": GEMINI_API_PROVIDER_ID,
            "base_path": "/oauth/gemini-api",
        }
    )


def gemini_api_callback():
    provider = get_provider(GEMINI_API_PROVIDER_ID)
    result = provider.complete_callback(dict(request.args), request)
    if result.ok:
        return _html_page("Google Gemini API Connected", result.account_label or "Connected")
    return _html_page("Google Gemini API Sign-In Failed", result.error or "The OAuth callback failed."), 400


def gemini_api_models():
    if request.method == "OPTIONS":
        return _options_response()
    denied = _proxy_denied_response()
    if denied:
        return denied

    provider = get_provider(GEMINI_API_PROVIDER_ID)
    return jsonify(
        {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "gemini-api-oauth",
                }
                for model in provider.models()
            ],
        }
    )


def gemini_api_chat_completions():
    if request.method == "OPTIONS":
        return _options_response()
    return _gemini_api_json_proxy("/chat/completions")


def gemini_api_responses():
    if request.method == "OPTIONS":
        return _options_response()
    return _gemini_api_json_proxy("/responses")


def _github_copilot_json_proxy(path: str):
    from plugins._oauth.helpers.providers.github_copilot import COPILOT_HEADERS, safe_copilot_base_url

    return _oauth_json_proxy(
        GITHUB_COPILOT_PROVIDER_ID,
        path,
        "GitHub Copilot OAuth is not connected.",
        lambda auth: safe_copilot_base_url(auth.get("base_url"), auth.get("enterprise_domain")),
        lambda auth, access: {
            **COPILOT_HEADERS,
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
        },
    )


def _xai_grok_json_proxy(path: str):
    from plugins._oauth.helpers.providers.xai_grok import safe_api_base_url

    return _oauth_json_proxy(
        XAI_GROK_PROVIDER_ID,
        path,
        "xAI Grok OAuth is not connected.",
        lambda auth: safe_api_base_url(auth.get("base_url")),
        lambda auth, access: {
            "Accept": "application/json",
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
        },
        require_refresh=True,
    )


def _gemini_api_json_proxy(path: str):
    from plugins._oauth.helpers.providers.gemini_api import _gemini_headers, safe_api_base_url

    return _oauth_json_proxy(
        GEMINI_API_PROVIDER_ID,
        path,
        "Google Gemini API OAuth is not connected.",
        lambda auth: safe_api_base_url(auth.get("base_url")),
        lambda auth, access: {
            **_gemini_headers(auth),
            "Content-Type": "application/json",
        },
        require_refresh=True,
    )


def _oauth_json_proxy(
    provider_id: str,
    path: str,
    not_connected_message: str,
    base_url_for: Callable[[dict[str, Any]], str],
    headers_for: Callable[[dict[str, Any], str], dict[str, str]],
    *,
    require_refresh: bool = False,
):
    denied = _proxy_denied_response()
    if denied:
        return denied

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _json_error("Request body must be a JSON object.")

    try:
        auth = _provider_auth(provider_id)
    except ProviderError as exc:
        return _json_error(str(exc), status=exc.status, code=exc.code)
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")

    access = str(auth.get("access") or "")
    refresh = str(auth.get("refresh") or "")
    if not access or (require_refresh and not refresh):
        return _json_error(not_connected_message, status=401, code="not_connected")

    wants_stream = body.get("stream") is True
    try:
        import requests

        base_url = base_url_for(auth)
        upstream = requests.post(
            f"{base_url}{path}",
            headers=headers_for(auth, access),
            json=body,
            stream=wants_stream,
            timeout=120,
        )
    except ProviderError as exc:
        return _json_error(str(exc), status=exc.status, code=exc.code)
    except Exception as exc:
        return _json_error(str(exc), status=502, code="upstream_error")

    if wants_stream and upstream.ok:
        return _stream_upstream_sse(upstream)
    return _copy_upstream_response(upstream)


def _provider_auth(provider_id: str) -> dict[str, Any]:
    provider = get_provider(provider_id)
    ensure_fresh_auth = getattr(provider, "ensure_fresh_auth", None)
    read_auth = getattr(provider, "read_auth", None)
    if callable(ensure_fresh_auth):
        auth = ensure_fresh_auth()
    elif callable(read_auth):
        auth = read_auth()
    else:
        auth = {}
    return auth if isinstance(auth, dict) else {}


def _stream_upstream_sse(upstream):
    headers = codex.response_headers(upstream)
    headers.setdefault("Content-Type", "text/event-stream")
    headers.setdefault("Cache-Control", "no-cache")
    return Response(
        stream_with_context(upstream.iter_content(chunk_size=8192)),
        status=upstream.status_code,
        headers=headers,
    )


def _stream_chat_completion(upstream, model: str):
    created = int(time.time())
    chunk_id = f"chatcmpl_{int(time.time() * 1000)}"

    def generate():
        yield _sse_data(
            {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            }
        )
        for event in codex.iter_sse_events(upstream):
            data = event.get("data")
            if not data:
                continue
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue
            for delta in codex.extract_sse_text_deltas(parsed, event.get("event", "")):
                yield _sse_data(
                    {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": delta},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
        yield _sse_data(
            {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
        )
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
    )


def _copy_upstream_response(upstream):
    return Response(
        upstream.content,
        status=upstream.status_code,
        headers=codex.response_headers(upstream),
    )


def _proxy_denied_response() -> Response | None:
    if _proxy_authorized():
        return None
    return _json_error("Codex/ChatGPT account proxy access denied.", status=403, code="access_denied")


def _proxy_authorized() -> bool:
    cfg = codex_config()
    token = cfg["proxy_token"]
    supplied = _supplied_proxy_token()
    if token and supplied == token:
        return True
    if cfg["require_proxy_token"]:
        return False
    return _remote_is_loopback(request.remote_addr)


def _supplied_proxy_token() -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (
        request.headers.get("X-API-Key")
        or request.args.get("api_key")
        or request.args.get("key")
        or ""
    ).strip()


def _host_is_local(host: str) -> bool:
    hostname = (host or "").strip().lower()
    if hostname.startswith("["):
        closing_bracket = hostname.find("]")
        hostname = hostname[1:closing_bracket] if closing_bracket >= 0 else hostname.strip("[]")
    elif hostname.count(":") == 1:
        hostname = hostname.split(":", 1)[0]
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _remote_is_loopback(addr: str | None) -> bool:
    try:
        return ipaddress.ip_address(addr or "").is_loopback
    except ValueError:
        return False


def _json_error(message: str, *, status: int = 400, code: str = "invalid_request") -> Response:
    return jsonify({"error": {"message": message, "type": code, "code": code}}), status


def _options_response() -> Response:
    return Response(status=204)


def _sse_data(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_escape_html(title)}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #101214;
      color: #f2f5f7;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(560px, calc(100vw - 32px));
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 8px;
      padding: 24px;
      background: #171a1d;
      box-shadow: 0 18px 70px rgba(0,0,0,.28);
    }}
    h1 {{ margin: 0 0 10px; font-size: 24px; }}
    p {{ margin: 0; color: #b9c1c9; line-height: 1.5; white-space: pre-line; }}
    span {{ color: #7f8b96; font-size: 13px; }}
  </style>
</head>
<body>
  <main>
    <h1>{_escape_html(title)}</h1>
    <p>{_escape_html(body)}</p>
  </main>
</body>
</html>"""


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
