from pathlib import Path
from types import SimpleNamespace
from threading import Lock

import httpx
import pytest

from plugins._a2a_chat.helpers.fasta2a_client import AgentConnection
from plugins._a2a_chat.helpers.chat_handler import A2AChatTool


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


@pytest.mark.asyncio
async def test_a2a_skill_load_preserves_current_and_legacy_tool_access(monkeypatch):
    from agent import Agent
    from helpers import responses_tools, skills, subagents, tool_policy
    from helpers.errors import RepairableException
    from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import EnforceToolPolicy
    from tools.skills_tool import SkillsTool
    from tools.unknown import Unknown

    root = Path(__file__).resolve().parents[1]
    plugin = root / "plugins/_a2a_chat"
    assert not (plugin / "tools/a2a_chat.py").exists()
    assert not (plugin / "prompts/agent.system.tool.a2a_chat.md").exists()
    paths = {
        ("skills",): [str(plugin / "skills")],
        ("extensions/python", "skill_tools"): [str(plugin / "extensions/python/skill_tools")],
        ("extensions/python", "_functions/agent/Agent/get_tool/end"): [
            str(root / "extensions/python/_functions/agent/Agent/get_tool/end")
        ],
    }
    monkeypatch.setattr(subagents, "get_paths", lambda _agent, *parts, **kwargs: paths.get(parts, []))
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda _agent: "")
    monkeypatch.setattr(skills, "get_hidden_skills", lambda _agent: [])
    monkeypatch.setattr(skills, "get_visibility_policy", lambda _agent: skills.normalize_visibility_policy(None))

    saved = tool_policy.normalize_policy({"mode": "custom", "default": "block"})
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: saved)
    state = {}
    agent = object.__new__(Agent)
    agent.context = SimpleNamespace(id="a2a-skill-test", get_data=state.get, set_data=state.__setitem__)
    agent.config = SimpleNamespace(profile="a2a-skill-test")
    agent.loop_data = SimpleNamespace(current_tool=None)
    agent.data = {}
    tool_id = "plugin:_a2a_chat:a2a_chat"
    legacy_id = "local:a2a_chat"
    args = {"agent_url": "https://peer.invalid/a2a", "message": "Hello"}
    saved["allowed"] = [legacy_id]

    def select():
        tool = agent.get_tool("a2a_chat", None, args, "", agent.loop_data)
        agent.loop_data.current_tool = tool
        return tool

    assert tool_id in {item["id"] for item in tool_policy.get_tool_catalog(agent)}
    assert responses_tools.build_responses_function_tools(agent) == ([], {})
    assert isinstance(select(), Unknown)
    loader = SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)
    assert '"tool_name": "a2a_chat"' in loader._load("a2a-chat").message

    for allowed_id, denied_id in ((tool_id, legacy_id), (legacy_id, tool_id)):
        saved.update(allowed=[allowed_id], blocked=[])
        [declaration], names = responses_tools.build_responses_function_tools(agent)
        assert names == {"a2a_chat": "a2a_chat"}
        assert declaration["parameters"]["required"] == ["agent_url", "message"]
        assert isinstance(select(), A2AChatTool)
        await EnforceToolPolicy(agent).execute(tool_name="a2a_chat", tool_args=args)

        saved["blocked"] = [denied_id]
        assert responses_tools.build_responses_function_tools(agent) == ([], {})
        assert isinstance(select(), Unknown)
        with pytest.raises(RepairableException, match="is blocked"):
            await EnforceToolPolicy(agent).execute(tool_name="a2a_chat", tool_args=args)


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
    "token-url", "explicit-header", "public-peer",
    pytest.param("project-url", marks=pytest.mark.xfail(
        strict=True, reason="Pre-existing project router duplicates chunked request bodies",
    )),
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
