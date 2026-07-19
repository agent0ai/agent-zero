from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import stat
import types
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import helpers.api  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name != "flask":
        raise
    fake_api = types.ModuleType("helpers.api")

    class ApiHandler:
        def __init__(self, app=None, thread_lock=None):
            self.app = app
            self.thread_lock = thread_lock

    class Request:
        pass

    fake_api.ApiHandler = ApiHandler
    fake_api.Request = Request
    sys.modules["helpers.api"] = fake_api

try:
    import helpers.extension  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name not in {"regex", "simpleeval"}:
        raise
    fake_extension = types.ModuleType("helpers.extension")

    class Extension:
        def __init__(self, agent=None, **kwargs):
            self.agent = agent
            self.kwargs = kwargs

    fake_extension.Extension = Extension
    sys.modules["helpers.extension"] = fake_extension

from plugins._oauth.api import status as status_api
from plugins._oauth.api import disconnect as disconnect_api
from plugins._oauth.api import manual_callback as manual_callback_api
from plugins._oauth.api import poll_device_login as poll_device_login_api
from plugins._oauth.api import start_device_login as start_device_login_api
from plugins._oauth.api import start_login as start_login_api
from plugins._oauth.api.models import Models
from plugins._oauth.extensions.python._functions.models.get_api_key.end import (
    _20_oauth_account_dummy_key as oauth_dummy_key,
)
from plugins._oauth.helpers import state
from plugins._oauth.helpers.providers import base as provider_base
from plugins._oauth.helpers.providers.base import (
    CODEX_PROVIDER_ID,
    DUMMY_API_KEY,
    GEMINI_API_PROVIDER_ID,
    GITHUB_COPILOT_PROVIDER_ID,
    XAI_GROK_PROVIDER_ID,
    CallbackResult,
    LoginPollResult,
    LoginStartResult,
    ProviderError,
    provider_data_dir,
    public_error,
    write_private_json,
)
from plugins._oauth.helpers.providers.registry import get_provider, provider_registry
from plugins._oauth.helpers.summary import build_oauth_status_summary
from plugins._oauth.helpers.usage_plans import usage_plan_catalog


class FakeRequest:
    headers = {}
    url_root = "http://localhost:50001/"


def test_registry_exposes_initial_oauth_providers():
    registry = provider_registry()

    assert list(registry) == [
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    ]
    assert registry[CODEX_PROVIDER_ID].metadata().display_name == "Codex/ChatGPT"
    assert registry[GITHUB_COPILOT_PROVIDER_ID].metadata().model_provider_id == GITHUB_COPILOT_PROVIDER_ID
    assert registry[GEMINI_API_PROVIDER_ID].metadata().supports_oauth_client_config is True
    assert registry[XAI_GROK_PROVIDER_ID].metadata().auth_flow == "browser_pkce"


def test_get_provider_rejects_unknown_provider_id():
    with pytest.raises(KeyError, match="Unknown OAuth provider"):
        get_provider("missing")


def test_get_provider_coerces_non_string_provider_id():
    with pytest.raises(KeyError, match="Unknown OAuth provider: 123"):
        get_provider(123)


@pytest.mark.parametrize("provider_id", [0, False])
def test_get_provider_rejects_falsey_non_string_provider_id(provider_id):
    with pytest.raises(KeyError, match=f"Unknown OAuth provider: {provider_id}"):
        get_provider(provider_id)


@pytest.mark.parametrize("provider_id", [None, ""])
def test_get_provider_defaults_empty_provider_id_to_codex(provider_id):
    assert get_provider(provider_id).provider_id == CODEX_PROVIDER_ID


def test_state_keeps_login_attempts_provider_scoped():
    attempt = state.put_attempt(
        "state-a",
        "verifier-a",
        "http://127.0.0.1:56121/callback",
        provider_id=XAI_GROK_PROVIDER_ID,
        extra={"nonce": "nonce-a"},
    )

    loaded = state.get_attempt("state-a")

    assert loaded == attempt
    assert loaded.provider_id == XAI_GROK_PROVIDER_ID
    assert loaded.extra == {"nonce": "nonce-a"}
    assert state.pop_attempt("state-a") == attempt
    assert state.get_attempt("state-a") is None


def test_state_keeps_device_attempts_provider_scoped():
    attempt = state.put_device_attempt(
        "attempt-a",
        "device-a",
        "USER-CODE",
        5,
        99_999_999_999,
        provider_id=GITHUB_COPILOT_PROVIDER_ID,
        extra={"domain": "github.com"},
    )

    loaded = state.get_device_attempt("attempt-a")

    assert loaded == attempt
    assert loaded.provider_id == GITHUB_COPILOT_PROVIDER_ID
    assert loaded.extra == {"domain": "github.com"}
    assert state.pop_device_attempt("attempt-a") == attempt
    assert state.get_device_attempt("attempt-a") is None


def test_starter_providers_report_login_flow_values():
    class FakeProvider:
        def __init__(self, provider_id: str, flow: str):
            self.provider_id = provider_id
            self.flow = flow

        def start_login(self, input=None, request=None):
            return LoginStartResult(
                ok=False,
                provider_id=self.provider_id,
                flow=self.flow,
                message="not connected",
            )

    registry = {
        GITHUB_COPILOT_PROVIDER_ID: FakeProvider(GITHUB_COPILOT_PROVIDER_ID, "device_code"),
        XAI_GROK_PROVIDER_ID: FakeProvider(XAI_GROK_PROVIDER_ID, "browser_pkce"),
    }

    github = registry[GITHUB_COPILOT_PROVIDER_ID].start_login({})
    xai = registry[XAI_GROK_PROVIDER_ID].start_login({})

    assert github.flow == "device_code"
    assert xai.flow == "browser_pkce"


