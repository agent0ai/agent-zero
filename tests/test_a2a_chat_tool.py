from types import SimpleNamespace
from threading import Lock

import httpx
import pytest

from plugins._a2a_chat.helpers.fasta2a_client import AgentConnection
from plugins._a2a_chat.tools.a2a_chat import A2AChatTool


class _FakeLog:
    def log(self, **kwargs) -> dict:
        return kwargs


class _FakeAgent:
    def __init__(self) -> None:
        self.context = SimpleNamespace(log=_FakeLog())


def _make_tool(args: dict) -> A2AChatTool:
    return A2AChatTool(
        agent=_FakeAgent(), name="a2a_chat", method="execute", args=args, message="chat", loop_data=None
    )


def test_log_object_titles_headline_with_agent_url():
    tool = _make_tool({"agent_url": "http://peer.example.com/a2a", "message": "hello"})

    entry = tool.get_log_object()

    assert entry["type"] == "a2a_chat"
    assert entry["heading"] == "icon://hub Chatting: http://peer.example.com/a2a"
    assert entry["kvps"]["agent_url"] == "http://peer.example.com/a2a"
    assert entry["kvps"]["message"] == "hello"


def test_get_heading_falls_back_without_host():
    tool = _make_tool({})

    assert tool.get_heading() == "icon://hub Chatting"


async def _agent_card_request(connection: AgentConnection) -> httpx.Request:
    requests = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"name": "test-agent"})

    connection._http_client._transport = httpx.MockTransport(handle_request)
    try:
        await connection.get_agent_card()
    finally:
        await connection.close()
    assert len(requests) == 1
    return requests[0]


@pytest.mark.asyncio
async def test_agent_connection_does_not_send_ambient_a2a_token(monkeypatch):
    monkeypatch.setenv("A2A_TOKEN", "synthetic-ambient-token")

    request = await _agent_card_request(AgentConnection("http://untrusted.invalid"))

    assert request.url.path == "/.well-known/agent.json"
    assert "Authorization" not in request.headers
    assert "X-API-KEY" not in request.headers


@pytest.mark.asyncio
async def test_agent_connection_sends_explicit_token(monkeypatch):
    monkeypatch.setenv("A2A_TOKEN", "synthetic-ambient-token")

    request = await _agent_card_request(
        AgentConnection("http://peer.invalid", token="explicit-peer-token")
    )

    assert request.headers["Authorization"] == "Bearer explicit-peer-token"
    assert request.headers["X-API-KEY"] == "explicit-peer-token"


@pytest.mark.asyncio
async def test_agent_zero_token_url_is_preserved_for_discovery_and_rpc():
    connection = AgentConnection("http://peer.invalid/a2a/t-peer-token")
    try:
        card_request = connection._http_client.build_request(
            "GET", f"{connection.agent_url}/.well-known/agent.json"
        )
        rpc_request = connection._a2a_client.http_client.build_request("POST", "/")
    finally:
        await connection.close()

    assert card_request.url.path == "/a2a/t-peer-token/.well-known/agent.json"
    assert rpc_request.url.path == "/a2a/t-peer-token/"
    assert "Authorization" not in rpc_request.headers
    assert "X-API-KEY" not in rpc_request.headers


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_mode", [
    "token-url", "explicit-header", "public-peer", "project-url",
])
async def test_vps_a2a_discovery_and_conversation_preserve_explicit_auth(monkeypatch, auth_mode):
    from helpers import fasta2a_server, settings
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    monkeypatch.setenv("A2A_TOKEN", "unrelated-ambient-secret")
    monkeypatch.setattr(settings, "get_settings", lambda: {
        "a2a_server_enabled": True, "mcp_server_token": "" if auth_mode == "public-peer" else "peer-token",
    })
    messages, headers = [], []

    async def card(request):
        headers.append(request.headers)
        return JSONResponse({"name": "VPS peer"})

    async def send_message(request):
        headers.append(request.headers)
        body = await request.json()
        messages.append(body["params"]["message"])
        return JSONResponse({"jsonrpc": "2.0", "id": body["id"], "result": {
            "kind": "task", "id": "test-task", "contextId": "test-conversation",
            "status": {"state": "completed"},
        }})

    peer = fasta2a_server.DynamicA2AProxy.__new__(fasta2a_server.DynamicA2AProxy)
    peer.app = Starlette(routes=[Route("/.well-known/agent.json", card), Route("/", send_message, methods=["POST"])])
    peer._lock = Lock()
    peer._startup_done = True
    peer._reconfigure_needed = False
    url = "https://peer.example.invalid"
    if auth_mode in {"token-url", "project-url"}:
        url += "/a2a/t-peer-token"
    if auth_mode == "project-url":
        url += "/p-existing-project"
    connection = AgentConnection(url, token="peer-token" if auth_mode == "explicit-header" else None)
    connection._http_client._transport = httpx.ASGITransport(app=peer)
    try:
        assert (await connection.get_agent_card())["name"] == "VPS peer"
        first = await connection.send_message("Hello")
        second = await connection.send_message("Follow up")
        assert first["result"]["status"]["state"] == second["result"]["status"]["state"] == "completed"
        assert messages[1]["contextId"] == "test-conversation"
        if auth_mode == "project-url":
            assert all(message["metadata"]["project"] == "existing-project" for message in messages)
        assert len(headers) == 3
        for request_headers in headers:
            assert request_headers.get("Authorization") == ("Bearer peer-token" if auth_mode == "explicit-header" else None)
            assert request_headers.get("X-API-KEY") == ("peer-token" if auth_mode == "explicit-header" else None)
    finally:
        await connection.close()
