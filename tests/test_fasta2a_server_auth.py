import importlib.util
import sys
import threading
import types
from pathlib import Path
from urllib.parse import parse_qs

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "helpers" / "fasta2a_server.py"


class _StubHeaders(dict):
    def get(self, key, default=None):
        return super().get(str(key).lower(), default)


class _StubRequest:
    def __init__(self, scope, receive=None):
        raw_headers = scope.get("headers", []) or []
        self.headers = _StubHeaders(
            {
                key.decode("latin-1").lower(): value.decode("latin-1")
                for key, value in raw_headers
            }
        )
        raw_query = (scope.get("query_string") or b"").decode("latin-1")
        self.query_params = {
            key: values[-1]
            for key, values in parse_qs(raw_query, keep_blank_values=True).items()
        }


class _StubPrintStyle:
    def __init__(self, *args, **kwargs):
        pass

    def print(self, *args, **kwargs):
        return None


class _StubAgentContext:
    _contexts = {}

    def __init__(self, *args, **kwargs):
        self.id = "ctx-id"
        self.data = {}
        self.log = types.SimpleNamespace(log=lambda **kwargs: None)

    def reset(self):
        return None

    def communicate(self, *_args, **_kwargs):
        async def _result():
            return "ok"

        return types.SimpleNamespace(result=_result)

    @staticmethod
    def remove(_context_id):
        return None


class _StubUserMessage:
    def __init__(self, message="", attachments=None, **kwargs):
        self.message = message
        self.attachments = attachments or []


class _StubAgentContextType:
    BACKGROUND = "background"


async def _empty_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def _collecting_send(messages, message):
    messages.append(message)


def _load_target_module(monkeypatch, settings_payload):
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    helpers_pkg = types.ModuleType("helpers")
    settings_mod = types.ModuleType("helpers.settings")
    settings_mod.get_settings = lambda: settings_payload
    projects_mod = types.ModuleType("helpers.projects")
    print_style_mod = types.ModuleType("helpers.print_style")
    print_style_mod.PrintStyle = _StubPrintStyle
    persist_chat_mod = types.ModuleType("helpers.persist_chat")
    persist_chat_mod.remove_chat = lambda *_args, **_kwargs: None

    helpers_pkg.settings = settings_mod
    helpers_pkg.projects = projects_mod

    monkeypatch.setitem(sys.modules, "helpers", helpers_pkg)
    monkeypatch.setitem(sys.modules, "helpers.settings", settings_mod)
    monkeypatch.setitem(sys.modules, "helpers.projects", projects_mod)
    monkeypatch.setitem(sys.modules, "helpers.print_style", print_style_mod)
    monkeypatch.setitem(sys.modules, "helpers.persist_chat", persist_chat_mod)

    agent_mod = types.ModuleType("agent")
    agent_mod.AgentContext = _StubAgentContext
    agent_mod.UserMessage = _StubUserMessage
    agent_mod.AgentContextType = _StubAgentContextType
    monkeypatch.setitem(sys.modules, "agent", agent_mod)

    initialize_mod = types.ModuleType("initialize")
    initialize_mod.initialize_agent = lambda: object()
    monkeypatch.setitem(sys.modules, "initialize", initialize_mod)

    starlette_pkg = types.ModuleType("starlette")
    requests_mod = types.ModuleType("starlette.requests")
    requests_mod.Request = _StubRequest
    monkeypatch.setitem(sys.modules, "starlette", starlette_pkg)
    monkeypatch.setitem(sys.modules, "starlette.requests", requests_mod)

    module_name = "test_fasta2a_server_auth_target"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    module.FASTA2A_AVAILABLE = True
    return module


def _build_proxy(module, app):
    proxy = object.__new__(module.DynamicA2AProxy)
    proxy.app = app
    proxy.token = ""
    proxy._lock = threading.Lock()
    proxy._startup_done = True
    proxy._worker_bg_task = None
    proxy._reconfigure_needed = False
    return proxy