def test_result_contract_preserves_account_id_with_account_label():
    poll = LoginPollResult(
        ok=True,
        provider_id=CODEX_PROVIDER_ID,
        account_label="user@example.com",
        account_id="acct-1",
    )
    callback = CallbackResult(
        ok=True,
        provider_id=CODEX_PROVIDER_ID,
        account_label="user@example.com",
        account_id="acct-1",
    )

    assert poll.account_label == "user@example.com"
    assert poll.account_id == "acct-1"
    assert callback.account_label == "user@example.com"
    assert callback.account_id == "acct-1"


def test_provider_data_dir_creates_directory(tmp_path, monkeypatch):
    fake_files = types.SimpleNamespace(
        USER_DIR="usr",
        PLUGINS_DIR="plugins",
        get_abs_path=lambda *parts: str(tmp_path.joinpath(*parts)),
    )
    monkeypatch.setitem(sys.modules, "helpers.files", fake_files)

    path = provider_data_dir("provider-a")

    assert path == tmp_path / "usr" / "plugins" / "_oauth" / "provider-a"
    assert path.is_dir()


@pytest.mark.parametrize("provider_slug", ["../codex", "nested/codex", "nested\\codex", "", "."])
def test_provider_data_dir_rejects_unsafe_slugs(provider_slug):
    with pytest.raises(ProviderError, match="Invalid OAuth provider storage slug.") as exc_info:
        provider_data_dir(provider_slug)

    assert exc_info.value.code == "invalid_provider_slug"


def test_write_private_json_does_not_reuse_preexisting_temp_file(tmp_path):
    path = tmp_path / "auth.json"
    stale_tmp = tmp_path / "auth.json.tmp"
    stale_tmp.write_text("stale", encoding="utf-8")
    stale_tmp.chmod(0o666)
    stale_inode = stale_tmp.stat().st_ino

    write_private_json(path, {"access_token": "secret"})

    assert stale_tmp.read_text(encoding="utf-8") == "stale"
    assert stale_tmp.stat().st_ino == stale_inode
    assert path.read_text(encoding="utf-8").find("secret") > -1
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_private_json_cleans_up_generated_temp_file_on_error(tmp_path, monkeypatch):
    def fail_dump(*args, **kwargs):
        raise RuntimeError("write failed")

    monkeypatch.setattr(provider_base.json, "dump", fail_dump)

    path = tmp_path / "auth.json"
    with pytest.raises(RuntimeError, match="write failed"):
        write_private_json(path, {"token": "secret"})

    assert list(tmp_path.glob(".auth.json.*.tmp")) == []
    assert not path.exists()


