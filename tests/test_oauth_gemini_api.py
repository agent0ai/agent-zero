from __future__ import annotations

import base64
import json
import sys
import time
import types
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass(frozen=True)
class PkcePair:
    verifier: str
    challenge: str


from plugins._oauth.helpers.providers import gemini_api as gemini
from plugins._oauth.helpers.providers.base import GEMINI_API_PROVIDER_ID, ProviderError
from plugins._oauth.helpers.state import pop_attempt, put_attempt


def _config() -> dict:
    return {
        "enabled": True,
        "client_id": "client-id.apps.googleusercontent.com",
        "client_secret": "client-secret",
        "scopes": [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/generative-language.retriever",
        ],
        "quota_project_id": "quota-project",
        "api_base_url": gemini.GEMINI_OPENAI_API_BASE,
        "proxy_base_path": "/oauth/gemini-api",
        "callback_path": "/oauth/gemini-api/callback",
    }


class FakeRequest:
    headers = {}
    url_root = "http://localhost:50001/"


def _fake_codex_helper():
    fake_codex = types.SimpleNamespace()
    fake_codex.generate_pkce = lambda: PkcePair("verifier", "challenge")
    fake_codex.generate_state = lambda: "state-1"
    return fake_codex


def _jwt(claims: dict) -> str:
    header = _b64({"alg": "none", "typ": "JWT"})
    payload = _b64(claims)
    return f"{header}.{payload}.signature"


def _b64(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def test_start_login_builds_google_pkce_authorize_url_without_network(monkeypatch):
    provider = gemini.GeminiApiOAuthProvider()
    monkeypatch.setattr(gemini, "_gemini_api_config", _config)
    monkeypatch.setattr(gemini, "_codex_helper", _fake_codex_helper)

    result = provider.start_login({}, FakeRequest())

    try:
        assert result.ok is True
        assert result.provider_id == GEMINI_API_PROVIDER_ID
        assert result.flow == "browser_pkce"
        assert result.redirect_uri == "http://localhost:50001/oauth/gemini-api/callback"

        parsed = urlparse(result.auth_url)
        query = parse_qs(parsed.query)
        assert result.auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
        assert query["response_type"] == ["code"]
        assert query["client_id"] == ["client-id.apps.googleusercontent.com"]
        assert query["scope"] == [" ".join(_config()["scopes"])]
        assert query["code_challenge"] == ["challenge"]
        assert query["code_challenge_method"] == ["S256"]
        assert query["state"] == ["state-1"]
        assert query["access_type"] == ["offline"]
        assert query["prompt"] == ["consent"]
        assert query["redirect_uri"] == ["http://localhost:50001/oauth/gemini-api/callback"]
    finally:
        pop_attempt("state-1")


def test_start_login_requires_user_supplied_oauth_client(monkeypatch):
    provider = gemini.GeminiApiOAuthProvider()
    cfg = _config()
    cfg["client_id"] = ""
    cfg["client_secret"] = ""
    monkeypatch.setattr(gemini, "_gemini_api_config", lambda: cfg)
    monkeypatch.setattr(gemini, "_codex_helper", _fake_codex_helper)

    result = provider.start_login({}, FakeRequest())

    assert result.ok is False
    assert result.provider_id == GEMINI_API_PROVIDER_ID
    assert "OAuth client ID and client secret" in result.error


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "http://localhost:50001/oauth/gemini-api/callback?code=abc&state=state-1",
            {"code": "abc", "state": "state-1", "error": None, "error_description": None},
        ),
        ("?code=abc&state=state-1", {"code": "abc", "state": "state-1", "error": None, "error_description": None}),
        ("code=abc&state=state-1", {"code": "abc", "state": "state-1", "error": None, "error_description": None}),
        ("abc", {"code": "abc", "state": None, "error": None, "error_description": None}),
    ],
)
def test_parse_manual_callback_accepts_url_query_and_bare_code(raw, expected):
    assert gemini.parse_manual_callback(raw) == expected


