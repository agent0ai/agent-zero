from __future__ import annotations

import itertools
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from agent import Agent
from helpers import responses_tools, skills, tool_policy
from helpers.errors import RepairableException
from helpers.tool_actions import BUNDLED_ACTIONS, action_policy_id, bundled_path
from plugins._agent_editor.helpers import editor
from plugins._browser.helpers.browser_handler import Browser
from plugins._browser.helpers.skill_access import _LEGACY_ACTION_IDS
from plugins._document_query.helpers.query_handler import DocumentQueryTool
from tools.skills_tool import SkillsTool
from tools.unknown import Unknown
from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import EnforceToolPolicy


ROOT = Path(__file__).resolve().parents[1]
# The retired connector IDs still describe saved host permissions.
RETIRED_HOST_TOOLS = {
    "plugin:_a0_connector:text_editor_remote", "plugin:_a0_connector:code_execution_remote",
}
CALLABLE_ACTIONS = {tool_id: spec for tool_id, spec in BUNDLED_ACTIONS.items() if tool_id not in RETIRED_HOST_TOOLS}


@pytest.fixture
def action_agent(monkeypatch):
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


@pytest.fixture
def browser_agent(monkeypatch):
    state = {}
    agent = object.__new__(Agent)
    agent.config = SimpleNamespace(profile="restricted-browser")
    agent.context = SimpleNamespace(
        id="skill-browser", get_data=state.get, set_data=state.__setitem__,
    )
    agent.data = {}
    agent.loop_data = SimpleNamespace(current_tool=None)
    plugin = ROOT / "plugins/_browser"
    plugin_extensions = plugin / "extensions/python"
    paths = {
        ("skills",): [str(plugin / "skills")],
        ("extensions/python", "skill_tools"): [str(plugin / "extensions/python/skill_tools")],
        ("extensions/python", "_functions/agent/Agent/get_tool/end"): [
            str(ROOT / "extensions/python/_functions/agent/Agent/get_tool/end")
        ],
    }
    for point in ("get_skill_roots", "get_visibility_policy"):
        skill_extension = f"_functions/helpers/skills/{point}/end"
        paths[("extensions/python", skill_extension)] = [str(plugin_extensions / skill_extension)]
    skill_policy = skills.normalize_visibility_policy(None)
    get_config = skills.plugin_helpers.get_plugin_config
    monkeypatch.setattr(skills.plugin_helpers, "get_plugin_config", lambda name, *args, **kwargs: (
        {"visibility_policy": skill_policy}
        if name == skills.ACTIVE_SKILLS_PLUGIN_NAME else get_config(name, *args, **kwargs)
    ))
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda _agent, *parts, **_: paths.get(parts, []))
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda _agent: "")
    return agent, paths, skill_policy


@pytest.mark.asyncio
async def test_browser_skill_respects_saved_tool_access(monkeypatch, browser_agent):
    agent, paths, skill_policy = browser_agent
    [skill_root] = paths[("skills",)]
    tool_id = "plugin:_browser:browser"
    loader = SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)

    async def check(available):
        schemas, names = responses_tools.build_responses_function_tools(agent)
        tool = agent.get_tool("browser", None, {"action": "open"}, "", agent.loop_data)
        agent.loop_data.current_tool = tool
        if available:
            assert names == {"browser": "browser"}
            assert "cdp_method" in schemas[0]["parameters"]["properties"]
            assert isinstance(tool, Browser)
            await EnforceToolPolicy(agent).execute(tool_name="browser", tool_args=tool.args)
        else:
            assert (schemas, names) == ([], {})
            assert isinstance(tool, Unknown)
            with pytest.raises(RepairableException, match="is blocked"):
                await EnforceToolPolicy(agent).execute(tool_name="browser", tool_args=tool.args)

    policy(monkeypatch, default="block", allowed=[tool_id])
    assert tool_id not in BUNDLED_ACTIONS
    assert "browser" not in {item["name"] for item in tool_policy.get_tool_catalog(agent)}
    assert skills.find_skill("browser-automation", agent=agent)
    await check(False)
    assert '"tool_name":"browser"' in loader._load("browser-automation").message
    await check(True)

    policy(monkeypatch, default="block", allowed=_LEGACY_ACTION_IDS)
    await check(True)

    for saved_rules in (
        {"blocked": [tool_id]},
        {"allowed": [tool_id], "blocked": [action_policy_id(tool_id, "evaluate")]},
        {"default": "block", "allowed": [action_policy_id(tool_id, "open")]},
    ):
        policy(monkeypatch, **saved_rules)
        assert skill_root not in skills.get_skill_roots(agent)
        assert skill_root in skills.get_skill_roots()
        assert not skills.find_skill("browser-automation", agent=agent)
        await check(False)

    policy(monkeypatch)
    skill = skills.find_skill("browser-automation", agent=agent)
    policy(monkeypatch, blocked=[action_policy_id(tool_id, "cdp")])
    with monkeypatch.context() as override:
        override.setattr(skills, "find_skill", lambda *_args, **_kwargs: skill)
        await check(False)

    policy(monkeypatch)
    assert skills.find_skill("browser-automation", agent=agent)
    skill_policy.update(skills.normalize_visibility_policy({
        "mode": "custom",
        "blocked": ["browser-automation"],
    }))
    await check(False)


