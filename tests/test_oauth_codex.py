from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plugins._oauth.helpers import codex
from plugins._oauth.extensions.python._functions.models.get_api_key.end._20_codex_account_dummy_key import (
    CodexAccountDummyKey,
)


def test_generate_pkce_produces_urlsafe_verifier_and_challenge():
    pair = codex.generate_pkce()

    assert 43 <= len(pair.verifier) <= 128
    assert pair.verifier
    assert pair.challenge
    assert "=" not in pair.verifier
    assert "=" not in pair.challenge


def test_build_authorize_url_uses_existing_a0_origin_callback(monkeypatch):
    monkeypatch.setattr(
        codex,
        "codex_config",
        lambda: {
            "issuer": "https://auth.openai.com",
            "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
            "scopes": [
                "openid",
                "profile",
                "email",
                "offline_access",
                "api.connectors.read",
                "api.connectors.invoke",
            ],
            "forced_workspace_id": "",
        },
    )
    pair = codex.PkcePair(verifier="verifier", challenge="challenge")
    auth_url = codex.build_authorize_url(
        "http://localhost:50001/auth/callback",
        "state",
        pair,
    )

    assert auth_url.startswith("https://auth.openai.com/oauth/authorize?")
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A50001%2Fauth%2Fcallback" in auth_url
    assert "code_challenge=challenge" in auth_url
    assert "originator=codex_cli_rs" in auth_url


def test_chat_messages_to_response_body_extracts_instructions():
    body = codex.chat_messages_to_response_body(
        {
            "model": "gpt-5.2",
            "messages": [
                {"role": "system", "content": "Be precise."},
                {"role": "user", "content": "Hello"},
            ],
            "temperature": 0.2,
            "reasoning_effort": "high",
        }
    )

    assert body["model"] == "gpt-5.2"
    assert body["instructions"] == "Be precise."
    assert body["input"] == [{"role": "user", "content": "Hello"}]
    assert body["temperature"] == 0.2
    assert body["reasoning"] == {"effort": "high"}


def test_response_text_reads_output_text_or_output_blocks():
    assert codex.response_text({"output_text": "direct"}) == "direct"

    assert (
        codex.response_text(
            {
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": "a"},
                            {"type": "output_text", "text": "b"},
                        ]
                    }
                ]
            }
        )
        == "ab"
    )


def test_parse_sse_block_joins_data_lines():
    event = codex.parse_sse_block(
        'event: response.completed\ndata: {"response":\ndata: {"id":"r"}}\n'
    )

    assert event["event"] == "response.completed"
    assert json.loads(event["data"]) == {"response": {"id": "r"}}


def test_extract_sse_text_deltas_reads_chat_completion_chunks():
    deltas = codex.extract_sse_text_deltas(
        {
            "id": "chatcmpl_test",
            "choices": [
                {"delta": {"role": "assistant"}},
                {"delta": {"content": "Hel"}},
                {"delta": {"content": "lo"}},
            ],
        }
    )

    assert deltas == ["Hel", "lo"]


def test_collect_completed_response_falls_back_to_text_deltas():
    class FakeResponse:
        encoding = "utf-8"

        def iter_content(self, chunk_size=8192, decode_unicode=True):
            del chunk_size, decode_unicode
            yield b'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
            yield b'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
            yield b'event: response.completed\ndata: {"response":{"output":[]}}\n\n'
            yield b"data: [DONE]\n\n"

    assert codex.collect_completed_response(FakeResponse()) == {"output": [], "output_text": "Hello"}


def test_normalize_usage_payload_reads_codex_windows():
    usage = codex.normalize_usage_payload(
        {
            "plan_type": "plus",
            "rate_limit": {
                "primary_window": {
                    "used_percent": 39,
                    "reset_at": 1_738_300_000,
                    "limit_window_seconds": 18_000,
                },
                "secondary_window": {
                    "used_percent": 15,
                    "reset_at": 1_738_900_000,
                    "limit_window_seconds": 604_800,
                },
            },
            "credits": {"has_credits": True, "unlimited": False, "balance": 5.39},
        }
    )

    assert usage["available"] is True
    assert usage["plan_type"] == "plus"
    assert usage["primary"]["used_percent"] == 39
    assert usage["primary"]["remaining_percent"] == 61
    assert usage["primary"]["label"] == "5h"
    assert usage["secondary"]["used_percent"] == 15
    assert usage["secondary"]["label"] == "7d"
    assert usage["credits"]["balance"] == 5.39


def test_normalize_usage_payload_accepts_zero_percent_headers():
    usage = codex.normalize_usage_payload(
        {},
        {
            "x-codex-primary-used-percent": "0",
            "x-codex-primary-window-minutes": "300",
        },
    )

    assert usage["available"] is True
    assert usage["primary"]["used_percent"] == 0
    assert usage["primary"]["remaining_percent"] == 100
    assert usage["primary"]["label"] == "5h"


def test_disconnect_auth_clears_chatgpt_tokens_and_preserves_api_key(tmp_path, monkeypatch):
    private_auth = tmp_path / "private-auth.json"
    shared_auth = tmp_path / "shared-auth.json"
    private_auth.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "OPENAI_API_KEY": None,
                "tokens": {
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "id_token": "id",
                    "account_id": "account",
                },
                "last_refresh": "2026-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    shared_auth.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "OPENAI_API_KEY": "sk-keep",
                "tokens": {"access_token": "access", "account_id": "account"},
                "last_refresh": "2026-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(codex, "resolve_auth_file_candidates", lambda: [private_auth, shared_auth])

    result = codex.disconnect_auth()

    assert result["disconnected"] is True
    assert str(private_auth) in result["removed_auth_files"]
    assert not private_auth.exists()
    preserved = json.loads(shared_auth.read_text(encoding="utf-8"))
    assert preserved == {"OPENAI_API_KEY": "sk-keep"}


def test_provider_config_uses_container_local_agent_zero_origin():
    provider_path = Path(__file__).resolve().parents[1] / "plugins/_oauth/conf/model_providers.yaml"
    provider_config = yaml.safe_load(provider_path.read_text(encoding="utf-8"))
    codex_provider = provider_config["chat"]["codex_oauth"]

    assert codex_provider["name"] == "Codex/ChatGPT Account"
    assert codex_provider["models_list"]["endpoint_url"] == "/models"
    assert codex_provider["kwargs"]["api_base"] == "http://127.0.0.1/oauth/codex/v1"
    assert "50001" not in json.dumps(codex_provider)


def test_codex_provider_reports_dummy_api_key_when_missing():
    data = {"args": ("codex_oauth",), "kwargs": {}, "result": "None"}

    CodexAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "oauth"


def test_codex_provider_preserves_configured_api_key():
    data = {"args": ("codex_oauth",), "kwargs": {}, "result": "configured"}

    CodexAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "configured"
