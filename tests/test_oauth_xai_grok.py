from __future__ import annotations

import json
import sys
import types
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

@dataclass(frozen=True)
class PkcePair:
    verifier: str
    challenge: str


from plugins._oauth.helpers.providers.base import ProviderError, XAI_GROK_PROVIDER_ID
from plugins._oauth.helpers.providers import xai_grok as xai
from plugins._oauth.helpers.state import pop_attempt, put_attempt


def _discovery() -> dict[str, str]:
    return {
        "authorization_endpoint": "https://auth.x.ai/oauth/authorize",
        "token_endpoint": "https://auth.x.ai/oauth/token",
    }


def test_start_login_builds_xai_pkce_authorize_url_without_network(monkeypatch):
    provider = xai.XaiGrokOAuthProvider()
    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_codex.PkcePair = PkcePair
    fake_codex.generate_pkce = lambda: PkcePair("verifier", "challenge")
    fake_codex.generate_state = lambda: "state-1"
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setattr(provider, "discovery", _discovery)

    result = provider.start_login({})

    try:
        assert result.ok is True
        assert result.provider_id == XAI_GROK_PROVIDER_ID
        assert result.flow == "browser_pkce"
        assert result.redirect_uri == "http://127.0.0.1:56121/callback"

        parsed = urlparse(result.auth_url)
        query = parse_qs(parsed.query)
        assert result.auth_url.startswith("https://auth.x.ai/oauth/authorize?")
        assert query["response_type"] == ["code"]
        assert query["client_id"] == [xai.XAI_CLIENT_ID]
        assert query["scope"] == [xai.XAI_SCOPE]
        assert query["code_challenge"] == ["challenge"]
        assert query["code_challenge_method"] == ["S256"]
        assert query["state"] == ["state-1"]
        assert query["plan"] == ["generic"]
        assert query["referrer"] == ["agent-zero"]
        assert query["redirect_uri"] == ["http://127.0.0.1:56121/callback"]
        assert query["nonce"]
    finally:
        pop_attempt("state-1")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "http://127.0.0.1:56121/callback?code=abc&state=state-1",
            {"code": "abc", "state": "state-1", "error": None, "error_description": None},
        ),
        ("?code=abc&state=state-1", {"code": "abc", "state": "state-1", "error": None, "error_description": None}),
        ("code=abc&state=state-1", {"code": "abc", "state": "state-1", "error": None, "error_description": None}),
        ("abc", {"code": "abc", "state": None, "error": None, "error_description": None}),
    ],
)
def test_parse_manual_callback_accepts_url_query_and_bare_code(raw, expected):
    assert xai.parse_manual_callback(raw) == expected


def test_manual_callback_rejects_state_mismatch(monkeypatch):
    provider = xai.XaiGrokOAuthProvider()
    put_attempt(
        "state-good",
        "verifier",
        xai.XAI_REDIRECT_URI,
        provider_id=XAI_GROK_PROVIDER_ID,
        extra={"token_endpoint": "https://auth.x.ai/oauth/token"},
    )
    monkeypatch.setattr(provider, "discovery", _discovery)

    try:
        result = provider.manual_callback({"callback": "code=abc&state=state-bad"})

        assert result.ok is False
        assert "state mismatch" in result.error.lower()
    finally:
        pop_attempt("state-good")
        pop_attempt("state-bad")


def test_manual_callback_exchanges_code_and_stores_tokens(tmp_path, monkeypatch):
    provider = xai.XaiGrokOAuthProvider()
    auth_path = tmp_path / "auth.json"
    put_attempt(
        "state-1",
        "verifier-1",
        xai.XAI_REDIRECT_URI,
        provider_id=XAI_GROK_PROVIDER_ID,
        extra={"token_endpoint": "https://auth.x.ai/oauth/token", "code_challenge": "challenge-1"},
    )
    calls = []

    monkeypatch.setattr(provider, "auth_path", lambda: auth_path)
    monkeypatch.setattr(provider, "discovery", _discovery)

    def fake_exchange(token_endpoint, code, redirect_uri, code_verifier, code_challenge):
        calls.append((token_endpoint, code, redirect_uri, code_verifier, code_challenge))
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "id_token": "id-token",
            "token_type": "Bearer",
        }

    monkeypatch.setattr(provider, "exchange_code", fake_exchange)

    result = provider.manual_callback(
        {"callback": "http://127.0.0.1:56121/callback?code=code-1&state=state-1"}
    )

    assert result.ok is True
    assert result.completed is True
    assert result.account_label == "xAI Grok"
    assert calls == [
        (
            "https://auth.x.ai/oauth/token",
            "code-1",
            "http://127.0.0.1:56121/callback",
            "verifier-1",
            "challenge-1",
        )
    ]
    saved = json.loads(auth_path.read_text(encoding="utf-8"))
    assert saved["provider"] == XAI_GROK_PROVIDER_ID
    assert saved["access"] == "access-token"
    assert saved["refresh"] == "refresh-token"