@pytest.mark.asyncio
async def test_browser_discovery_leaves_override_imports_to_dispatch(monkeypatch, tmp_path, browser_agent):
    agent, paths, _ = browser_agent
    override = tmp_path / "browser.py"
    override.write_text("raise ImportError('missing test dependency')\n")
    paths[("tools",)] = [str(tmp_path)]
    paths[("tools", "browser.py")] = [str(override)]
    load_classes = Mock(wraps=responses_tools.extract_tools.load_classes_from_file)
    monkeypatch.setattr(responses_tools.extract_tools, "load_classes_from_file", load_classes)
    policy(monkeypatch)
    SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)._load("browser-automation")
    assert responses_tools.build_responses_function_tools(agent) == ([], {})
    assert "local:browser" in {item["id"] for item in tool_policy.get_tool_catalog(agent)}
    load_classes.assert_not_called()

    agent.loop_data.current_tool = agent.get_tool("browser", None, {}, "", agent.loop_data)
    assert isinstance(agent.loop_data.current_tool, Browser)
    load_classes.assert_called_once()

    policy(monkeypatch, blocked=[action_policy_id("plugin:_browser:browser", "navigate")])
    with pytest.raises(RepairableException, match="is blocked"):
        await EnforceToolPolicy(agent).execute(tool_name="browser", tool_args={})

    override.unlink()
    policy(monkeypatch)
    schemas, names = responses_tools.build_responses_function_tools(agent)
    assert names == {"browser": "browser"}
    assert "cdp_method" in schemas[0]["parameters"]["properties"]
    load_classes.assert_called_once()


def test_browser_denial_hides_scoped_skill_overrides(monkeypatch, tmp_path, browser_agent):
    agent, paths, skill_policy = browser_agent
    paths[("skills",)].insert(0, str(tmp_path))
    override = tmp_path / "renamed-folder"
    for directory, name in ((override, "browser-automation"), (tmp_path / "unrelated", "unrelated")):
        directory.mkdir()
        (directory / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Scoped {name}\n---\nInstructions.\n")
    policy(monkeypatch)
    assert skills.find_skill("browser-automation", agent=agent).path == override
    skill_policy.update(mode="custom", allowed=["browser-automation"])
    policy(monkeypatch, blocked=["plugin:_browser:browser:evaluate"])
    assert {skill.name for skill in skills.list_skills(agent)} == {"unrelated"}
    assert skills.find_skill("browser-automation", agent=agent) is None
    catalog = {item["name"]: item for item in skills.list_skill_catalog(agent=agent)}
    assert catalog["browser-automation"]["hidden"]
    assert not catalog["unrelated"]["hidden"]
    with pytest.raises(ValueError, match="is blocked"):
        skills.activate_chat_skill(agent, {"name": "browser-automation", "path": str(override)})
    loader = SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)
    assert "skill not found" in loader._load("browser-automation").message


