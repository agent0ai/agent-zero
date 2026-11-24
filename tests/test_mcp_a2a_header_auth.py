"""Header-based auth and project routing for the MCP and A2A servers.

The URL form (/t-<token>/, /p-<project>/) keeps working; clients may instead send
"Authorization: Bearer <token>" and "X-A0-Project: <project>".
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOKEN = "Tok3n-For-Tests1"
LOGS: list[str] = []


# ---------------------------------------------------------------------------
# Stubs for the Agent Zero modules the servers import
# ---------------------------------------------------------------------------


def _stub(monkeypatch, name, module):
    """Install a stub submodule of helpers, also as the package attribute that
    "from helpers import x" reads first when helpers is already imported."""
    monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(sys.modules["helpers"], name.split(".", 1)[1], module, raising=False)


def _install_stubs(monkeypatch):
    LOGS.clear()
    importlib.import_module("helpers")

    settings_stub = types.ModuleType("helpers.settings")
    settings_stub.get_settings = lambda: {
        "mcp_server_enabled": True,
        "a2a_server_enabled": True,
        "mcp_server_token": TOKEN,
    }
    _stub(monkeypatch, "helpers.settings", settings_stub)

    projects_stub = types.ModuleType("helpers.projects")
    projects_stub.CONTEXT_DATA_KEY_PROJECT = "project"
    projects_stub.activated = []

    def validate_project_name(name):
        candidate = str(name or "").strip()
        if not candidate or candidate in {".", ".."} or os.path.basename(candidate) != candidate:
            raise ValueError("Invalid project name")
        return candidate

    projects_stub.validate_project_name = validate_project_name
    projects_stub.activate_project = lambda context_id, name, **kw: projects_stub.activated.append(
        (context_id, name)
    )
    _stub(monkeypatch, "helpers.projects", projects_stub)

    print_style_stub = types.ModuleType("helpers.print_style")

    class _PrintStyle:
        def __init__(self, *args, **kwargs):
            pass

        def print(self, *args, **kwargs):
            LOGS.append(" ".join(str(a) for a in args))

        @staticmethod
        def error(*args, **kwargs):
            LOGS.append(" ".join(str(a) for a in args))

    print_style_stub.PrintStyle = _PrintStyle
    _stub(monkeypatch, "helpers.print_style", print_style_stub)

    class _Context:
        contexts: dict = {}

        def __init__(self, config=None, type=None):
            self.id = f"ctx-{len(_Context.contexts) + 1}"
            self.data = {}
            _Context.contexts[self.id] = self

        @classmethod
        def get(cls, context_id):
            return cls.contexts.get(context_id)

        @classmethod
        def remove(cls, context_id):
            cls.contexts.pop(context_id, None)

        def get_data(self, key):
            return self.data.get(key)

        def reset(self):
            pass

    agent_stub = types.ModuleType("agent")
    agent_stub.AgentContext = _Context
    agent_stub.UserMessage = lambda **kwargs: types.SimpleNamespace(**kwargs)
    agent_stub.AgentContextType = types.SimpleNamespace(BACKGROUND="background")
    monkeypatch.setitem(sys.modules, "agent", agent_stub)

    initialize_stub = types.ModuleType("initialize")
    initialize_stub.initialize_agent = lambda: {}
    monkeypatch.setitem(sys.modules, "initialize", initialize_stub)

    persist_chat_stub = types.ModuleType("helpers.persist_chat")
    persist_chat_stub.remove_chat = lambda *args, **kwargs: None
    _stub(monkeypatch, "helpers.persist_chat", persist_chat_stub)

    # Fresh server modules bound to these stubs; monkeypatch restores the
    # originals (module and package attribute) afterwards.
    package = sys.modules["helpers"]
    for name in ("helpers.server_auth", "helpers.mcp_server", "helpers.fasta2a_server"):
        monkeypatch.delitem(sys.modules, name, raising=False)
        attr = name.split(".", 1)[1]
        monkeypatch.setattr(package, attr, None, raising=False)
        delattr(package, attr)
    # Import both, so the package attributes dropped above exist again when
    # monkeypatch restores them.
    importlib.import_module("helpers.mcp_server")
    importlib.import_module("helpers.fasta2a_server")
    return projects_stub, _Context


@pytest.fixture
def mcp(monkeypatch):
    projects_stub, context_cls = _install_stubs(monkeypatch)
    module = importlib.import_module("helpers.mcp_server")
    module.DynamicMcpProxy._instance = None
    return types.SimpleNamespace(
        module=module, projects=projects_stub, context=context_cls
    )


@pytest.fixture
def a2a(monkeypatch):
    projects_stub, _ = _install_stubs(monkeypatch)
    module = importlib.import_module("helpers.fasta2a_server")
    return types.SimpleNamespace(module=module, projects=projects_stub)


# ---------------------------------------------------------------------------
# Minimal ASGI client
# ---------------------------------------------------------------------------


def _scope(method, path, headers=(), query=b"", root_path=""):
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "path": path,
        "raw_path": path.encode(),
        "root_path": root_path,
        "query_string": query,
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers],
    }


async def _request(app, method, path, headers=(), body=b"", query=b""):
    sent = []
    done = False

    async def receive():
        nonlocal done
        if not done:
            done = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        sent.append(message)

    await app(_scope(method, path, headers, query), receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], payload


async def _open_sse(app, path, headers=()):
    """Open an SSE stream; return (status, first chunk, task) and keep it open."""
    first = asyncio.get_running_loop().create_future()
    disconnect = asyncio.Event()
    status = {}

    async def receive():
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            status["code"] = message["status"]
        elif message["type"] == "http.response.body" and not first.done():
            first.set_result(message.get("body", b""))

    task = asyncio.create_task(
        app(_scope("GET", path, headers + (("accept", "text/event-stream"),)), receive, send)
    )
    done, _ = await asyncio.wait({first, task}, timeout=5, return_when=asyncio.FIRST_COMPLETED)
    chunk = first.result() if first.done() else b""
    return status.get("code"), chunk.decode(), task, disconnect


async def _close(task, disconnect):
    disconnect.set()
    task.cancel()
    with contextlib.suppress(BaseException):
        await task


def _mcp_app(module):
    from starlette.applications import Starlette
    from starlette.routing import Mount

    return Starlette(routes=[Mount("/mcp", app=module.DynamicMcpProxy.get_instance())])


def _endpoint(chunk: str) -> str:
    for line in chunk.splitlines():
        if line.startswith("data:"):
            return line[len("data:"):].strip()
    raise AssertionError(f"no endpoint event in {chunk!r}")


BEARER = (("authorization", f"Bearer {TOKEN}"),)


# ---------------------------------------------------------------------------
# MCP
# ---------------------------------------------------------------------------


def test_mcp_sse_url_token_announces_url_token_endpoint(mcp):
    async def run():
        app = _mcp_app(mcp.module)
        status, chunk, task, disc = await _open_sse(app, f"/mcp/t-{TOKEN}/sse")
        try:
            assert status == 200
            endpoint = _endpoint(chunk)
            assert endpoint.startswith(f"/mcp/t-{TOKEN}/messages/?session_id=")
            # the announced endpoint works with the URL token alone
            code, _ = await _request(app, "POST", endpoint.split("?")[0], body=b"{}",
                                     query=endpoint.split("?")[1].encode())
            assert code in (202, 400)  # accepted by the transport (400 = invalid JSON-RPC)
        finally:
            await _close(task, disc)

    asyncio.run(run())


def test_mcp_sse_header_auth_announces_token_free_endpoint(mcp):
    async def run():
        app = _mcp_app(mcp.module)
        status, chunk, task, disc = await _open_sse(app, "/mcp/sse", BEARER)
        try:
            assert status == 200
            endpoint = _endpoint(chunk)
            assert endpoint.startswith("/mcp/messages/?session_id=")
            assert TOKEN not in endpoint
            path, query = endpoint.split("?")
            ping = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode()
            code, _ = await _request(app, "POST", path, BEARER + (("content-type", "application/json"),),
                                     body=ping, query=query.encode())
            assert code == 202
            # the token-free messages endpoint without the header is refused
            code, _ = await _request(app, "POST", path, (("content-type", "application/json"),),
                                     body=ping, query=query.encode())
            assert code == 403
        finally:
            await _close(task, disc)

    asyncio.run(run())


@pytest.mark.parametrize(
    "path,headers",
    [
        ("/mcp/sse", ()),
        ("/mcp/sse", (("authorization", "Bearer wrong-token"),)),
        ("/mcp/sse", (("authorization", f"Basic {TOKEN}"),)),
        ("/mcp/sse", (("authorization", "Bearer "),)),
        ("/mcp/t-wrong-token/sse", ()),
        ("/mcp/t-wrong-token/sse", BEARER),  # a URL token must itself be valid
        ("/mcp/http/", ()),
        ("/mcp/messages/", ()),
        ("/mcp/other", BEARER),
    ],
)
def test_mcp_rejects_missing_or_wrong_token(mcp, path, headers):
    status, _ = asyncio.run(_request(_mcp_app(mcp.module), "GET", path, headers))
    assert status == 403


def test_mcp_streamable_http_header_and_url_token(mcp):
    init = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "1"}},
    }).encode()
    common = (("content-type", "application/json"), ("accept", "application/json, text/event-stream"))

    async def run():
        import anyio

        app = _mcp_app(mcp.module)
        # Run the session manager's task group in this task, as a server's lifespan would
        proxy = mcp.module.DynamicMcpProxy.get_instance()
        task_group = anyio.create_task_group()
        await task_group.__aenter__()
        proxy.http_session_task_group = task_group
        proxy.http_session_manager._task_group = task_group
        try:
            header_status, header_body = await _request(app, "POST", "/mcp/http/", BEARER + common, init)
            url_status, _ = await _request(app, "POST", f"/mcp/t-{TOKEN}/http/", common, init)
            none_status, _ = await _request(app, "POST", "/mcp/http/", common, init)
        finally:
            task_group.cancel_scope.cancel()
            await task_group.__aexit__(None, None, None)
        return header_status, header_body, url_status, none_status

    header_status, header_body, url_status, none_status = asyncio.run(run())
    assert header_status == 200 and b'"serverInfo"' in header_body
    assert url_status == 200
    assert none_status == 403


def _capture_proxy(module):
    """Proxy with recording apps: returns (proxy, calls)."""
    calls = []

    async def recorder(scope, receive, send):
        calls.append({"path": scope["path"], "root_path": scope["root_path"],
                      "project": module._mcp_project_name.get()})

    proxy = module.DynamicMcpProxy.get_instance()
    proxy.sse_app = recorder
    proxy.http_app = recorder
    return proxy, calls


def test_mcp_project_from_header_or_url(mcp):
    proxy, calls = _capture_proxy(mcp.module)

    async def call(path, headers=()):
        await proxy(_scope("GET", path, headers, root_path="/mcp"), None, None)

    asyncio.run(call("/mcp/sse", BEARER + (("x-a0-project", "alpha"),)))
    asyncio.run(call(f"/mcp/t-{TOKEN}/p-beta/sse"))
    asyncio.run(call(f"/mcp/t-{TOKEN}/p-gamma/http/", (("x-a0-project", "gamma"),)))
    asyncio.run(call("/mcp/p-delta/messages/", BEARER))

    assert calls == [
        {"path": "/mcp/sse", "root_path": "/mcp", "project": "alpha"},
        {"path": f"/mcp/t-{TOKEN}/sse", "root_path": f"/mcp/t-{TOKEN}", "project": "beta"},
        {"path": f"/mcp/t-{TOKEN}/http/", "root_path": f"/mcp/t-{TOKEN}", "project": "gamma"},
        {"path": "/mcp/messages/", "root_path": "/mcp", "project": "delta"},
    ]


@pytest.mark.parametrize(
    "path,headers",
    [
        (f"/mcp/t-{TOKEN}/p-alpha/sse", (("x-a0-project", "beta"),)),
        ("/mcp/p-alpha/sse", BEARER + (("x-a0-project", "beta"),)),
        ("/mcp/sse", BEARER + (("x-a0-project", ".."),)),
        ("/mcp/sse", BEARER + (("x-a0-project", "a/b"),)),
    ],
)
def test_mcp_conflicting_or_invalid_project_is_rejected(mcp, path, headers):
    from starlette.exceptions import HTTPException

    proxy, calls = _capture_proxy(mcp.module)
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(proxy(_scope("GET", path, headers, root_path="/mcp"), None, None))
    assert excinfo.value.status_code == 400
    assert "X-A0-Project" in excinfo.value.detail
    assert calls == []


def test_mcp_invalid_url_project_is_rejected(mcp):
    from starlette.exceptions import HTTPException

    proxy, calls = _capture_proxy(mcp.module)
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(proxy(_scope("GET", "/mcp/p-../sse", BEARER, root_path="/mcp"), None, None))
    assert excinfo.value.status_code == 400
    assert "URL" in excinfo.value.detail
    assert calls == []


def test_mcp_header_project_activates_and_guards_existing_chat(mcp):
    module = mcp.module

    async def fake_run_chat(context, message, attachments=None):
        return "ok"

    module._run_chat = fake_run_chat
    tool = getattr(module.send_message, "fn", module.send_message)

    async def run():
        module._mcp_project_name.set("alpha")
        new_chat = await tool(message="hi", persistent_chat=True)
        existing = mcp.context.get(new_chat.chat_id)
        existing.data["project"] = "alpha"
        module._mcp_project_name.set("beta")
        other = await tool(message="hi", chat_id=new_chat.chat_id)
        return new_chat, other

    new_chat, other = asyncio.run(run())
    assert new_chat.status == "success"
    assert mcp.projects.activated == [(new_chat.chat_id, "alpha")]
    assert other.status == "error" and "belongs to project 'alpha'" in other.error


def test_mcp_never_logs_token(mcp):
    async def run():
        app = _mcp_app(mcp.module)
        status, chunk, task, disc = await _open_sse(app, "/mcp/p-alpha/sse", BEARER)
        await _close(task, disc)
        await _request(app, "GET", "/mcp/sse", (("authorization", "Bearer wrong"),))

    asyncio.run(run())
    assert LOGS, "expected some log lines"
    assert not any(TOKEN in line for line in LOGS)


# ---------------------------------------------------------------------------
# A2A
# ---------------------------------------------------------------------------


def _a2a_proxy(module):
    calls = []

    async def app(scope, receive, send):
        message = await receive()
        calls.append({"path": scope["path"], "body": message.get("body", b"")})
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    proxy = object.__new__(module.DynamicA2AProxy)
    proxy.app = app
    proxy.token = TOKEN
    proxy._lock = __import__("threading").Lock()
    proxy._startup_done = True
    proxy._reconfigure_needed = False
    return proxy, calls


A2A_BODY = json.dumps({
    "jsonrpc": "2.0", "id": "1", "method": "message/send",
    "params": {"message": {"role": "user", "kind": "message", "message_id": "m1",
                           "parts": [{"kind": "text", "text": "hi"}]}},
}).encode()


def _project_of(body: bytes):
    return (json.loads(body)["params"]["message"].get("metadata") or {}).get("project")


@pytest.mark.skipif(
    importlib.util.find_spec("fasta2a") is None, reason="fasta2a not installed"
)
def test_a2a_header_and_url_auth_and_project(a2a):
    proxy, calls = _a2a_proxy(a2a.module)

    def call(path, headers=()):
        return asyncio.run(_request(proxy, "POST", path, headers, A2A_BODY))

    assert call(f"/a2a/t-{TOKEN}/")[0] == 200
    assert call("/a2a/", BEARER)[0] == 200
    assert call("/a2a/", BEARER + (("x-a0-project", "alpha"),))[0] == 200
    assert call(f"/a2a/t-{TOKEN}/p-beta/")[0] == 200
    assert call(f"/a2a/t-{TOKEN}/p-gamma/", (("x-a0-project", "gamma"),))[0] == 200

    assert [c["path"] for c in calls] == ["/", "/a2a/", "/a2a/", "/", "/"]
    assert [_project_of(c["body"]) for c in calls] == [None, None, "alpha", "beta", "gamma"]

    assert call("/a2a/")[0] == 401
    assert call("/a2a/", (("authorization", "Bearer wrong"),))[0] == 401
    assert call("/a2a/t-wrong/")[0] == 401

    status, body = call(f"/a2a/t-{TOKEN}/p-alpha/", (("x-a0-project", "beta"),))
    assert status == 400 and b"X-A0-Project" in body
    status, _ = call("/a2a/", BEARER + (("x-a0-project", ".."),))
    assert status == 400
    assert len(calls) == 5
    assert not any(TOKEN in line for line in LOGS)


async def _chunked_request(app, path, headers, chunks):
    """POST ``chunks`` as separate http.request events; return what the app read."""
    pending = [
        {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
        for i, chunk in enumerate(chunks)
    ]
    sent = []

    async def receive():
        if pending:
            return pending.pop(0)
        await asyncio.Event().wait()

    async def send(message):
        sent.append(message)

    await app(_scope("POST", path, headers), receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    return start["status"]


def _a2a_reading_proxy(module):
    """A2A proxy whose app reads every http.request event until more_body is false."""
    events = []

    async def app(scope, receive, send):
        while True:
            message = await receive()
            events.append(message)
            if message["type"] != "http.request" or not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    proxy, _ = _a2a_proxy(module)
    proxy.app = app
    return proxy, events


@pytest.mark.skipif(
    importlib.util.find_spec("fasta2a") is None, reason="fasta2a not installed"
)
@pytest.mark.parametrize(
    "path,headers",
    [
        ("/a2a/", BEARER + (("x-a0-project", "alpha"),)),
        (f"/a2a/t-{TOKEN}/p-alpha/", ()),
    ],
    ids=["header-project", "url-project"],
)
def test_a2a_chunked_body_is_rewritten_once(a2a, path, headers):
    """A body sent in several http.request events reaches the app exactly once,
    as one rewritten http.request event (no duplicated first chunk)."""
    proxy, events = _a2a_reading_proxy(a2a.module)
    chunks = [A2A_BODY[:10], A2A_BODY[10:40], A2A_BODY[40:]]

    assert asyncio.run(_chunked_request(proxy, path, headers, chunks)) == 200

    assert len(events) == 1
    assert events[0]["type"] == "http.request"
    assert events[0]["more_body"] is False
    data = json.loads(events[0]["body"])
    assert data["params"]["message"]["metadata"] == {"project": "alpha"}
    expected = json.loads(A2A_BODY)
    expected["params"]["message"]["metadata"] = {"project": "alpha"}
    assert data == expected


@pytest.mark.skipif(
    importlib.util.find_spec("fasta2a") is None, reason="fasta2a not installed"
)
def test_a2a_chunked_body_without_project_passes_through(a2a):
    """Without a project nothing is buffered: the app reads the chunks as sent."""
    proxy, events = _a2a_reading_proxy(a2a.module)
    chunks = [A2A_BODY[:10], A2A_BODY[10:]]

    assert asyncio.run(_chunked_request(proxy, "/a2a/", BEARER, chunks)) == 200

    assert [e["body"] for e in events] == chunks
    assert [e["more_body"] for e in events] == [True, False]