def test_manual_callback_exchanges_code_and_stores_tokens(tmp_path, monkeypatch):
    provider = gemini.GeminiApiOAuthProvider()
    auth_path = tmp_path / "auth.json"
    put_attempt(
        "state-1",
        "verifier-1",
        "http://localhost:50001/oauth/gemini-api/callback",
        provider_id=GEMINI_API_PROVIDER_ID,
        extra={
            "client_id": "client-id.apps.googleusercontent.com",
            "client_secret": "client-secret",
            "quota_project_id": "quota-project",
            "token_endpoint": gemini.GOOGLE_TOKEN_ENDPOINT,
            "api_base_url": gemini.GEMINI_OPENAI_API_BASE,
        },
    )
    calls = []

    monkeypatch.setattr(provider, "auth_path", lambda: auth_path)

    def fake_exchange(token_endpoint, code, redirect_uri, code_verifier, client_id, client_secret):
        calls.append((token_endpoint, code, redirect_uri, code_verifier, client_id, client_secret))
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "id_token": _jwt({"email": "user@example.com"}),
            "token_type": "Bearer",
        }

    monkeypatch.setattr(provider, "exchange_code", fake_exchange)

    result = provider.manual_callback(
        {"callback": "http://localhost:50001/oauth/gemini-api/callback?code=code-1&state=state-1"}
    )

    assert result.ok is True
    assert result.completed is True
    assert result.account_label == "user@example.com"
    assert calls == [
        (
            gemini.GOOGLE_TOKEN_ENDPOINT,
            "code-1",
            "http://localhost:50001/oauth/gemini-api/callback",
            "verifier-1",
            "client-id.apps.googleusercontent.com",
            "client-secret",
        )
    ]
    saved = json.loads(auth_path.read_text(encoding="utf-8"))
    assert saved["provider"] == GEMINI_API_PROVIDER_ID
    assert saved["access"] == "access-token"
    assert saved["refresh"] == "refresh-token"
    assert saved["quota_project_id"] == "quota-project"
    assert saved["client_id"] == "client-id.apps.googleusercontent.com"


def test_ensure_fresh_auth_rejects_malicious_stored_token_endpoint(monkeypatch):
    provider = gemini.GeminiApiOAuthProvider()
    monkeypatch.setattr(
        provider,
        "read_auth",
        lambda: {
            "access": "expired-access-token",
            "refresh": "refresh-token",
            "expires": 1,
            "client_id": "client-id.apps.googleusercontent.com",
            "client_secret": "client-secret",
            "token_endpoint": "https://evil.example/oauth/token",
        },
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.ensure_fresh_auth()

    assert exc_info.value.code == "invalid_token_endpoint"


def test_models_returns_curated_list_without_network(monkeypatch):
    provider = gemini.GeminiApiOAuthProvider()
    monkeypatch.setattr(provider, "read_auth", lambda: {})

    models = provider.models()

    assert models[:3] == [
        "gemini-3.5-flash",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
    ]


def test_models_does_not_send_bearer_token_to_malicious_base_url(monkeypatch):
    calls = []

    class FakeResponse:
        ok = True

        def json(self):
            return {"data": [{"id": "models/gemini-3.5-flash"}]}

    class FakeRequests:
        @staticmethod
        def get(url, headers, timeout):
            calls.append((url, headers, timeout))
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    provider = gemini.GeminiApiOAuthProvider()
    monkeypatch.setattr(
        provider,
        "read_auth",
        lambda: {
            "access": "access-token",
            "refresh": "refresh-token",
            "expires": int(time.time() * 1000) + 3_600_000,
            "base_url": "https://evil.example/v1",
            "quota_project_id": "quota-project",
        },
    )

    assert provider.models() == ["gemini-3.5-flash"]
    assert calls == [
        (
            "https://generativelanguage.googleapis.com/v1beta/openai/models",
            {
                "Accept": "application/json",
                "Authorization": "Bearer access-token",
                "x-goog-user-project": "quota-project",
            },
            30,
        )
    ]