@pytest.mark.asyncio
async def test_document_query_skill_registers_callable_with_existing_tool_access(monkeypatch, tmp_path):
    plugin = ROOT / "plugins/_document_query"
    tool_id = "plugin:_document_query:document_query"
    state = {}
    agent = object.__new__(Agent)
    agent.config = SimpleNamespace(profile="document-query-binding")
    agent.data = {}
    agent.context = SimpleNamespace(
        id="document-query-binding", get_data=state.get, set_data=state.__setitem__,
    )
    agent.loop_data = SimpleNamespace(current_tool=None)
    skill_roots = [str(plugin / "skills")]

    def paths(_agent, *parts, **kwargs):
        return {
            ("skills",): skill_roots,
            ("extensions/python", "skill_tools"): [str(plugin / "extensions/python/skill_tools")],
            ("extensions/python", "_functions/agent/Agent/get_tool/end"): [
                str(ROOT / "extensions/python/_functions/agent/Agent/get_tool/end")
            ],
        }.get(parts, [])

    monkeypatch.setattr(tool_policy.subagents, "get_paths", paths)
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda _agent: "")
    skill_policy = skills.normalize_visibility_policy(None)
    monkeypatch.setattr(skills, "get_visibility_policy", lambda _agent: skill_policy)
    current = tool_policy.normalize_policy(None)
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: current)

    async def check(available, source, description=None):
        schemas, names = responses_tools.build_responses_function_tools(agent)
        assert ("document_query" in names) is available
        decision = tool_policy.resolve_tool(agent, "document_query")
        assert (decision.tool_id, decision.source) == (tool_id, source)
        assert tool_id in {item["id"] for item in tool_policy.get_tool_catalog(agent)}
        tool = agent.get_tool("document_query", None, {}, "", agent.loop_data)
        agent.loop_data.current_tool = tool
        if available:
            assert isinstance(tool, DocumentQueryTool)
            assert "destination" in schemas[0]["parameters"]["properties"]
            assert schemas[0]["parameters"]["required"] == ["document"]
            if description:
                assert schemas[0]["description"] == description
            await EnforceToolPolicy(agent).execute(tool_name="document_query")
        else:
            assert isinstance(tool, Unknown)
            with pytest.raises(RepairableException, match="is blocked"):
                await EnforceToolPolicy(agent).execute(tool_name="document_query")

    loader = SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)
    await check(False, "skill")
    shadow = tmp_path / "document-query"
    shadow.mkdir()
    override = shadow / "SKILL.md"
    override.write_text("---\nname: document-query\ndescription: Shadow skill\n---\nShadow instructions.\n")
    skill_roots.insert(0, str(tmp_path))
    assert "Shadow instructions" in loader._load("document-query").message
    await check(False, "skill")
    builtin = (plugin / "skills/document-query/SKILL.md").read_text()
    override.write_text(builtin.replace(
        next(line for line in builtin.splitlines() if line.startswith("description:")),
        "description: Overridden document query",
    ))
    await check(True, "inherited", "Overridden document query")
    skill_roots.pop(0)
    registered = tool_policy.skill_tools.registered

    def register_fresh_factory(for_agent):
        binding = registered(for_agent)["document_query"]
        return {"document_query": replace(binding, factory=lambda **kwargs: binding.factory(**kwargs))}

    with monkeypatch.context() as fresh:
        fresh.setattr(tool_policy.skill_tools, "registered", register_fresh_factory)
        await check(True, "inherited")
    current.update(mode="custom", default="block")
    await check(False, "scoped-default")
    current["allowed"] = ["local:document_query"]
    await check(False, "scoped-default")
    current["allowed"] = [tool_id]
    await check(True, "scoped-policy")

    with monkeypatch.context() as disabled:
        disabled.setattr(tool_policy.skill_tools, "registered", lambda _agent: {})
        with pytest.raises(RepairableException, match="is blocked"):
            await EnforceToolPolicy(agent).execute(tool_name="document_query")

    # A permission change also applies to a handler already resolved for execution.
    current["blocked"] = [tool_id]
    with pytest.raises(RepairableException, match="is blocked"):
        await EnforceToolPolicy(agent).execute(tool_name="document_query")
    await check(False, "scoped-policy")
    current["blocked"] = ["local:document_query"]
    await check(False, "scoped-policy")
    current["blocked"] = []
    skill_policy.update(skills.normalize_visibility_policy({
        "mode": "custom", "blocked": ["document-query"],
    }))
    await check(False, "skill")


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_id,spec", CALLABLE_ACTIONS.items())
async def test_each_action_has_the_same_permission_in_prompts_schemas_and_execution(
    monkeypatch, action_agent, tool_id, spec,
):
    name = tool_id.rsplit(":", 1)[-1]
    prompt = f"### {name}\nTool instructions."
    monkeypatch.setattr(responses_tools, "_local_tool_prompts", lambda _agent: [(name, prompt)])
    allowed_actions = Mock(wraps=tool_policy.allowed_tool_actions)
    monkeypatch.setattr(tool_policy, "allowed_tool_actions", allowed_actions)
    for allowed_action in spec.actions:
        current = policy(monkeypatch, default="block", allowed=[action_policy_id(tool_id, allowed_action)])
        assert tool_policy.resolve_tool(action_agent, name).allowed
        allowed_actions.reset_mock()
        schemas, names = responses_tools.build_responses_function_tools(action_agent)
        allowed_actions.assert_called_once_with(action_agent, name, _policy=current)
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
    ("goal", {}, "get"),
    ("skills_tool", {}, "list"),
    ("skills_tool", {"action": "", "method": "load"}, "load"),
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