def test_models_returns_curated_list_without_network(monkeypatch):
    provider = xai.XaiGrokOAuthProvider()
    monkeypatch.setattr(provider, "read_auth", lambda: {})

    models = provider.models()

    assert models[:4] == [
        "grok-4.3",
        "grok-4.20-0309-reasoning",
        "grok-4.20-0309-non-reasoning",
        "grok-4.20-multi-agent-0309",
    ]


def test_exchange_code_http_403_explains_oauth_tier_restriction(monkeypatch):
    class FakeResponse:
        ok = False
        status_code = 403
        text = "forbidden"

        def json(self):
            return {"error": "forbidden"}

    class FakeRequests:
        @staticmethod
        def post(*args, **kwargs):
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    provider = xai.XaiGrokOAuthProvider()
    with pytest.raises(ProviderError) as exc_info:
        provider.exchange_code(
            "https://auth.x.ai/oauth/token",
            "code",
            xai.XAI_REDIRECT_URI,
            "verifier",
            "challenge",
        )

    assert exc_info.value.status == 403
    assert "restricted by tier" in str(exc_info.value)
    assert "API-key `xai` provider" in str(exc_info.value)


def test_refresh_403_preserves_oauth_tier_guidance(monkeypatch):
    class FakeResponse:
        ok = False
        status_code = 403

        def json(self):
            return {"error": "forbidden"}

    class FakeRequests:
        @staticmethod
        def post(*args, **kwargs):
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    provider = xai.XaiGrokOAuthProvider()
    monkeypatch.setattr(
        provider,
        "read_auth",
        lambda: {
            "access": "expired-access-token",
            "refresh": "refresh-token",
            "expires": 1,
            "token_endpoint": "https://auth.x.ai/oauth/token",
        },
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.ensure_fresh_auth()

    assert exc_info.value.status == 403
    assert exc_info.value.code == "oauth_tier_restricted"
    assert "restricted by tier" in str(exc_info.value)
    assert "API-key `xai` provider" in str(exc_info.value)


def test_ensure_fresh_auth_rejects_malicious_stored_token_endpoint(monkeypatch):
    calls = []

    class FakeRequests:
        @staticmethod
        def post(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("malicious token endpoint must not be called")

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    provider = xai.XaiGrokOAuthProvider()
    monkeypatch.setattr(
        provider,
        "read_auth",
        lambda: {
            "access": "expired-access-token",
            "refresh": "refresh-token",
            "expires": 1,
            "token_endpoint": "https://evil.example/oauth/token",
        },
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.ensure_fresh_auth()

    assert exc_info.value.code == "invalid_token_endpoint"
    assert calls == []


def test_models_does_not_send_bearer_token_to_malicious_base_url(monkeypatch):
    calls = []

    class FakeResponse:
        ok = True

        def json(self):
            return {"data": [{"id": "safe-model"}]}

    class FakeRequests:
        @staticmethod
        def get(url, headers, timeout):
            calls.append((url, headers, timeout))
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    provider = xai.XaiGrokOAuthProvider()
    monkeypatch.setattr(
        provider,
        "read_auth",
        lambda: {
            "access": "access-token",
            "refresh": "refresh-token",
            "expires": int(time.time() * 1000) + 3_600_000,
            "base_url": "https://evil.example/v1",
        },
    )

    assert provider.models() == ["safe-model"]
    assert calls == [
        (
            "https://api.x.ai/v1/models",
            {"Accept": "application/json", "Authorization": "Bearer access-token"},
            30,
        )
    ]
