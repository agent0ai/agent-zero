"""VPS proxy/auth compatibility using isolated accounts and loopback HTTP."""

from pathlib import Path
import subprocess
import sys
from threading import Thread
from types import SimpleNamespace

from flask import Flask
import pytest
import requests
from werkzeug.serving import make_server

import models
from helpers import runtime
from helpers.litellm_transport import LiteLLMTransport
from plugins._oauth import helpers as oauth_helpers
from plugins._oauth.helpers import routes
from plugins._oauth.helpers.providers import CODEX_PROVIDER_ID, get_provider, oauth_provider_ids
from test_litellm_sdk import chat_reply, provider, response_reply
from test_oauth_proxy_security import isolate_oauth_model_extensions


@pytest.fixture
def proxy_app(monkeypatch):
    # Older stub-based tests restore sys.modules but leave the parent attribute stale.
    monkeypatch.setattr(oauth_helpers, "routes", routes)
    monkeypatch.setattr(routes, "codex_config", lambda: {
        "proxy_base_path": "/oauth/codex", "callback_path": "/auth/callback",
        "proxy_token": "existing-proxy-token", "require_proxy_token": False,
    })
    monkeypatch.setattr(routes.codex, "fetch_models", lambda: ["synthetic-model"])
    monkeypatch.setattr(routes.codex, "resolve_installation_id", lambda: "synthetic-installation")
    registry = routes.provider_registry()
    monkeypatch.setattr(routes, "provider_registry", lambda: registry)
    monkeypatch.setattr(routes, "get_provider", lambda provider_id: registry[provider_id])
    for account in registry.values():
        monkeypatch.setattr(account, "models", lambda: ["synthetic-model"])
    app = Flask(__name__)
    routes.register_oauth_routes(app)
    return app


@pytest.mark.parametrize("provider_id", sorted(oauth_provider_ids()))
@pytest.mark.parametrize("remote_addr", ["127.0.0.1", "::1", "203.0.113.10"])
@pytest.mark.parametrize("auth", ["none", "legacy", "internal", "configured"])
def test_reverse_proxy_authentication_is_independent_of_peer_address(proxy_app, provider_id, remote_addr, auth):
    path = get_provider(provider_id).metadata().proxy_base_path
    key = models.get_api_key(provider_id)
    headers = {
        "Host": "agent.example.invalid", "Origin": "https://agent.example.invalid",
        "X-Forwarded-For": "203.0.113.25", "X-Forwarded-Proto": "https",
        "Forwarded": "for=203.0.113.25;proto=https;host=agent.example.invalid",
    }
    token = {"none": "", "legacy": "oauth", "internal": key, "configured": "existing-proxy-token"}[auth]
    if token:
        headers["Authorization"] = f"Bearer {token}"
    client = proxy_app.test_client()
    response = client.get(f"{path}/v1/models", headers=headers, environ_overrides={"REMOTE_ADDR": remote_addr})
    assert response.status_code == (200 if auth in {"internal", "configured"} else 403)
    assert "Access-Control-Allow-Origin" not in response.headers
    for endpoint in ["responses", "chat/completions"]:
        # Auth must run before body parsing, upstream access, or stored-account reads.
        response = client.post(f"{path}/v1/{endpoint}", json=[], headers=headers,
                               environ_overrides={"REMOTE_ADDR": remote_addr})
        assert response.status_code == (400 if auth in {"internal", "configured"} else 403)
        preflight = client.options(f"{path}/v1/{endpoint}", headers=headers)
        assert preflight.status_code == 204
        assert "Access-Control-Allow-Origin" not in preflight.headers


