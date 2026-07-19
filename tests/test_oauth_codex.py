from __future__ import annotations

import json
import multiprocessing
import queue
import stat
import sys
import threading
import time
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plugins._oauth.helpers import codex
from plugins._oauth.helpers import routes
from plugins._oauth.helpers.providers import codex as codex_provider
from plugins._oauth.extensions.python._functions.models.get_api_key.end import (
    _20_oauth_account_dummy_key as oauth_dummy_key,
)


@pytest.fixture(autouse=True)
def use_temporary_auth_locks(tmp_path, monkeypatch):
    def lock_path(path: Path) -> Path:
        digest = codex.hashlib.sha256(codex._path_key(path).encode("utf-8")).hexdigest()
        return tmp_path / "locks" / f"{digest}.lock"

    monkeypatch.setattr(codex, "_auth_lock_path", lock_path)


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


def test_chat_messages_to_response_body_uses_current_codex_default_model():
    body = codex.chat_messages_to_response_body(
        {
            "messages": [
                {"role": "user", "content": "Hello"},
            ],
        }
    )

    assert body["model"] == "gpt-5.5"


def test_codex_provider_metadata_uses_upstream_models_only_by_default(monkeypatch):
    monkeypatch.setattr(
        codex_provider,
        "_codex_config",
        lambda: {
            "models": [],
            "proxy_base_path": "/oauth/codex",
            "callback_path": "/auth/callback",
        },
    )

    metadata = codex_provider.CodexOAuthProvider().metadata()

    assert metadata.default_model == "gpt-5.5"
    assert metadata.default_models == []


def test_codex_fetch_models_omits_fake_client_version(monkeypatch):
    calls = []

    class FakeResponse:
        ok = True

        def json(self):
            return {"models": [{"slug": "upstream-model"}]}

    monkeypatch.setattr(codex, "codex_config", lambda: {"models": []})
    monkeypatch.setattr(codex, "resolve_codex_version", lambda: "")
    monkeypatch.setattr(codex, "request_codex", lambda path, params=None: calls.append((path, params)) or FakeResponse())

    assert codex.fetch_models() == ["upstream-model"]
    assert calls == [("/models", None)]


def test_codex_fetch_model_catalog_preserves_model_metadata(monkeypatch):
    class FakeResponse:
        ok = True

        def json(self):
            return {
                "models": [
                    {
                        "slug": "gpt-5.5",
                        "display_name": "GPT-5.5",
                        "description": "Frontier coding model.",
                        "default_reasoning_level": "medium",
                        "base_instructions": "too large for the settings UI",
                    }
                ]
            }

    monkeypatch.setattr(codex, "codex_config", lambda: {"models": []})
    monkeypatch.setattr(codex, "resolve_codex_version", lambda: "0.142.5")
    monkeypatch.setattr(codex, "request_codex", lambda path, params=None: FakeResponse())

    assert codex.fetch_model_catalog() == [
        {
            "slug": "gpt-5.5",
            "id": "gpt-5.5",
            "display_name": "GPT-5.5",
            "description": "Frontier coding model.",
            "default_reasoning_level": "medium",
        }
    ]


def test_prepare_responses_body_adds_codex_client_metadata(monkeypatch):
    monkeypatch.setattr(
        codex,
        "build_client_metadata",
        lambda: {
            "x-codex-installation-id": "install-1",
            "session_id": "session-1",
            "thread_id": "thread-1",
            "x-codex-window-id": "agent-zero",
        },
    )

    body = codex.prepare_responses_body(
        {
            "model": "gpt-5.5",
            "input": "hello",
            "client_metadata": {
                "caller": "plugin-test",
                "x-codex-installation-id": "stale",
            },
            "reasoning": {"effort": "medium"},
            "include": ["output_text"],
        },
        force_stream=True,
    )

    assert body["client_metadata"] == {
        "caller": "plugin-test",
        "x-codex-installation-id": "install-1",
        "session_id": "session-1",
        "thread_id": "thread-1",
        "x-codex-window-id": "agent-zero",
    }
    assert body["input"] == [{"role": "user", "content": "hello"}]
    assert body["stream"] is True
    assert body["include"] == ["output_text", "reasoning.encrypted_content"]


def test_prepare_responses_body_sends_empty_continuation_input_as_list(monkeypatch):
    monkeypatch.setattr(codex, "build_client_metadata", lambda: {})

    body = codex.prepare_responses_body(
        {
            "model": "gpt-5.5",
            "input": "",
            "previous_response_id": "resp_1",
        },
        force_stream=True,
    )

    assert body["input"] == []
    assert body["previous_response_id"] == "resp_1"


