from __future__ import annotations

import itertools
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from helpers import responses_tools, tool_policy
from helpers.errors import RepairableException
from helpers.tool_actions import BUNDLED_ACTIONS, action_policy_id, bundled_path
from plugins._agent_editor.helpers import editor
from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import EnforceToolPolicy


ROOT = Path(__file__).resolve().parents[1]
# The retired connector IDs still describe saved host permissions.
RETIRED_HOST_TOOLS = {
    "plugin:_a0_connector:text_editor_remote", "plugin:_a0_connector:code_execution_remote",
}
CALLABLE_ACTIONS = {tool_id: spec for tool_id, spec in BUNDLED_ACTIONS.items() if tool_id not in RETIRED_HOST_TOOLS}


@pytest.fixture
def action_agent(monkeypatch):
    from plugins._browser.helpers import config as browser_config
    monkeypatch.setattr(browser_config, "get_browser_config", lambda agent: {"runtime_backend": "container"})
    agent = SimpleNamespace(config=SimpleNamespace(profile="restricted"))
    paths = {tool_id.rsplit(":", 1)[-1]: ROOT / bundled_path(tool_id) for tool_id in CALLABLE_ACTIONS}
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda _agent, *parts, **kwargs: (
        [str(paths[Path(parts[-1]).stem])] if len(parts) == 2 and Path(parts[-1]).stem in paths else []
    ))
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    return agent


def policy(monkeypatch, *, default="allow", allowed=(), blocked=()):
    result = tool_policy.normalize_policy({
        "mode": "custom", "default": default, "allowed": list(allowed), "blocked": list(blocked),
    })
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: result)
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
async def test_each_action_has_the_same_permission_in_prompts_schemas_and_execution(
    monkeypatch, action_agent, tool_id, spec,
):
    name = tool_id.rsplit(":", 1)[-1]
    prompt = f"### {name}\nTool instructions."
    monkeypatch.setattr(responses_tools, "_local_tool_prompts", lambda _agent: [(name, prompt)])
    for allowed_action in spec.actions:
        policy(monkeypatch, default="block", allowed=[action_policy_id(tool_id, allowed_action)])
        assert tool_policy.resolve_tool(action_agent, name).allowed
        schemas, names = responses_tools.build_responses_function_tools(action_agent)
        assert names == {name: name}
        assert schemas[0]["parameters"]["properties"][spec.argument]["enum"] == [allowed_action]
        assert f"Permitted {name} actions for this agent: {allowed_action}." in schemas[0]["description"]
        for action in spec.actions:
            args = {spec.argument: f" {action.upper()} "}
            if action == allowed_action:
                await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args=args)
            else:
                with pytest.raises(RepairableException, match="is blocked"):
                    await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args=args)

    policy(monkeypatch, default="block")
    assert responses_tools.build_responses_function_tools(action_agent) == ([], {})
    assert tool_policy.filter_tool_prompt(action_agent, f"agent.system.tool.{name}.md", prompt) == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
async def test_whole_tool_block_still_wins_and_policy_changes_apply_immediately(
    monkeypatch, action_agent, tool_id, spec,
):
    name = tool_id.rsplit(":", 1)[-1]
    action = spec.actions[0]
    current = policy(monkeypatch, allowed=[action_policy_id(tool_id, action)])
    await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args={spec.argument: action})
    current["blocked"] = [tool_id]
    with pytest.raises(RepairableException):
        await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args={spec.argument: action})


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
async def test_aliases_cannot_bypass_action_blocks(monkeypatch, action_agent, tool_id, spec):
    name = tool_id.rsplit(":", 1)[-1]
    for alias, action in spec.aliases.items():
        policy(monkeypatch, blocked=[action_policy_id(tool_id, action)])
        with pytest.raises(RepairableException):
            await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args={spec.argument: alias})


@pytest.mark.asyncio
@pytest.mark.parametrize("name,args,blocked_action", [
    ("browser", {}, "state"),
    ("goal", {}, "get"),
    ("skills_tool", {}, "list"),
    ("skills_tool", {"action": "", "method": "load"}, "load"),
    ("browser", {"action": "multi", "calls": [{"action": "state"}, {"action": "evaluate", "script": "1"}]}, "evaluate"),
    ("browser", {"action": "multi", "calls": [{"action": "cdp", "cdp_method": "Browser.getVersion"}]}, "cdp"),
    ("browser", {"action": "multi", "calls": [{"action": "multi", "calls": [{"action": "focus"}]}]}, "set_active"),
    ("code_execution_tool", {"runtime": "terminal", "reset": "true"}, "reset"),
    ("parallel", {"action": "collect", "tool_calls": []}, "start"),
    ("parallel", {"action": "await", "calls": "[]"}, "start"),
    ("parallel", {"items": []}, "start"),
    ("parallel", {"action": "start", "wait": True, "tool_calls": []}, "await"),
    ("parallel", {"action": "start", "job_ids": ["job"]}, "collect"),
])
async def test_defaults_and_compound_requests_cannot_skip_a_denied_action(
    monkeypatch, action_agent, name, args, blocked_action,
):
    tool_id = next(tool_id for tool_id in CALLABLE_ACTIONS if tool_id.endswith(":" + name))
    policy(monkeypatch, blocked=[action_policy_id(tool_id, blocked_action)])
    with pytest.raises(RepairableException):
        await EnforceToolPolicy(action_agent).execute(tool_name=name, tool_args=args)