@pytest.mark.parametrize("callback_path", [
    "/oauth/codex/callback", "/auth/callback", "/oauth/xai-grok/callback", "/oauth/gemini-api/callback",
])
def test_remote_oauth_callbacks_remain_accessible_without_proxy_credentials(monkeypatch, proxy_app, callback_path):
    monkeypatch.setattr(routes, "pop_attempt", lambda state: SimpleNamespace(redirect_uri="https://agent.example.invalid/auth/callback", verifier="synthetic-verifier"))
    monkeypatch.setattr(routes.codex, "complete_login", lambda *args: SimpleNamespace(account_id="synthetic-account"))
    monkeypatch.setattr(routes.codex, "status", lambda: {"email": "synthetic@example.invalid"})
    from plugins._oauth.helpers.providers import CallbackResult
    for account in routes.provider_registry().values():
        monkeypatch.setattr(account, "complete_callback", lambda *args: CallbackResult(ok=True, provider_id="synthetic"))
    response = proxy_app.test_client().get(callback_path + "?code=synthetic-code&state=synthetic-state", headers={
        "Host": "agent.example.invalid", "X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.25",
    })
    assert response.status_code == 200
    assert b"Connected" in response.data


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_id", sorted(oauth_provider_ids()))
@pytest.mark.parametrize("stream", [False, True])
async def test_existing_model_calls_through_real_http_proxy_without_reconfiguration(
    monkeypatch, proxy_app, provider, provider_id, stream
):
    upstream_url = provider.kwargs["api_base"]
    native = provider_id in {CODEX_PROVIDER_ID, "xai_grok_oauth"}
    provider.replies.append((200, response_reply(True if provider_id == CODEX_PROVIDER_ID else stream)
                             if native else chat_reply(stream)))
    if provider_id == CODEX_PROVIDER_ID:
        monkeypatch.setattr(routes.codex, "request_codex", lambda path, **kwargs: requests.post(
            upstream_url + path, data=kwargs["body"], headers=kwargs["headers"], stream=True, timeout=5,
        ))
    else:
        module_name = {"github_copilot_oauth": "github_copilot", "gemini_api_oauth": "gemini_api",
                       "xai_grok_oauth": "xai_grok"}[provider_id]
        module = __import__(f"plugins._oauth.helpers.providers.{module_name}", fromlist=[module_name])
        validator = "safe_copilot_base_url" if module_name == "github_copilot" else "safe_api_base_url"
        monkeypatch.setattr(module, validator, lambda *args: upstream_url)
        monkeypatch.setattr(routes, "_provider_auth", lambda _: {"access": "synthetic-access", "refresh": "synthetic-refresh"})

    received = []

    @proxy_app.before_request
    def record_request():
        from flask import request
        received.append((request.path, request.headers.get("Host"), request.headers.get("Authorization")))

    server = make_server("127.0.0.1", 0, proxy_app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(runtime, "get_web_ui_port", lambda: server.server_port)
    path = get_provider(provider_id).metadata().proxy_base_path
    try:
        model = models.get_chat_model(
            provider_id, "gpt-4o", api_base=f"http://127.0.0.1:{server.server_port}{path}/v1",
            api_key="oauth", extra_headers={"Authorization": "Bearer oauth", "Host": "agent.example.invalid",
                                            "X-Forwarded-For": "203.0.113.25", "X-Forwarded-Proto": "https"},
            num_retries=0, timeout=5,
        )
        transport = LiteLLMTransport(model=model.model_name, messages=[{"role": "user", "content": "Check"}],
                                     kwargs=model.kwargs)
        if stream:
            _ = [chunk async for chunk in transport.astream()]
        else:
            await transport.acomplete()
        assert transport.last_result.function_calls[0].name == "lookup"
        assert len(received) == 1
        assert received[0] == (f"{path}/v1/{'responses' if native else 'chat/completions'}",
                               "agent.example.invalid", f"Bearer {models.get_api_key(provider_id)}")
        assert len(provider.requests) == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_existing_client_credential_survives_bundled_plugin_reload():
    # A separate interpreter exercises the real namespace purge without contaminating pytest.
    code = """
from flask import Flask
from helpers import plugins
from plugins._oauth.helpers import routes
from plugins._oauth.helpers.providers import DUMMY_API_KEY
routes.codex_config = lambda: {'proxy_token': ''}
app = Flask(__name__)
with app.test_request_context(headers={'Authorization': f'Bearer {DUMMY_API_KEY}'}):
    assert routes._proxy_authorized()
    plugins.refresh_plugin_modules(['_unrelated_plugin'])
    assert routes._proxy_authorized(), 'Plugin reload invalidated an existing model client'
    from plugins._oauth.helpers.providers import DUMMY_API_KEY as reloaded_key
    assert reloaded_key == DUMMY_API_KEY
print('ok')
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