@pytest.mark.asyncio
async def test_token_path_auth_uses_compare_digest(monkeypatch):
    module = _load_target_module(
        monkeypatch,
        {"a2a_server_enabled": True, "mcp_server_token": "secret"},
    )

    compare_calls = []

    def _fake_compare(left, right):
        compare_calls.append((left, right))
        return True

    monkeypatch.setattr(module.hmac, "compare_digest", _fake_compare)

    delegated_scopes = []
    sent_messages = []

    async def _app(scope, receive, send):
        delegated_scopes.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"OK"})

    proxy = _build_proxy(module, _app)
    scope = {
        "type": "http",
        "path": "/t-secret/.well-known/agent.json",
        "headers": [],
        "query_string": b"",
    }

    await proxy(scope, _empty_receive, lambda message: _collecting_send(sent_messages, message))

    assert compare_calls == [(b"secret", b"secret")]
    assert len(delegated_scopes) == 1
    assert delegated_scopes[0]["path"] == "/.well-known/agent.json"
    assert sent_messages[0]["status"] == 200


@pytest.mark.asyncio
async def test_token_path_auth_rejects_mismatch(monkeypatch):
    module = _load_target_module(
        monkeypatch,
        {"a2a_server_enabled": True, "mcp_server_token": "secret"},
    )

    monkeypatch.setattr(module.hmac, "compare_digest", lambda left, right: False)

    delegated_scopes = []
    sent_messages = []

    async def _app(scope, receive, send):
        delegated_scopes.append(scope)

    proxy = _build_proxy(module, _app)
    scope = {
        "type": "http",
        "path": "/t-wrong/.well-known/agent.json",
        "headers": [],
        "query_string": b"",
    }

    await proxy(scope, _empty_receive, lambda message: _collecting_send(sent_messages, message))

    assert delegated_scopes == []
    assert sent_messages[0]["status"] == 401
    assert sent_messages[1]["body"] == b"Unauthorized"


@pytest.mark.asyncio
async def test_bearer_auth_uses_compare_digest(monkeypatch):
    module = _load_target_module(
        monkeypatch,
        {"a2a_server_enabled": True, "mcp_server_token": "secret"},
    )

    compare_calls = []

    def _fake_compare(left, right):
        compare_calls.append((left, right))
        return True

    monkeypatch.setattr(module.hmac, "compare_digest", _fake_compare)

    delegated_scopes = []
    sent_messages = []

    async def _app(scope, receive, send):
        delegated_scopes.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"OK"})

    proxy = _build_proxy(module, _app)
    scope = {
        "type": "http",
        "path": "/.well-known/agent.json",
        "headers": [(b"authorization", b"Bearer secret")],
        "query_string": b"",
    }

    await proxy(scope, _empty_receive, lambda message: _collecting_send(sent_messages, message))

    assert compare_calls == [(b"secret", b"secret")]
    assert len(delegated_scopes) == 1
    assert sent_messages[0]["status"] == 200


@pytest.mark.asyncio
async def test_api_key_query_auth_uses_compare_digest(monkeypatch):
    module = _load_target_module(
        monkeypatch,
        {"a2a_server_enabled": True, "mcp_server_token": "secret"},
    )

    compare_calls = []

    def _fake_compare(left, right):
        compare_calls.append((left, right))
        return True

    monkeypatch.setattr(module.hmac, "compare_digest", _fake_compare)

    delegated_scopes = []
    sent_messages = []

    async def _app(scope, receive, send):
        delegated_scopes.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"OK"})

    proxy = _build_proxy(module, _app)
    scope = {
        "type": "http",
        "path": "/.well-known/agent.json",
        "headers": [],
        "query_string": b"api_key=secret",
    }

    await proxy(scope, _empty_receive, lambda message: _collecting_send(sent_messages, message))

    assert compare_calls == [(b"secret", b"secret")]
    assert len(delegated_scopes) == 1
    assert sent_messages[0]["status"] == 200
