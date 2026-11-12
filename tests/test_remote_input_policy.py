import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import responses_tools, tool_policy
from helpers.errors import RepairableException
from plugins._a0_connector.extensions.python._functions._11_tools_prompt.build_prompt.end._70_include_remote_tool_stubs import IncludeRemoteToolStubs
from plugins._a0_connector.helpers import ws_runtime
from plugins._a0_connector.tools import code_execution_remote
from plugins._a0_connector.tools.input_remote import InputRemote
from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import EnforceToolPolicy


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins/_a0_connector"
INPUT_ID = "plugin:_a0_connector:input_remote"
EXEC_ID = "plugin:_a0_connector:code_execution_remote"


class RecordingManager:
    def __init__(self):
        self.calls = []

    async def emit_to(self, namespace, sid, event, payload, **kwargs):
        self.calls.append((event, payload))
        assert namespace == "/ws" and event == "connector_exec_op"
        assert ws_runtime.resolve_pending_exec_op(
            payload["op_id"], sid=sid,
            payload={"ok": True, "result": {"output": "input sent"}},
        )


@pytest.fixture
def remote_input(monkeypatch):
    context_id, sid = f"ctx-{uuid.uuid4()}", f"sid-{uuid.uuid4()}"
    agent = SimpleNamespace(
        config=SimpleNamespace(profile="restricted-input"),
        context=SimpleNamespace(id=context_id, get_data=lambda *args, **kwargs: None),
        get_data=lambda key: None,
        read_prompt=lambda name, **kwargs: (PLUGIN_ROOT / "prompts" / name).read_text(),
    )
    policy = tool_policy.normalize_policy({
        "mode": "custom", "default": "block", "allowed": [INPUT_ID, EXEC_ID],
    })
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: policy)
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda _agent, *parts, **kwargs: [str(PLUGIN_ROOT.joinpath(*parts))])
    monkeypatch.setattr(code_execution_remote, "build_exec_config", lambda **kwargs: {})
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda _agent: "")
    manager = RecordingManager()
    monkeypatch.setattr(code_execution_remote, "get_shared_ws_manager", lambda: manager)
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
    ws_runtime.store_sid_remote_file_metadata(sid, {"enabled": True, "write_enabled": True})
    tool = InputRemote(agent=agent, name="input_remote", method=None,
                       args={"session": 3}, message="", loop_data=None)
    try:
        yield SimpleNamespace(agent=agent, policy=policy, manager=manager, sid=sid, tool=tool)
    finally:
        ws_runtime.unregister_sid(sid)