def test_request_codex_sends_current_codex_headers_from_body(monkeypatch):
    calls = []
    body = json.dumps(
        {
            "client_metadata": {
                "x-codex-installation-id": "install-1",
                "session_id": "session-1",
                "thread_id": "thread-1",
                "x-codex-window-id": "agent-zero",
            }
        }
    )

    class FakeResponse:
        ok = True

    monkeypatch.setattr(
        codex,
        "codex_config",
        lambda: {
            "upstream_base_url": "https://chatgpt.example/backend-api/codex",
            "request_timeout_seconds": 120,
        },
    )
    monkeypatch.setattr(
        codex,
        "load_auth",
        lambda: codex.EffectiveAuth(
            access_token="access-token",
            account_id="account-1",
        ),
    )

    def fake_request(method, target, headers, data, params, timeout, stream):
        calls.append(
            {
                "method": method,
                "target": target,
                "headers": headers,
                "data": data,
                "params": params,
                "timeout": timeout,
                "stream": stream,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(codex.requests, "request", fake_request)

    response = codex.request_codex(
        "/responses",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
        stream=True,
    )

    assert response.ok is True
    call = calls[0]
    assert call["target"] == "https://chatgpt.example/backend-api/codex/responses"
    assert call["headers"]["Authorization"] == "Bearer access-token"
    assert call["headers"]["chatgpt-account-id"] == "account-1"
    assert call["headers"]["OpenAI-Beta"] == "responses=experimental"
    assert call["headers"]["originator"] == "codex_cli_rs"
    assert call["headers"]["x-codex-installation-id"] == "install-1"
    assert call["headers"]["session-id"] == "session-1"
    assert call["headers"]["thread-id"] == "thread-1"
    assert call["headers"]["x-codex-window-id"] == "agent-zero"


def test_chat_messages_to_response_body_preserves_image_parts_for_responses():
    data_url = "data:image/png;base64,abcd"

    body = codex.chat_messages_to_response_body(
        {
            "model": "gpt-5.5",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Inspect this screenshot."},
                        {"type": "text", "text": "Fresh screen attached."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
    )

    assert body["input"] == [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Inspect this screenshot."},
                {"type": "input_text", "text": "Fresh screen attached."},
                {"type": "input_image", "image_url": data_url, "detail": "auto"},
            ],
        }
    ]


def test_chat_messages_to_response_body_keeps_text_only_lists_as_text():
    body = codex.chat_messages_to_response_body(
        {
            "model": "gpt-5.5",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "first"},
                        {"type": "text", "text": "second"},
                    ],
                }
            ],
        }
    )

    assert body["input"] == [{"role": "user", "content": "first\nsecond"}]


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


def test_extract_sse_text_deltas_ignores_final_done_text():
    assert (
        codex.extract_sse_text_deltas(
            {"type": "response.output_text.done", "text": "Hello"},
            "response.output_text.done",
        )
        == []
    )


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


def test_token_error_message_prefers_description():
    class FakeResponse:
        status_code = 400
        text = '{"error":"invalid_grant","error_description":"refresh token was already used"}'

        @staticmethod
        def json():
            return {
                "error": "invalid_grant",
                "error_description": "refresh token was already used",
            }

    assert codex._token_error_message(FakeResponse()) == "refresh token was already used"


def test_refresh_tokens_sends_agent_zero_user_agent(monkeypatch):
    requests: list[dict] = []

    class FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {
                "access_token": "access-1",
                "refresh_token": "refresh-1",
            }

    def post(url, *, headers, json, timeout):
        requests.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(
        codex,
        "codex_config",
        lambda: {"token_url": "https://auth.example/oauth/token", "client_id": "client"},
    )
    monkeypatch.setattr(codex, "resolve_agent_zero_user_agent", lambda: "agent-zero/v1.18")
    monkeypatch.setattr(codex.requests, "post", post)

    assert codex.refresh_tokens("refresh-0") == {
        "id_token": "",
        "access_token": "access-1",
        "refresh_token": "refresh-1",
    }
    assert requests == [
        {
            "url": "https://auth.example/oauth/token",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "agent-zero/v1.18",
            },
            "json": {
                "client_id": "client",
                "grant_type": "refresh_token",
                "refresh_token": "refresh-0",
            },
            "timeout": 30,
        }
    ]


