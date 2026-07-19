from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins._oauth.helpers.providers import github_copilot as copilot
from plugins._oauth.helpers.providers.base import GITHUB_COPILOT_PROVIDER_ID
from plugins._oauth.helpers.state import pop_device_attempt


def test_normalize_enterprise_domain_defaults_blank_to_github_dot_com():
    assert copilot.normalize_enterprise_domain("") == "github.com"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("github.example.com", "github.example.com"),
        ("https://github.example.com/org", "github.example.com"),
    ],
)
def test_normalize_enterprise_domain_accepts_domain_or_url(value, expected):
    assert copilot.normalize_enterprise_domain(value) == expected


def test_normalize_enterprise_domain_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid GitHub Enterprise"):
        copilot.normalize_enterprise_domain("http://")


def test_copilot_base_url_from_token_uses_proxy_endpoint():
    token = "tid=1;exp=9999999999;proxy-ep=proxy.individual.githubcopilot.com;sku=monthly"

    assert copilot.copilot_base_url_from_token(token, "") == "https://api.individual.githubcopilot.com"


def test_copilot_base_url_from_token_falls_back_for_malicious_proxy_endpoint():
    token = "tid=1;exp=9999999999;proxy-ep=evil.example.com;sku=monthly"

    assert copilot.copilot_base_url_from_token(token, "") == "https://api.individual.githubcopilot.com"


def test_poll_pending_and_slow_down_do_not_complete(monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    pending = provider._store_device_attempt_for_test("github.com", "device-pending", "PENDING", 5)
    slowed = provider._store_device_attempt_for_test("github.com", "device-slow", "SLOW", 5)

    def fake_poll(domain, device_code):
        if device_code == "device-slow":
            return {"error": "slow_down"}
        return {"error": "authorization_pending"}

    monkeypatch.setattr(copilot, "_post_device_poll", fake_poll)

    try:
        pending_result = provider.poll_login({"attempt_id": pending.attempt_id})
        slowed_result = provider.poll_login({"attempt_id": slowed.attempt_id})

        assert pending_result.ok is True
        assert pending_result.completed is False
        assert pending_result.interval == 5
        assert slowed_result.ok is True
        assert slowed_result.completed is False
        assert slowed_result.interval == 10
    finally:
        pop_device_attempt(pending.attempt_id)
        pop_device_attempt(slowed.attempt_id)


def test_poll_success_stores_copilot_credentials(tmp_path, monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    auth_path = tmp_path / "auth.json"
    attempt = provider._store_device_attempt_for_test("github.com", "device-ok", "OK", 5)

    monkeypatch.setattr(provider, "auth_path", lambda: auth_path)
    monkeypatch.setattr(
        copilot,
        "_post_device_poll",
        lambda domain, device_code: {"access_token": "github-access-token"},
    )
    monkeypatch.setattr(
        copilot,
        "refresh_copilot_token",
        lambda refresh, domain: {
            "provider": GITHUB_COPILOT_PROVIDER_ID,
            "type": "oauth",
            "refresh": refresh,
            "access": "copilot-access-token",
            "expires": 9_999_999_000,
            "enterprise_domain": "",
            "base_url": "https://api.individual.githubcopilot.com",
        },
    )
    monkeypatch.setattr(
        copilot,
        "enable_known_models",
        lambda token, domain: {"attempted": 8, "enabled": 8, "failed": []},
    )

    result = provider.poll_login({"attempt_id": attempt.attempt_id})

    assert result.ok is True
    assert result.completed is True
    saved = json.loads(auth_path.read_text(encoding="utf-8"))
    assert saved["provider"] == GITHUB_COPILOT_PROVIDER_ID
    assert saved["refresh"] == "github-access-token"
    assert saved["access"] == "copilot-access-token"
    assert saved["base_url"] == "https://api.individual.githubcopilot.com"


def test_models_returns_curated_list_without_network(monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    monkeypatch.setattr(provider, "read_auth", lambda: {})

    models = provider.models()

    assert models[:3] == ["gpt-5.2", "claude-sonnet-4.5", "claude-opus-4.5"]
    assert "grok-code-fast-1" in models


def test_ensure_fresh_auth_refreshes_expired_credentials(tmp_path, monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    auth_path = tmp_path / "auth.json"
    provider.write_auth = lambda data: copilot.write_private_json(auth_path, data)
    provider.read_auth = lambda: copilot.read_json_file(auth_path)
    provider.write_auth(
        {
            "provider": GITHUB_COPILOT_PROVIDER_ID,
            "type": "oauth",
            "refresh": "github-refresh-token",
            "access": "expired-access-token",
            "expires": 1,
            "enterprise_domain": "",
            "base_url": "https://api.individual.githubcopilot.com",
            "models_warning": "existing warning",
        }
    )

    monkeypatch.setattr(
        copilot,
        "refresh_copilot_token",
        lambda refresh, domain: {
            "provider": GITHUB_COPILOT_PROVIDER_ID,
            "type": "oauth",
            "refresh": refresh,
            "access": "fresh-access-token",
            "expires": int(time.time() * 1000) + 3_600_000,
            "enterprise_domain": "",
            "base_url": "https://api.individual.githubcopilot.com",
        },
    )

    auth = provider.ensure_fresh_auth()

    assert auth["refresh"] == "github-refresh-token"
    assert auth["access"] == "fresh-access-token"
    assert auth["models_warning"] == "existing warning"
    saved = json.loads(auth_path.read_text(encoding="utf-8"))
    assert saved["access"] == "fresh-access-token"


def test_models_uses_refreshed_auth_without_live_network(monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    calls = []

    monkeypatch.setattr(
        provider,
        "ensure_fresh_auth",
        lambda: {
            "access": "fresh-access-token",
            "base_url": "https://api.individual.githubcopilot.com",
        },
    )

    class FakeResponse:
        ok = True

        def json(self):
            return {"data": [{"id": "fresh-model"}]}

    class FakeRequests:
        @staticmethod
        def get(url, headers, timeout):
            calls.append((url, headers, timeout))
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    assert provider.models() == ["fresh-model"]
    assert calls[0][1]["Authorization"] == "Bearer fresh-access-token"


def test_models_does_not_send_bearer_token_to_malicious_base_url(monkeypatch):
    provider = copilot.GitHubCopilotOAuthProvider()
    calls = []

    monkeypatch.setattr(
        provider,
        "ensure_fresh_auth",
        lambda: {
            "access": "fresh-access-token",
            "base_url": "https://evil.example.com/v1",
        },
    )

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

    assert provider.models() == ["safe-model"]
    assert calls[0][0] == "https://api.individual.githubcopilot.com/models"
    assert not calls[0][0].startswith("https://evil.example.com")
    assert calls[0][1]["Authorization"] == "Bearer fresh-access-token"


def test_refresh_copilot_token_normalizes_malicious_proxy_endpoint(monkeypatch):
    class FakeResponse:
        ok = True
        status_code = 200

        def json(self):
            return {
                "token": "tid=1;exp=9999999999;proxy-ep=evil.example.com;sku=monthly",
                "expires_at": int(time.time()) + 3600,
            }

    class FakeRequests:
        @staticmethod
        def get(url, headers, timeout):
            return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", FakeRequests)

    auth = copilot.refresh_copilot_token("github-refresh-token", "")

    assert auth["base_url"] == "https://api.individual.githubcopilot.com"