@pytest.mark.asyncio
@pytest.mark.parametrize("custom", [False, True])
async def test_default_remote_input_needs_no_editor_grants(remote_input, custom):
    state = remote_input
    state.policy.update(tool_policy.normalize_policy(
        tool_policy.plugins.get_default_plugin_config(tool_policy.PLUGIN_NAME)
    ))
    if custom:
        state.policy["mode"] = "custom"
    assert state.policy["allowed"] == state.policy["blocked"] == []
    assert tool_policy.resolve_tool(state.agent, "input_remote").allowed
    assert tool_policy.resolve_tool(state.agent, "code_execution_remote", action="terminal").allowed

    prompts = [(path.name, path.read_text()) for path in (PLUGIN_ROOT / "prompts").glob("agent.system.tool.*.md")]
    data = {"result": "\n".join(tool_policy.filter_tool_prompts(state.agent, prompts))}
    IncludeRemoteToolStubs(agent=state.agent).execute(data=data)
    assert '"tool_name": "input_remote"' in data["result"]
    tools, _ = responses_tools.build_responses_function_tools(state.agent)
    assert "input_remote" in {tool["name"] for tool in tools}

    await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": "yes"})
    assert (await state.tool.execute(keyboard="yes")).message == "input sent"
    assert len(state.manager.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit", [False, True])
async def test_remote_input_cannot_dispatch_without_execution_permission(remote_input, explicit):
    state = remote_input
    state.policy.update(allowed=[INPUT_ID], blocked=[EXEC_ID] if explicit else [])
    assert not tool_policy.resolve_tool(state.agent, "code_execution_remote").allowed

    with pytest.raises(RepairableException, match='"code_execution_remote" is blocked'):
        await state.tool.execute(keyboard="printf policy-bypass")

    assert state.manager.calls == []
    assert state.tool.args == {"session": 3}


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked_id", [INPUT_ID, EXEC_ID])
async def test_remote_input_execution_hook_requires_both_permissions(remote_input, blocked_id):
    state = remote_input
    state.policy["blocked"] = [blocked_id]
    with pytest.raises(RepairableException, match='"input_remote" is blocked'):
        await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": "yes"})
    assert state.manager.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit", [False, True])
async def test_remote_input_requires_terminal_permission(remote_input, explicit):
    state = remote_input
    state.policy.update(allowed=[INPUT_ID, f"{EXEC_ID}:output"],
                        blocked=[f"{EXEC_ID}:terminal"] if explicit else [])
    assert tool_policy.resolve_tool(state.agent, "code_execution_remote").allowed
    with pytest.raises(RepairableException):
        await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": "yes"})
    with pytest.raises(RepairableException):
        await state.tool.execute(keyboard="printf policy-bypass")
    assert state.manager.calls == []


@pytest.mark.parametrize("grant", ["blocked", "missing", "output_only"])
def test_remote_input_is_hidden_from_text_and_native_tools_when_execution_is_blocked(remote_input, grant):
    state = remote_input
    state.policy.update(allowed=[INPUT_ID], blocked=[EXEC_ID] if grant == "blocked" else [])
    if grant == "output_only":
        state.policy["allowed"].append(f"{EXEC_ID}:output")
    prompts = [(path.name, path.read_text()) for path in (PLUGIN_ROOT / "prompts").glob("agent.system.tool.*.md")]
    data = {"result": "\n".join(tool_policy.filter_tool_prompts(state.agent, prompts))}
    IncludeRemoteToolStubs(agent=state.agent).execute(data=data)
    assert '"tool_name": "input_remote"' not in data["result"]
    tools, _ = responses_tools.build_responses_function_tools(state.agent)
    assert "input_remote" not in {tool["name"] for tool in tools}


@pytest.mark.asyncio
async def test_remote_input_checks_the_bundled_execution_capability_even_when_shadowed(remote_input, monkeypatch, tmp_path):
    state = remote_input
    state.policy.update(default="allow", blocked=[EXEC_ID])
    shadow = tmp_path / "code_execution_remote.py"
    shadow.write_text("")
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda _agent, *parts, **kwargs:
                        [str(shadow if parts == ("tools", "code_execution_remote.py") else PLUGIN_ROOT.joinpath(*parts))])
    assert tool_policy.resolve_tool(state.agent, "code_execution_remote").allowed
    assert not tool_policy.resolve_tool(state.agent, "input_remote").allowed
    with pytest.raises(RepairableException, match='"code_execution_remote" is blocked'):
        await state.tool.execute(keyboard="printf policy-bypass")
    assert state.manager.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["custom", "inherit"])
@pytest.mark.parametrize("keyboard", ["yes  \n", ""])
async def test_authorized_remote_input_preserves_terminal_transport(remote_input, mode, keyboard):
    state = remote_input
    state.policy["mode"] = mode
    await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": keyboard})
    result = await state.tool.execute(keyboard=keyboard, code="ignored", runtime="python", reset=True)
    assert result.message == "input sent"
    [(event, payload)] = state.manager.calls
    assert event == "connector_exec_op"
    assert (payload["runtime"], payload["code"], payload["session"], payload["allow_running"]) == ("terminal", keyboard.rstrip(), 3, True)
    assert "reset" not in payload


@pytest.mark.asyncio
async def test_terminal_permission_does_not_grant_input_permission(remote_input):
    state = remote_input
    state.policy["allowed"] = [f"{EXEC_ID}:terminal"]
    with pytest.raises(RepairableException):
        await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": "yes"})
    assert state.manager.calls == []
    state.policy["allowed"].append(INPUT_ID)
    await EnforceToolPolicy(agent=state.agent).execute(tool_name="input_remote", tool_args={"keyboard": "yes"})
    assert (await state.tool.execute(keyboard="yes")).message == "input sent"


@pytest.mark.asyncio
@pytest.mark.parametrize("gate", ["disconnected", "disabled", "read_only"])
async def test_remote_input_still_requires_host_grants(remote_input, gate):
    state = remote_input
    if gate == "disconnected":
        ws_runtime.unregister_sid(state.sid)
    elif gate == "disabled":
        ws_runtime.store_sid_remote_exec_metadata(state.sid, {"enabled": False})
    else:
        ws_runtime.store_sid_remote_file_metadata(state.sid, {"enabled": True, "write_enabled": False})
    result = await state.tool.execute(keyboard="yes")
    assert state.manager.calls == []
    assert {"disconnected": "no CLI client", "disabled": "press F4", "read_only": "Press F3"}[gate] in result.message


@pytest.mark.asyncio
async def test_remote_execution_ignores_model_supplied_allow_running(remote_input):
    state = remote_input
    tool = code_execution_remote.CodeExecutionRemote(
        agent=state.agent, name="code_execution_remote", method=None,
        args={"runtime": "terminal", "code": "printf allowed", "allow_running": True},
        message="", loop_data=None,
    )
    await tool.execute()
    assert "allow_running" not in state.manager.calls[0][1]