def test_default_auth_file_ignores_codex_cli_credentials(tmp_path, monkeypatch):
    shared_auth = tmp_path / ".codex" / "auth.json"
    private_auth = tmp_path / "usr" / "plugins" / "_oauth" / "codex" / "auth.json"
    shared_auth.parent.mkdir()
    shared_auth.write_text(json.dumps({"tokens": {"refresh_token": "shared"}}), encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(codex, "codex_config", lambda: {"auth_file_path": ""})
    monkeypatch.setattr(codex.files, "get_abs_path", lambda *parts: str(tmp_path.joinpath(*parts)))

    path, data = codex.read_auth_file()

    assert codex.resolve_auth_file_candidates() == [private_auth]
    assert path == private_auth
    assert data == {}


def test_explicit_codex_cli_auth_path_is_rejected(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setattr(codex, "codex_config", lambda: {"auth_file_path": str(codex_home / "auth.json")})

    with pytest.raises(RuntimeError, match="Agent Zero-owned auth file"):
        codex.resolve_auth_write_path()


def test_explicit_codex_cli_auth_hard_link_is_rejected(tmp_path, monkeypatch):
    shared_auth = tmp_path / ".codex" / "auth.json"
    shared_auth.parent.mkdir()
    shared_auth.write_text(json.dumps({"tokens": {"refresh_token": "shared"}}), encoding="utf-8")
    alias = tmp_path / "agent-zero-auth.json"
    alias.hardlink_to(shared_auth)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(codex, "codex_config", lambda: {"auth_file_path": str(alias)})

    with pytest.raises(RuntimeError, match="Agent Zero-owned auth file"):
        codex.resolve_auth_write_path()


def test_explicit_private_auth_hard_link_is_rejected(tmp_path, monkeypatch):
    private_auth = tmp_path / "private-auth.json"
    private_auth.write_text(json.dumps({"tokens": {"refresh_token": "private"}}), encoding="utf-8")
    alias = tmp_path / "agent-zero-auth.json"
    alias.hardlink_to(private_auth)
    monkeypatch.setattr(codex, "codex_config", lambda: {"auth_file_path": str(alias)})

    with pytest.raises(RuntimeError, match="Agent Zero-owned auth file"):
        codex.resolve_auth_write_path()


def test_write_auth_file_uses_atomic_replace_and_private_permissions(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    replacements: list[tuple[Path, Path]] = []
    replace = codex.os.replace

    def record_replace(source, destination):
        replacements.append((Path(source), Path(destination)))
        replace(source, destination)

    monkeypatch.setattr(codex.os, "replace", record_replace)

    codex.write_auth_file(auth_path, {"tokens": {"refresh_token": "refresh"}})

    assert json.loads(auth_path.read_text(encoding="utf-8")) == {
        "tokens": {"refresh_token": "refresh"}
    }
    assert stat.S_IMODE(auth_path.stat().st_mode) == 0o600
    assert len(replacements) == 1
    assert replacements[0][0] != auth_path
    assert replacements[0][1] == auth_path
    assert list(tmp_path.glob(".auth.json.*.tmp")) == []


def test_write_auth_file_falls_back_for_file_bind_mount(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(json.dumps({"tokens": {"refresh_token": "refresh-0"}}), encoding="utf-8")

    def reject_replace(source, destination):
        raise OSError(codex.errno.EBUSY, "Device or resource busy", destination)

    monkeypatch.setattr(codex.os, "replace", reject_replace)

    codex.write_auth_file(auth_path, {"tokens": {"refresh_token": "refresh-1"}})

    assert json.loads(auth_path.read_text(encoding="utf-8")) == {
        "tokens": {"refresh_token": "refresh-1"}
    }
    assert stat.S_IMODE(auth_path.stat().st_mode) == 0o600
    assert list(tmp_path.glob(".auth.json.*.tmp")) == []


def test_write_auth_file_falls_back_when_parent_rejects_temporary_files(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(json.dumps({"tokens": {"refresh_token": "refresh-0"}}), encoding="utf-8")
    open_file = codex.os.open

    def reject_temporary_file(path, flags, mode=0o777):
        if str(path).endswith(".tmp"):
            raise OSError(codex.errno.EACCES, "Permission denied", path)
        return open_file(path, flags, mode)

    monkeypatch.setattr(codex.os, "open", reject_temporary_file)

    codex.write_auth_file(auth_path, {"tokens": {"refresh_token": "refresh-1"}})

    assert json.loads(auth_path.read_text(encoding="utf-8")) == {
        "tokens": {"refresh_token": "refresh-1"}
    }
    assert stat.S_IMODE(auth_path.stat().st_mode) == 0o600
    assert not auth_path.with_name(".auth.json.lock").exists()


def test_resolve_auth_write_path_preserves_custom_symlink_target(tmp_path, monkeypatch):
    target = tmp_path / "mounted" / "auth.json"
    target.parent.mkdir()
    target.write_text(json.dumps({"tokens": {"refresh_token": "refresh-0"}}), encoding="utf-8")
    symlink = tmp_path / "auth.json"
    symlink.symlink_to(target)
    monkeypatch.setattr(codex, "codex_config", lambda: {"auth_file_path": str(symlink)})

    resolved_path = codex.resolve_auth_write_path()
    codex.write_auth_file(resolved_path, {"tokens": {"refresh_token": "refresh-1"}})

    assert resolved_path == target
    assert symlink.is_symlink()
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "tokens": {"refresh_token": "refresh-1"}
    }


def test_lock_file_retries_windows_contention(tmp_path, monkeypatch):
    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        def __init__(self):
            self.calls: list[int] = []

        def locking(self, _descriptor: int, mode: int, _length: int) -> None:
            self.calls.append(mode)
            if mode == self.LK_NBLCK and self.calls.count(mode) < 3:
                raise OSError(codex.errno.EACCES, "Permission denied")

    fake_msvcrt = FakeMsvcrt()
    sleeps: list[float] = []
    monkeypatch.setattr(codex, "fcntl", None)
    monkeypatch.setattr(codex, "msvcrt", fake_msvcrt)
    monkeypatch.setattr(codex.time, "sleep", sleeps.append)

    with (tmp_path / "auth.lock").open("a+b") as handle:
        codex._lock_file(handle)
        codex._unlock_file(handle)

    assert fake_msvcrt.calls == [
        fake_msvcrt.LK_NBLCK,
        fake_msvcrt.LK_NBLCK,
        fake_msvcrt.LK_NBLCK,
        fake_msvcrt.LK_UNLCK,
    ]
    assert sleeps == [codex.WINDOWS_LOCK_RETRY_SECONDS, codex.WINDOWS_LOCK_RETRY_SECONDS]


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("localhost:5000", True),
        ("127.0.0.1:5000", True),
        ("[::1]:5000", True),
        ("::1", True),
        ("example.com:5000", False),
    ],
)
def test_proxy_local_host_detection_supports_loopback_ipv6(host, expected):
    assert routes._host_is_local(host) is expected


def test_load_auth_serializes_refresh_across_threads(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    _write_refreshable_auth(auth_path)
    monkeypatch.setattr(codex, "resolve_auth_write_path", lambda: auth_path)
    refresh_started = threading.Event()
    release_refresh = threading.Event()
    calls: list[str] = []
    results: list[codex.EffectiveAuth] = []

    def refresh_tokens(refresh_token: str) -> dict[str, str]:
        calls.append(refresh_token)
        refresh_started.set()
        assert release_refresh.wait(timeout=2)
        return _rotated_tokens()

    monkeypatch.setattr(codex, "refresh_tokens", refresh_tokens)
    first = threading.Thread(target=lambda: results.append(codex.load_auth()))
    second = threading.Thread(target=lambda: results.append(codex.load_auth()))

    first.start()
    assert refresh_started.wait(timeout=2)
    second.start()
    time.sleep(0.1)

    assert calls == ["refresh-0"]
    release_refresh.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert calls == ["refresh-0"]
    assert [result.refresh_token for result in results] == ["refresh-1", "refresh-1"]


def test_load_auth_holds_lock_until_rotated_token_is_persisted(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    _write_refreshable_auth(auth_path)
    monkeypatch.setattr(codex, "resolve_auth_write_path", lambda: auth_path)
    persist_started = threading.Event()
    release_persist = threading.Event()
    calls: list[str] = []
    results: list[codex.EffectiveAuth] = []
    write_auth_file = codex._write_auth_file_unlocked

    def refresh_tokens(refresh_token: str) -> dict[str, str]:
        calls.append(refresh_token)
        return _rotated_tokens()

    def delay_write(path: Path, data: dict) -> None:
        persist_started.set()
        assert release_persist.wait(timeout=2)
        write_auth_file(path, data)

    monkeypatch.setattr(codex, "refresh_tokens", refresh_tokens)
    monkeypatch.setattr(codex, "_write_auth_file_unlocked", delay_write)
    first = threading.Thread(target=lambda: results.append(codex.load_auth()))
    second = threading.Thread(target=lambda: results.append(codex.load_auth()))

    first.start()
    assert persist_started.wait(timeout=2)
    second.start()
    time.sleep(0.1)

    assert calls == ["refresh-0"]
    release_persist.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert calls == ["refresh-0"]
    assert [result.refresh_token for result in results] == ["refresh-1", "refresh-1"]


def test_load_auth_serializes_refresh_across_processes(tmp_path):
    auth_path = tmp_path / "auth.json"
    _write_refreshable_auth(auth_path)
    context = multiprocessing.get_context("spawn")
    refresh_started = context.Event()
    release_refresh = context.Event()
    calls = context.Queue()
    results = context.Queue()
    process_args = (str(auth_path), refresh_started, release_refresh, calls, results)
    first = context.Process(target=_load_auth_in_process, args=process_args)
    second = context.Process(target=_load_auth_in_process, args=process_args)

    first.start()
    assert refresh_started.wait(timeout=2)
    assert calls.get(timeout=2) == "refresh-0"
    second.start()
    with pytest.raises(queue.Empty):
        calls.get(timeout=0.2)

    release_refresh.set()
    first.join(timeout=3)
    second.join(timeout=3)

    assert first.exitcode == 0
    assert second.exitcode == 0
    with pytest.raises(queue.Empty):
        calls.get(timeout=0.2)
    assert sorted([results.get(timeout=2), results.get(timeout=2)]) == ["refresh-1", "refresh-1"]


def test_disconnect_auth_only_mutates_agent_zero_private_auth_file(tmp_path, monkeypatch):
    private_auth = tmp_path / "private-auth.json"
    shared_auth = tmp_path / ".codex" / "auth.json"
    private_auth.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "OPENAI_API_KEY": "sk-keep",
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
    shared_auth.parent.mkdir()
    shared_auth.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "OPENAI_API_KEY": None,
                "tokens": {"access_token": "access", "account_id": "account"},
                "last_refresh": "2026-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    shared_before = shared_auth.read_text(encoding="utf-8")
    monkeypatch.setattr(codex, "resolve_auth_write_path", lambda: private_auth)

    result = codex.disconnect_auth()

    assert result["disconnected"] is True
    assert result["preserved_auth_files"] == [str(private_auth)]
    preserved = json.loads(private_auth.read_text(encoding="utf-8"))
    assert preserved == {"OPENAI_API_KEY": "sk-keep"}
    assert shared_auth.read_text(encoding="utf-8") == shared_before


def _write_refreshable_auth(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "tokens": {
                    "access_token": "",
                    "refresh_token": "refresh-0",
                    "id_token": "",
                    "account_id": "account",
                },
                "last_refresh": "",
            }
        ),
        encoding="utf-8",
    )


def _rotated_tokens() -> dict[str, str]:
    return {
        "access_token": "access-1",
        "refresh_token": "refresh-1",
        "id_token": "",
    }


def _load_auth_in_process(auth_path: str, refresh_started, release_refresh, calls, results) -> None:
    codex.resolve_auth_write_path = lambda: Path(auth_path)
    codex._auth_lock_path = lambda _path: Path(auth_path).parent / ".auth.lock"

    def refresh_tokens(refresh_token: str) -> dict[str, str]:
        calls.put(refresh_token)
        refresh_started.set()
        assert release_refresh.wait(timeout=5)
        return _rotated_tokens()

    codex.refresh_tokens = refresh_tokens
    results.put(codex.load_auth().refresh_token)


def test_provider_config_uses_container_local_agent_zero_origin():
    provider_path = Path(__file__).resolve().parents[1] / "plugins/_oauth/conf/model_providers.yaml"
    provider_config = yaml.safe_load(provider_path.read_text(encoding="utf-8"))
    codex_provider = provider_config["chat"]["codex_oauth"]

    assert codex_provider["name"] == "Codex/ChatGPT Account"
    assert codex_provider["models_list"]["endpoint_url"] == "/models"
    assert codex_provider["kwargs"]["api_base"] == "http://127.0.0.1/oauth/codex/v1"
    assert "50001" not in json.dumps(codex_provider)


def test_codex_provider_leaves_api_key_empty_until_connected(monkeypatch):
    monkeypatch.setattr(oauth_dummy_key, "oauth_provider_is_connected", lambda _provider_id: False)
    data = {"args": ("codex_oauth",), "kwargs": {}, "result": "None"}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "None"


def test_codex_provider_reports_dummy_api_key_when_connected(monkeypatch):
    monkeypatch.setattr(oauth_dummy_key, "oauth_provider_is_connected", lambda _provider_id: True)
    data = {"args": ("codex_oauth",), "kwargs": {}, "result": "None"}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "oauth"


def test_codex_provider_preserves_configured_api_key():
    data = {"args": ("codex_oauth",), "kwargs": {}, "result": "configured"}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "configured"