def test_write_private_json_does_not_follow_preexisting_temp_symlink(tmp_path):
    leak_target = tmp_path / "leak-target"
    leak_target.write_text("safe", encoding="utf-8")
    stale_tmp = tmp_path / "auth.json.tmp"
    try:
        stale_tmp.symlink_to(leak_target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation is not supported: {exc}")

    path = tmp_path / "auth.json"
    write_private_json(path, {"token": "secret"})

    assert leak_target.read_text(encoding="utf-8") == "safe"
    assert stale_tmp.is_symlink()
    assert '"token": "secret"' in path.read_text(encoding="utf-8")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_private_json_sets_generated_temp_private_before_dump(tmp_path, monkeypatch):
    observed_modes = []
    real_dump = provider_base.json.dump

    def inspect_mode_before_dump(data, handle, *args, **kwargs):
        temp_files = list(tmp_path.glob(".auth.json.*.tmp"))
        assert len(temp_files) == 1
        observed_modes.append(stat.S_IMODE(temp_files[0].stat().st_mode))
        return real_dump(data, handle, *args, **kwargs)

    monkeypatch.setattr(provider_base.json, "dump", inspect_mode_before_dump)

    path = tmp_path / "auth.json"
    write_private_json(path, {"token": "secret"})

    assert observed_modes == [0o600]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_public_error_returns_user_facing_string():
    assert public_error(RuntimeError("visible")) == "visible"
    assert public_error(Exception()) == "Exception"


def test_status_api_returns_provider_registry_shape(monkeypatch):
    class FakeProvider:
        def __init__(self, provider_id: str):
            self.provider_id = provider_id

        def status(self):
            return {"provider_id": self.provider_id, "connected": False}

    fake_registry = {
        provider_id: FakeProvider(provider_id)
        for provider_id in [
            CODEX_PROVIDER_ID,
            GITHUB_COPILOT_PROVIDER_ID,
            GEMINI_API_PROVIDER_ID,
            XAI_GROK_PROVIDER_ID,
        ]
    }
    monkeypatch.setattr(status_api, "provider_registry", lambda: fake_registry)
    monkeypatch.setattr(status_api, "is_installed", lambda: True)

    response = asyncio.run(status_api.Status(None, None).process({}, FakeRequest()))

    assert response["ok"] is True
    assert response["routes_installed"] is True
    assert [provider["provider_id"] for provider in response["providers"]] == [
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    ]
    assert set(response["provider_map"]) == {
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    }
    assert set(response["usage_plan_catalog"]) >= {
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    }
    assert set(response["usage_plan_catalog"]) == {
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    }
    assert response["codex"] == response["provider_map"][CODEX_PROVIDER_ID]


def test_oauth_status_summary_adds_accounts_and_usage_windows():
    class FakeProvider:
        provider_id = CODEX_PROVIDER_ID

        def status(self):
            return {
                "provider_id": CODEX_PROVIDER_ID,
                "display_name": "Codex/ChatGPT",
                "short_name": "Codex",
                "connected": True,
                "account_label": "user@example.com",
                "usage": {
                    "available": True,
                    "primary": {"remaining_percent": 91, "label": "5h", "reset_at": 123},
                    "secondary": {"used_percent": 14, "label": "7d", "reset_at": 456},
                },
            }

    summary = build_oauth_status_summary(
        provider_registry=lambda: {CODEX_PROVIDER_ID: FakeProvider()},
        routes_installed=lambda: True,
    )

    assert summary["routes_installed"] is True
    assert summary["connected_count"] == 1
    assert summary["oauth_accounts"]["connected"][0]["account_label"] == "user@example.com"
    assert summary["provider_map"][CODEX_PROVIDER_ID]["usage_windows"] == [
        {"key": "primary", "title": "Session", "label": "5h", "remaining_percent": 91.0, "reset_at": 123},
        {"key": "secondary", "title": "Week", "label": "7d", "remaining_percent": 86.0, "reset_at": 456},
    ]


def test_status_api_contains_provider_status_exceptions(monkeypatch):
    class GoodProvider:
        provider_id = CODEX_PROVIDER_ID

        def status(self):
            return {"provider_id": CODEX_PROVIDER_ID, "connected": True}

    class FailingProvider:
        provider_id = XAI_GROK_PROVIDER_ID

        def metadata(self):
            return {
                "provider_id": XAI_GROK_PROVIDER_ID,
                "display_name": "xAI Grok",
                "auth_flow": "browser_pkce",
            }

        def status(self):
            raise RuntimeError("status failed")

    monkeypatch.setattr(
        status_api,
        "provider_registry",
        lambda: {
            CODEX_PROVIDER_ID: GoodProvider(),
            XAI_GROK_PROVIDER_ID: FailingProvider(),
        },
    )
    monkeypatch.setattr(status_api, "is_installed", lambda: True)

    response = asyncio.run(status_api.Status(None, None).process({}, FakeRequest()))

    assert response["ok"] is True
    assert response["provider_map"][CODEX_PROVIDER_ID]["connected"] is True
    assert response["provider_map"][XAI_GROK_PROVIDER_ID] == {
        "provider_id": XAI_GROK_PROVIDER_ID,
        "display_name": "xAI Grok",
        "auth_flow": "browser_pkce",
        "connected": False,
        "error": "status failed",
    }


@pytest.mark.parametrize(
    ("provider_id", "expected_flow"),
    [
        (GITHUB_COPILOT_PROVIDER_ID, "device_code"),
        (GEMINI_API_PROVIDER_ID, "browser_pkce"),
        (XAI_GROK_PROVIDER_ID, "browser_pkce"),
    ],
)
def test_start_login_dispatches_to_selected_starter_provider(monkeypatch, provider_id, expected_flow):
    class FakeProvider:
        def __init__(self, provider_id: str):
            self.provider_id = provider_id

        def start_login(self, input, request):
            return LoginStartResult(
                ok=False,
                provider_id=self.provider_id,
                flow=expected_flow,
                message="not connected",
            )

    monkeypatch.setattr(start_login_api, "get_provider", lambda selected: FakeProvider(selected))

    response = asyncio.run(
        start_login_api.StartLogin(None, None).process(
            {"provider_id": provider_id},
            FakeRequest(),
        )
    )

    assert response["ok"] is False
    assert response["provider_id"] == provider_id
    assert response["flow"] == expected_flow
    assert response["message"]


def test_start_login_without_provider_id_uses_legacy_codex_browser_login(monkeypatch):
    calls = []

    class FakeCodexProvider:
        def start_browser_login(self, input, request):
            calls.append(("browser", input, request))
            return LoginStartResult(
                ok=True,
                provider_id=CODEX_PROVIDER_ID,
                flow="browser_pkce",
                auth_url="http://auth.example/authorize",
                redirect_uri="http://localhost/auth/callback",
            )

        def start_login(self, input, request):
            calls.append(("device", input, request))
            return LoginStartResult(ok=True, provider_id=CODEX_PROVIDER_ID, flow="device_code")

    monkeypatch.setattr(start_login_api, "get_provider", lambda provider_id: FakeCodexProvider())

    request = FakeRequest()
    response = asyncio.run(start_login_api.StartLogin(None, None).process({}, request))

    assert calls == [("browser", {}, request)]
    assert response["ok"] is True
    assert response["provider_id"] == CODEX_PROVIDER_ID
    assert response["flow"] == "browser_pkce"
    assert response["auth_url"] == "http://auth.example/authorize"
    assert response["redirect_uri"] == "http://localhost/auth/callback"


def test_start_login_with_blank_provider_id_uses_provider_aware_codex_login(monkeypatch):
    calls = []

    class FakeCodexProvider:
        def start_browser_login(self, input, request):
            calls.append(("browser", input, request))
            return LoginStartResult(ok=True, provider_id=CODEX_PROVIDER_ID, flow="browser_pkce")

        def start_login(self, input, request):
            calls.append(("device", input, request))
            return LoginStartResult(ok=True, provider_id=CODEX_PROVIDER_ID, flow="device_code")

    monkeypatch.setattr(start_login_api, "get_provider", lambda provider_id: FakeCodexProvider())

    request = FakeRequest()
    response = asyncio.run(
        start_login_api.StartLogin(None, None).process({"provider_id": ""}, request)
    )

    assert calls == [("device", {"provider_id": ""}, request)]
    assert response["ok"] is True
    assert response["provider_id"] == CODEX_PROVIDER_ID
    assert response["flow"] == "device_code"


def test_start_login_provider_exception_returns_structured_error(monkeypatch):
    class FailingProvider:
        def start_login(self, input, request):
            raise RuntimeError("login failed")

    monkeypatch.setattr(start_login_api, "get_provider", lambda provider_id: FailingProvider())

    response = asyncio.run(
        start_login_api.StartLogin(None, None).process(
            {"provider_id": GITHUB_COPILOT_PROVIDER_ID},
            FakeRequest(),
        )
    )

    assert response == {
        "ok": False,
        "provider_id": GITHUB_COPILOT_PROVIDER_ID,
        "error": "login failed",
    }


def test_manual_callback_dispatches_to_xai_provider_without_active_attempt():
    response = asyncio.run(
        manual_callback_api.ManualCallback(None, None).process(
            {"provider_id": XAI_GROK_PROVIDER_ID, "callback_url": "http://localhost/callback?code=abc"},
            FakeRequest(),
        )
    )

    assert response["ok"] is False
    assert response["provider_id"] == XAI_GROK_PROVIDER_ID
    assert "no active xai grok sign-in attempt" in response["error"].lower()


def test_start_device_login_wrapper_defaults_to_codex_provider(monkeypatch):
    calls = []

    class FakeProvider:
        def start_login(self, input, request):
            calls.append((input, request))
            return LoginStartResult(
                ok=True,
                provider_id=CODEX_PROVIDER_ID,
                flow="device_code",
                attempt_id="attempt-1",
            )

    monkeypatch.setattr(
        start_device_login_api,
        "get_provider",
        lambda provider_id: calls.append(("provider_id", provider_id)) or FakeProvider(),
    )

    request = FakeRequest()
    response = asyncio.run(
        start_device_login_api.StartDeviceLogin(None, None).process(
            {"ignored_provider_id": XAI_GROK_PROVIDER_ID},
            request,
        )
    )

    assert calls[0] == ("provider_id", CODEX_PROVIDER_ID)
    assert calls[1][0] == {"ignored_provider_id": XAI_GROK_PROVIDER_ID}
    assert calls[1][1] is request
    assert response["ok"] is True
    assert response["provider_id"] == CODEX_PROVIDER_ID
    assert response["flow"] == "device_code"
    assert response["attempt_id"] == "attempt-1"


def test_start_device_login_with_provider_id_calls_github_provider(monkeypatch):
    calls = []

    class FakeProvider:
        def start_login(self, input, request):
            calls.append((input, request))
            return LoginStartResult(
                ok=True,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                flow="device_code",
                attempt_id="github-attempt-1",
                verification_url="https://github.com/login/device",
                user_code="1234-5678",
            )

    monkeypatch.setattr(
        start_device_login_api,
        "get_provider",
        lambda provider_id: calls.append(("provider_id", provider_id)) or FakeProvider(),
    )

    request = FakeRequest()
    payload = {"provider_id": GITHUB_COPILOT_PROVIDER_ID, "enterprise_domain": ""}
    response = asyncio.run(
        start_device_login_api.StartDeviceLogin(None, None).process(payload, request)
    )

    assert calls[0] == ("provider_id", GITHUB_COPILOT_PROVIDER_ID)
    assert calls[1] == (payload, request)
    assert response["ok"] is True
    assert response["provider_id"] == GITHUB_COPILOT_PROVIDER_ID
    assert response["flow"] == "device_code"
    assert response["attempt_id"] == "github-attempt-1"
    assert response["verification_url"] == "https://github.com/login/device"
    assert response["user_code"] == "1234-5678"


def test_start_device_login_unknown_provider_returns_structured_error():
    response = asyncio.run(
        start_device_login_api.StartDeviceLogin(None, None).process(
            {"provider_id": "missing"},
            FakeRequest(),
        )
    )

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert "Unknown OAuth provider" in response["error"]


def test_poll_device_login_wrapper_calls_codex_provider(monkeypatch):
    calls = []

    class FakeProvider:
        def poll_login(self, input, request):
            calls.append((input, request))
            return LoginPollResult(
                ok=True,
                provider_id=CODEX_PROVIDER_ID,
                completed=True,
                account_label="user@example.com",
                account_id="account-1",
            )

    monkeypatch.setattr(
        poll_device_login_api,
        "get_provider",
        lambda provider_id: calls.append(("provider_id", provider_id)) or FakeProvider(),
    )

    request = FakeRequest()
    response = asyncio.run(
        poll_device_login_api.PollDeviceLogin(None, None).process(
            {"attempt_id": "attempt-1"},
            request,
        )
    )

    assert calls[0] == ("provider_id", CODEX_PROVIDER_ID)
    assert calls[1][0] == {"attempt_id": "attempt-1"}
    assert calls[1][1] is request
    assert response["ok"] is True
    assert response["provider_id"] == CODEX_PROVIDER_ID
    assert response["completed"] is True
    assert response["account_label"] == "user@example.com"
    assert response["account_id"] == "account-1"


def test_poll_device_login_with_provider_id_calls_github_provider(monkeypatch):
    calls = []

    class FakeProvider:
        def poll_login(self, input, request):
            calls.append((input, request))
            return LoginPollResult(
                ok=True,
                provider_id=GITHUB_COPILOT_PROVIDER_ID,
                completed=True,
                account_label="github.com",
            )

    monkeypatch.setattr(
        poll_device_login_api,
        "get_provider",
        lambda provider_id: calls.append(("provider_id", provider_id)) or FakeProvider(),
    )

    request = FakeRequest()
    payload = {"provider_id": GITHUB_COPILOT_PROVIDER_ID, "attempt_id": "attempt-1"}
    response = asyncio.run(
        poll_device_login_api.PollDeviceLogin(None, None).process(payload, request)
    )

    assert calls[0] == ("provider_id", GITHUB_COPILOT_PROVIDER_ID)
    assert calls[1] == (payload, request)
    assert response["ok"] is True
    assert response["provider_id"] == GITHUB_COPILOT_PROVIDER_ID
    assert response["completed"] is True
    assert response["account_label"] == "github.com"


def test_poll_device_login_unknown_provider_returns_structured_error():
    response = asyncio.run(
        poll_device_login_api.PollDeviceLogin(None, None).process(
            {"provider_id": "missing", "attempt_id": "attempt-1"},
            FakeRequest(),
        )
    )

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert "Unknown OAuth provider" in response["error"]


@pytest.mark.parametrize(
    "provider_id",
    [CODEX_PROVIDER_ID, GITHUB_COPILOT_PROVIDER_ID, GEMINI_API_PROVIDER_ID, XAI_GROK_PROVIDER_ID],
)
@pytest.mark.parametrize("initial", [None, "None"])
def test_oauth_providers_leave_api_key_empty_until_connected(monkeypatch, provider_id, initial):
    monkeypatch.setattr(oauth_dummy_key, "oauth_provider_is_connected", lambda _provider_id: False)
    data = {"args": (provider_id,), "kwargs": {}, "result": initial}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == initial


@pytest.mark.parametrize(
    "provider_id",
    [CODEX_PROVIDER_ID, GITHUB_COPILOT_PROVIDER_ID, GEMINI_API_PROVIDER_ID, XAI_GROK_PROVIDER_ID],
)
@pytest.mark.parametrize("initial", [None, "None"])
def test_oauth_providers_report_dummy_api_key_when_connected(monkeypatch, provider_id, initial):
    monkeypatch.setattr(oauth_dummy_key, "oauth_provider_is_connected", lambda _provider_id: True)
    data = {"args": (provider_id,), "kwargs": {}, "result": initial}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == DUMMY_API_KEY


@pytest.mark.parametrize(
    "provider_id",
    [CODEX_PROVIDER_ID, GITHUB_COPILOT_PROVIDER_ID, GEMINI_API_PROVIDER_ID, XAI_GROK_PROVIDER_ID],
)
def test_oauth_providers_leave_missing_result_unset_when_disconnected(monkeypatch, provider_id):
    monkeypatch.setattr(oauth_dummy_key, "oauth_provider_is_connected", lambda _provider_id: False)
    data = {"args": (provider_id,), "kwargs": {}}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert "result" not in data


@pytest.mark.parametrize(
    "provider_id",
    [CODEX_PROVIDER_ID, GITHUB_COPILOT_PROVIDER_ID, GEMINI_API_PROVIDER_ID, XAI_GROK_PROVIDER_ID],
)
def test_oauth_providers_preserve_configured_api_key(provider_id):
    data = {"args": (provider_id,), "kwargs": {}, "result": "configured"}

    oauth_dummy_key.OAuthAccountDummyKey(agent=None).execute(data=data)

    assert data["result"] == "configured"


def test_model_provider_config_contains_all_oauth_providers():
    provider_path = Path(__file__).resolve().parents[1] / "plugins/_oauth/conf/model_providers.yaml"
    provider_config = yaml.safe_load(provider_path.read_text(encoding="utf-8"))
    chat = provider_config["chat"]

    assert set(chat) == {
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    }
    assert "api_key" not in chat[CODEX_PROVIDER_ID]["kwargs"]
    assert "api_key" not in chat[GITHUB_COPILOT_PROVIDER_ID]["kwargs"]
    assert "api_key" not in chat[GEMINI_API_PROVIDER_ID]["kwargs"]
    assert "api_key" not in chat[XAI_GROK_PROVIDER_ID]["kwargs"]
    assert chat[CODEX_PROVIDER_ID]["kwargs"]["api_base"] == "http://127.0.0.1/oauth/codex/v1"
    assert (
        chat[GITHUB_COPILOT_PROVIDER_ID]["kwargs"]["api_base"]
        == "http://127.0.0.1/oauth/github-copilot/v1"
    )
    assert chat[GEMINI_API_PROVIDER_ID]["kwargs"]["api_base"] == "http://127.0.0.1/oauth/gemini-api/v1"
    assert chat[XAI_GROK_PROVIDER_ID]["kwargs"]["api_base"] == "http://127.0.0.1/oauth/xai-grok/v1"
    assert "50001" not in json.dumps(provider_config)


def test_oauth_provider_config_marks_oauth_providers_as_oauth_api_key_mode():
    provider_path = Path(__file__).resolve().parents[1] / "plugins/_oauth/conf/model_providers.yaml"
    provider_config = yaml.safe_load(provider_path.read_text(encoding="utf-8"))
    chat = provider_config["chat"]

    assert chat[CODEX_PROVIDER_ID]["api_key_mode"] == "oauth"
    assert chat[GITHUB_COPILOT_PROVIDER_ID]["api_key_mode"] == "oauth"
    assert chat[GEMINI_API_PROVIDER_ID]["api_key_mode"] == "oauth"
    assert chat[XAI_GROK_PROVIDER_ID]["api_key_mode"] == "oauth"


def test_model_config_provider_metadata_stays_oauth_provider_agnostic():
    metadata_path = Path(__file__).resolve().parents[1] / "plugins/_model_config/provider_metadata.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))

    assert CODEX_PROVIDER_ID not in metadata["chat"]
    assert GITHUB_COPILOT_PROVIDER_ID not in metadata["chat"]
    assert GEMINI_API_PROVIDER_ID not in metadata["chat"]
    assert XAI_GROK_PROVIDER_ID not in metadata["chat"]


def test_usage_plan_catalog_covers_connectable_subscription_providers_only():
    catalog = usage_plan_catalog()

    assert set(catalog) == {
        CODEX_PROVIDER_ID,
        GITHUB_COPILOT_PROVIDER_ID,
        GEMINI_API_PROVIDER_ID,
        XAI_GROK_PROVIDER_ID,
    }

    assert {plan["id"] for plan in catalog[CODEX_PROVIDER_ID]["plans"]} >= {
        "free",
        "go",
        "plus",
        "pro",
        "business",
        "enterprise_edu",
        "api_key",
    }
    assert {plan["id"] for plan in catalog[GITHUB_COPILOT_PROVIDER_ID]["plans"]} >= {
        "free",
        "student",
        "pro",
        "pro_plus",
        "max",
        "business",
        "enterprise",
    }
    assert {plan["id"] for plan in catalog[GEMINI_API_PROVIDER_ID]["plans"]} >= {
        "oauth_cloud_project",
        "api_key",
        "vertex_ai",
    }
    assert catalog[GEMINI_API_PROVIDER_ID]["implemented"] is True
    assert {plan["id"] for plan in catalog[XAI_GROK_PROVIDER_ID]["plans"]} >= {
        "free",
        "supergrok_lite",
        "supergrok",
        "supergrok_heavy",
        "business",
        "enterprise",
        "api_credits",
    }


def test_disconnect_api_returns_provider_result_contract(monkeypatch):
    class FakeProvider:
        def __init__(self, provider_id: str):
            self.provider_id = provider_id

        def disconnect(self):
            return {"disconnected": True, "removed_auth_files": ["auth.json"]}

        def status(self):
            return {"provider_id": self.provider_id, "connected": False}

    provider = FakeProvider(GITHUB_COPILOT_PROVIDER_ID)
    monkeypatch.setattr(disconnect_api, "get_provider", lambda provider_id: provider)

    response = asyncio.run(
        disconnect_api.Disconnect(None, None).process(
            {"provider_id": GITHUB_COPILOT_PROVIDER_ID},
            FakeRequest(),
        )
    )

    assert response["ok"] is True
    assert response["provider_id"] == GITHUB_COPILOT_PROVIDER_ID
    assert response["result"] == {"disconnected": True, "removed_auth_files": ["auth.json"]}
    assert response["provider"] == {"provider_id": GITHUB_COPILOT_PROVIDER_ID, "connected": False}
    assert response["disconnected"] is True
    assert response["removed_auth_files"] == ["auth.json"]


def test_disconnect_api_keeps_codex_legacy_field(monkeypatch):
    class FakeProvider:
        provider_id = CODEX_PROVIDER_ID

        def disconnect(self):
            return {"disconnected": True}

        def status(self):
            return {"provider_id": CODEX_PROVIDER_ID, "connected": False}

    provider = FakeProvider()
    monkeypatch.setattr(disconnect_api, "get_provider", lambda provider_id: provider)

    response = asyncio.run(disconnect_api.Disconnect(None, None).process({}, FakeRequest()))

    assert response["result"] == {"disconnected": True}
    assert response["provider"] == {"provider_id": CODEX_PROVIDER_ID, "connected": False}
    assert response["codex"] == response["provider"]


def test_start_login_unknown_provider_returns_structured_error():
    response = asyncio.run(
        start_login_api.StartLogin(None, None).process({"provider_id": "missing"}, FakeRequest())
    )

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert "Unknown OAuth provider" in response["error"]


@pytest.mark.parametrize("provider_id", [0, False])
@pytest.mark.parametrize(
    "handler",
    [
        start_login_api.StartLogin,
        Models,
        disconnect_api.Disconnect,
        manual_callback_api.ManualCallback,
    ],
)
def test_provider_aware_apis_do_not_default_falsey_non_string_provider_ids(handler, provider_id):
    response = asyncio.run(handler(None, None).process({"provider_id": provider_id}, FakeRequest()))

    assert response["ok"] is False
    assert response["provider_id"] == str(provider_id)
    assert f"Unknown OAuth provider: {provider_id}" in response["error"]


def test_disconnect_unknown_provider_returns_structured_error():
    response = asyncio.run(
        disconnect_api.Disconnect(None, None).process({"provider_id": "missing"}, FakeRequest())
    )

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert "Unknown OAuth provider" in response["error"]


def test_manual_callback_unknown_provider_returns_structured_error():
    response = asyncio.run(
        manual_callback_api.ManualCallback(None, None).process({"provider_id": "missing"}, FakeRequest())
    )

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert "Unknown OAuth provider" in response["error"]


def test_models_api_returns_optional_model_metadata(monkeypatch):
    class FakeProvider:
        provider_id = CODEX_PROVIDER_ID

        def model_catalog(self):
            return [
                {
                    "slug": "gpt-5.5",
                    "display_name": "GPT-5.5",
                    "description": "Frontier coding model.",
                }
            ]

        def models(self):
            return ["ignored-when-catalog-exists"]

    models_module = sys.modules["plugins._oauth.api.models"]
    monkeypatch.setattr(models_module, "get_provider", lambda provider_id: FakeProvider())

    response = asyncio.run(Models(None, None).process({"provider_id": CODEX_PROVIDER_ID}, FakeRequest()))

    assert response["ok"] is True
    assert response["models"] == ["gpt-5.5"]
    assert response["model_metadata"] == [
        {
            "slug": "gpt-5.5",
            "display_name": "GPT-5.5",
            "description": "Frontier coding model.",
        }
    ]


def test_unknown_provider_id_on_provider_aware_api_returns_structured_error():
    response = asyncio.run(Models(None, None).process({"provider_id": "missing"}, FakeRequest()))

    assert response["ok"] is False
    assert response["provider_id"] == "missing"
    assert response["models"] == []
    assert "Unknown OAuth provider" in response["error"]


def test_register_oauth_routes_adds_codex_routes_and_provider_routes(monkeypatch):
    fake_flask = types.ModuleType("flask")

    class Response:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fake_flask.Response = Response
    fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
    fake_flask.request = types.SimpleNamespace()
    fake_flask.stream_with_context = lambda value: value

    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_config = types.ModuleType("plugins._oauth.helpers.config")
    fake_config.codex_config = lambda: {
        "proxy_base_path": "/oauth/codex",
        "callback_path": "/auth/callback",
    }

    monkeypatch.setitem(sys.modules, "flask", fake_flask)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.config", fake_config)

    module_name = "plugins._oauth.helpers.routes"
    previous_routes_module = sys.modules.pop(module_name, None)
    try:
        routes_module = importlib.import_module(module_name)

        class FakeApp:
            def __init__(self):
                self.view_functions = {}
                self.rules = []

            def add_url_rule(self, rule, endpoint, view_func, methods):
                self.view_functions[endpoint] = view_func
                self.rules.append((rule, endpoint, methods))

        registered_providers = []

        class FakeProvider:
            provider_id = "fake_provider"

            def register_routes(self, app):
                registered_providers.append(app)

        fake_provider = FakeProvider()
        monkeypatch.setattr(routes_module, "provider_registry", lambda: {"fake_provider": fake_provider})

        app = FakeApp()
        routes_module.register_oauth_routes(app)
        routes_module.register_oauth_routes(app)

        assert "oauth_codex_health" in app.view_functions
        assert app.rules.count(("/oauth/codex/health", "oauth_codex_health", ["GET"])) == 1
        assert registered_providers == [app, app]
    finally:
        sys.modules.pop(module_name, None)
        if previous_routes_module is not None:
            sys.modules[module_name] = previous_routes_module


def test_github_copilot_streaming_proxy_streams_successful_upstream(monkeypatch):
    fake_flask = types.ModuleType("flask")

    class Response:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fake_request = types.SimpleNamespace(
        method="POST",
        host="localhost",
        remote_addr="127.0.0.1",
        headers={},
        args={},
        get_json=lambda silent=True: {"stream": True, "model": "gpt-5.2"},
    )
    fake_flask.Response = Response
    fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
    fake_flask.request = fake_request
    fake_flask.stream_with_context = lambda value: value

    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_codex.response_headers = lambda upstream: dict(upstream.headers)
    fake_config = types.ModuleType("plugins._oauth.helpers.config")
    fake_config.codex_config = lambda: {
        "proxy_base_path": "/oauth/codex",
        "callback_path": "/auth/callback",
        "proxy_token": "",
        "require_proxy_token": False,
    }

    class FakeUpstream:
        ok = True
        status_code = 200
        headers = {}
        content = b"not-streamed"

        def iter_content(self, chunk_size):
            yield b"data: {}\n\n"

    fake_requests = types.ModuleType("requests")
    fake_requests.post = lambda *args, **kwargs: FakeUpstream()

    monkeypatch.setitem(sys.modules, "flask", fake_flask)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.config", fake_config)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    module_name = "plugins._oauth.helpers.routes"
    previous_routes_module = sys.modules.pop(module_name, None)
    try:
        routes_module = importlib.import_module(module_name)

        class FakeProvider:
            def ensure_fresh_auth(self):
                return {
                    "access": "fresh-access-token",
                    "base_url": "https://api.individual.githubcopilot.com",
                }

            def read_auth(self):
                return self.ensure_fresh_auth()

        monkeypatch.setattr(routes_module, "get_provider", lambda provider_id: FakeProvider())

        response = routes_module.github_copilot_responses()

        assert isinstance(response, Response)
        assert response.kwargs["headers"]["Content-Type"] == "text/event-stream"
        assert response.kwargs["status"] == 200
        assert response.args[0] != b"not-streamed"
    finally:
        sys.modules.pop(module_name, None)
        if previous_routes_module is not None:
            sys.modules[module_name] = previous_routes_module


def test_github_copilot_proxy_does_not_send_bearer_token_to_malicious_base_url(monkeypatch):
    fake_flask = types.ModuleType("flask")

    class Response:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fake_flask.Response = Response
    fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
    fake_flask.request = types.SimpleNamespace(
        method="POST",
        host="localhost",
        remote_addr="127.0.0.1",
        headers={},
        args={},
        get_json=lambda silent=True: {"stream": False, "model": "gpt-5.2"},
    )
    fake_flask.stream_with_context = lambda value: value

    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_codex.response_headers = lambda upstream: dict(upstream.headers)
    fake_config = types.ModuleType("plugins._oauth.helpers.config")
    fake_config.codex_config = lambda: {
        "proxy_base_path": "/oauth/codex",
        "callback_path": "/auth/callback",
        "proxy_token": "",
        "require_proxy_token": False,
    }

    calls = []

    class FakeUpstream:
        ok = True
        status_code = 200
        headers = {"Content-Type": "application/json"}
        content = b'{"ok":true}'

    fake_requests = types.ModuleType("requests")

    def fake_post(url, headers, json, stream, timeout):
        calls.append((url, headers, json, stream, timeout))
        return FakeUpstream()

    fake_requests.post = fake_post

    monkeypatch.setitem(sys.modules, "flask", fake_flask)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.config", fake_config)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    module_name = "plugins._oauth.helpers.routes"
    previous_routes_module = sys.modules.pop(module_name, None)
    try:
        routes_module = importlib.import_module(module_name)

        class FakeProvider:
            def ensure_fresh_auth(self):
                return {
                    "access": "fresh-access-token",
                    "base_url": "https://evil.example.com/v1",
                }

            def read_auth(self):
                return self.ensure_fresh_auth()

        monkeypatch.setattr(routes_module, "get_provider", lambda provider_id: FakeProvider())

        response = routes_module.github_copilot_responses()

        assert isinstance(response, Response)
        assert calls[0][0] == "https://api.individual.githubcopilot.com/responses"
        assert calls[0][1]["Authorization"] == "Bearer fresh-access-token"
    finally:
        sys.modules.pop(module_name, None)
        if previous_routes_module is not None:
            sys.modules[module_name] = previous_routes_module


def test_proxy_authorization_does_not_trust_host_header(monkeypatch):
    fake_flask = types.ModuleType("flask")
    fake_flask.Response = object
    fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
    fake_flask.request = types.SimpleNamespace(
        host="localhost",
        remote_addr="203.0.113.10",
        headers={},
        args={},
    )
    fake_flask.stream_with_context = lambda value: value

    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_config = types.ModuleType("plugins._oauth.helpers.config")
    fake_config.codex_config = lambda: {
        "proxy_base_path": "/oauth/codex",
        "callback_path": "/auth/callback",
        "proxy_token": "",
        "require_proxy_token": False,
    }

    monkeypatch.setitem(sys.modules, "flask", fake_flask)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.config", fake_config)

    module_name = "plugins._oauth.helpers.routes"
    previous_routes_module = sys.modules.pop(module_name, None)
    try:
        routes_module = importlib.import_module(module_name)

        assert routes_module._proxy_authorized() is False
    finally:
        sys.modules.pop(module_name, None)
        if previous_routes_module is not None:
            sys.modules[module_name] = previous_routes_module


def test_xai_proxy_does_not_send_bearer_token_to_malicious_base_url(monkeypatch):
    fake_flask = types.ModuleType("flask")

    class Response:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fake_flask.Response = Response
    fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
    fake_flask.request = types.SimpleNamespace(
        method="POST",
        host="localhost",
        remote_addr="127.0.0.1",
        headers={},
        args={},
        get_json=lambda silent=True: {"stream": False, "model": "grok-4.3"},
    )
    fake_flask.stream_with_context = lambda value: value

    fake_codex = types.ModuleType("plugins._oauth.helpers.codex")
    fake_codex.response_headers = lambda upstream: dict(upstream.headers)
    fake_config = types.ModuleType("plugins._oauth.helpers.config")
    fake_config.codex_config = lambda: {
        "proxy_base_path": "/oauth/codex",
        "callback_path": "/auth/callback",
        "proxy_token": "",
        "require_proxy_token": False,
    }

    calls = []

    class FakeUpstream:
        ok = True
        status_code = 200
        headers = {"Content-Type": "application/json"}
        content = b'{"ok":true}'

    fake_requests = types.ModuleType("requests")

    def fake_post(url, headers, json, stream, timeout):
        calls.append((url, headers, json, stream, timeout))
        return FakeUpstream()

    fake_requests.post = fake_post

    monkeypatch.setitem(sys.modules, "flask", fake_flask)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.codex", fake_codex)
    monkeypatch.setitem(sys.modules, "plugins._oauth.helpers.config", fake_config)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    module_name = "plugins._oauth.helpers.routes"
    previous_routes_module = sys.modules.pop(module_name, None)
    try:
        routes_module = importlib.import_module(module_name)

        class FakeProvider:
            def ensure_fresh_auth(self):
                return {
                    "access": "access-token",
                    "refresh": "refresh-token",
                    "base_url": "https://evil.example/v1",
                }

        monkeypatch.setattr(routes_module, "get_provider", lambda provider_id: FakeProvider())

        response = routes_module.xai_grok_responses()

        assert isinstance(response, Response)
        assert calls[0][0] == "https://api.x.ai/v1/responses"
        assert calls[0][1]["Authorization"] == "Bearer access-token"
    finally:
        sys.modules.pop(module_name, None)
        if previous_routes_module is not None:
            sys.modules[module_name] = previous_routes_module