def test_browser_cdp_inherits_the_profile_default_with_other_browser_actions_blocked(monkeypatch, action_agent):
    policy(monkeypatch, blocked=["plugin:_browser:browser:evaluate"])
    assert "cdp" in tool_policy.allowed_tool_actions(action_agent, "browser")
    assert tool_policy.resolve_tool(action_agent, "browser", tool_args={"action": "cdp"}).allowed
    assert not tool_policy.resolve_tool(action_agent, "browser", action="evaluate").allowed


@pytest.mark.parametrize("backend,family,block_cdp,compact", [
    ("container", "", False, True), ("container", "", True, False),
    ("host_required", "", False, True), ("host_required", "chrome", False, True),
    ("host_required", "safari", False, False),
])
def test_browser_discovery_matches_text_and_native(monkeypatch, action_agent, backend, family, block_cdp, compact):
    from plugins._a0_connector.helpers import ws_runtime
    from plugins._browser.helpers import config as browser_config
    action_agent.context = SimpleNamespace(id="discovery")
    monkeypatch.setattr(browser_config, "get_browser_config", lambda agent: {"runtime_backend": backend})
    monkeypatch.setattr(ws_runtime, "select_host_browser_target_sid", lambda ctx: "sid" if family else None)
    monkeypatch.setattr(ws_runtime, "select_host_browser_candidate_sid", lambda ctx: None)
    monkeypatch.setattr(ws_runtime, "host_browser_metadata_for_sid", lambda sid: {"browser_family": family})
    current = policy(monkeypatch, blocked=["plugin:_browser:browser:cdp"] if block_cdp else [])
    if not block_cdp:
        current["mode"] = "inherit"
    prompt = (ROOT / "plugins/_browser/prompts/agent.system.tool.browser.md").read_text()
    monkeypatch.setattr(responses_tools, "_local_tool_prompts", lambda agent: [("browser", prompt)])
    text = tool_policy.filter_tool_prompt(action_agent, "agent.system.tool.browser.md", prompt)
    tools, _ = responses_tools.build_responses_function_tools(action_agent)
    schema = tools[0]["parameters"]["properties"]
    actions = schema["action"]["enum"]
    assert ", ".join(actions) + "." in text
    assert ("cdp" in actions) == compact
    assert ("cdp_method" in schema) == compact
    assert ("script" in schema) == ("evaluate" in actions)
    if compact:
        assert actions == ["open", "list", "content", "click", "type", "evaluate", "screenshot", "upload_file", "cdp"]
        assert "calls" not in schema
    else:
        assert {"keyboard", "wheel", "navigate", "multi"} <= set(actions)
        assert ("evaluate" in actions) == (family != "safari")


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["", ":write"], ids=["whole-tool", "write-action"])
async def test_host_editor_enforces_saved_permissions_before_dispatch(monkeypatch, action_agent, suffix):
    from plugins._a0_connector.helpers.host_text_editor import HostTextEditor
    from plugins._text_editor.tools.text_editor import TextEditor

    send = AsyncMock()
    monkeypatch.setattr(HostTextEditor, "execute", send)
    saved = policy(monkeypatch, default="block", allowed=["plugin:_text_editor:text_editor:write"])
    args = {"action": "write", "destination": "host", "path": "note.txt", "content": "test"}
    tool = TextEditor(action_agent, "text_editor", None, args, "", None)
    await EnforceToolPolicy(action_agent).execute(tool_name="text_editor", tool_args=args)
    await tool.execute(**args)
    saved["blocked"].append("plugin:_a0_connector:text_editor_remote" + suffix)
    with pytest.raises(RepairableException, match="blocks text_editor_remote"):
        await tool.execute(**args)
    send.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [False, "false", "maybe", None])
async def test_non_reset_code_call_does_not_require_reset_permission(monkeypatch, action_agent, value):
    policy(monkeypatch, blocked=["plugin:_code_execution:code_execution_tool:reset"])
    await EnforceToolPolicy(action_agent).execute(
        tool_name="code_execution_tool", tool_args={"runtime": "python", "reset": value},
    )


@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
def test_action_contract_is_not_applied_to_profile_override(monkeypatch, tmp_path, action_agent, tool_id, spec):
    name = tool_id.rsplit(":", 1)[-1]
    path = tmp_path / (name + ".py")
    path.write_text("")
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *_args, **_kwargs: [str(path)])
    policy(monkeypatch, blocked=[action_policy_id(tool_id, spec.actions[0])])
    assert tool_policy.get_tool_actions(action_agent, name) is None
    assert tool_policy.allowed_tool_actions(action_agent, name) is None
    assert tool_policy.resolve_tool(action_agent, name, tool_args={spec.argument: "custom_action"}).allowed


@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
def test_editor_projection_preserves_whole_tool_and_action_rule_precedence(
    monkeypatch, action_agent, tool_id, spec,
):
    name = tool_id.rsplit(":", 1)[-1]
    catalog = [{"id": tool_id, "name": name, "label": name, "available": True, "actions": list(spec.actions)}]
    monkeypatch.setattr(tool_policy, "get_tool_catalog", lambda _agent: catalog)
    for default, whole, first in itertools.product(("allow", "block"), ("default", "allowed", "blocked"), ("default", "allowed", "blocked")):
        raw = policy(monkeypatch, default=default)
        for key, rule_id in [(whole, tool_id), (first, action_policy_id(tool_id, spec.actions[0]))]:
            if key != "default":
                raw[key].append(rule_id)
        state = editor._editor_tool_state(action_agent, raw)
        assert tool_id not in {row["id"] for row in state["catalog"]}
        assert all(row["parent_tool"]["id"] == tool_id for row in state["catalog"])
        assert {row["action_label"] for row in state["catalog"]} == {
            action.replace("_", " ").title() for action in spec.actions
        }
        for action in spec.actions:
            kwargs = {"canonical_id": tool_id, "action": action}
            before = tool_policy.resolve_tool(action_agent, name, **kwargs, _policy=raw)
            after = tool_policy.resolve_tool(action_agent, name, **kwargs, _policy=state["policy"])
            assert before.allowed == after.allowed
            assert editor._valid_tool_id(action_policy_id(tool_id, action))


@pytest.mark.asyncio
async def test_parallel_worker_rechecks_the_nested_tool_action_before_execution(monkeypatch, action_agent):
    from helpers import parallel_tools

    policy(monkeypatch, blocked=["plugin:_text_editor:text_editor:write"])
    tool = SimpleNamespace(before_execution=AsyncMock(), execute=AsyncMock(), after_execution=AsyncMock())
    monkeypatch.setattr(parallel_tools, "_resolve_parallel_tool", lambda *_args, **_kwargs: tool)
    action_agent.handle_intervention = AsyncMock()
    action_agent.loop_data = SimpleNamespace(current_tool=None)

    async def extensions(point, agent, **kwargs):
        if point == "tool_execute_before":
            await EnforceToolPolicy(agent).execute(**kwargs)

    monkeypatch.setattr(parallel_tools, "call_extensions_async", extensions)
    with pytest.raises(RepairableException):
        await parallel_tools.execute_tool_call(action_agent, "text_editor", {"action": "write", "path": "/tmp/denied"})
    tool.execute.assert_not_awaited()
    assert action_agent.loop_data.current_tool is None


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked", ["list", "load"])
async def test_automatic_skill_catalog_respects_action_permissions(monkeypatch, action_agent, blocked):
    from extensions.python.system_prompt import _13_skills_prompt

    policy(monkeypatch, blocked=[f"local:skills_tool:{blocked}"])
    monkeypatch.setattr(_13_skills_prompt.skills_helper, "list_skills", lambda **_kwargs: pytest.fail("must not list skills"))
    assert await _13_skills_prompt.build_prompt(action_agent) == ""


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked", ["search", "load"])
async def test_automatic_skill_recall_respects_action_permissions(monkeypatch, action_agent, blocked):
    from agent import LoopData
    from extensions.python.message_loop_prompts_after import _63_recall_relevant_skills

    policy(monkeypatch, blocked=[f"local:skills_tool:{blocked}"])
    monkeypatch.setattr(_63_recall_relevant_skills.skills_helper, "search_skills", lambda *_args, **_kwargs: pytest.fail("must not search skills"))
    loop = LoopData(iteration=0)
    await _63_recall_relevant_skills.RecallRelevantSkills(action_agent).execute(loop_data=loop)
    assert "relevant_skills" not in loop.extras_temporary
