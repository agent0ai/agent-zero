from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from extensions.python.system_prompt import _11_tools_prompt, _13_skills_prompt
from helpers import files, mcp_handler, responses_tools, tool_policy
from helpers.errors import RepairableException
from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import (
    EnforceToolPolicy,
)


class _Context:
    def get_data(self, key: str, recursive: bool = True):
        return None


class _Agent:
    def __init__(self, prompt_root: Path, profile: str = "researcher") -> None:
        self.prompt_root = prompt_root
        self.config = SimpleNamespace(profile=profile)
        self.context = _Context()
        self.data: dict = {}

    def read_prompt(self, basename: str, **kwargs) -> str:
        content = (self.prompt_root / basename).read_text(encoding="utf-8")
        for key, value in kwargs.items():
            content = content.replace("{{" + key + "}}", str(value))
        return content

    def get_data(self, key: str):
        return self.data.get(key)


class _NoMCPTools:
    def get_tools(self):
        return []


def _write_prompt(root: Path, basename: str, content: str) -> None:
    (root / basename).write_text(content.strip() + "\n", encoding="utf-8")


def _prompt_paths(root: Path):
    def get_paths(agent, *parts, **kwargs):
        return [str(root)] if parts and parts[0] == "prompts" else []

    return get_paths


def _custom_policy(*, default: str, mcp_default: str = "allow", allowed=(), blocked=()):
    return {
        "mode": "custom",
        "default": default,
        "mcp_default": mcp_default,
        "allowed": list(allowed),
        "blocked": list(blocked),
    }


def test_agent_import_does_not_cycle_through_tool_policy() -> None:
    subprocess.run(
        [sys.executable, "-c", "import agent"],
        cwd=Path(__file__).parents[1],
        check=True,
    )


@pytest.fixture
def local_prompt_agent(monkeypatch, tmp_path: Path) -> _Agent:
    _write_prompt(tmp_path, "agent.system.tools.md", "TOOLS\n{{tools}}")
    _write_prompt(
        tmp_path,
        "agent.system.tool.allowed.md",
        """### allowed
Allowed description
Keyboard input remains documented.
Do not call the `blocked` tool from here.
{"tool_name":"allowed","tool_args":{}}""",
    )
    _write_prompt(
        tmp_path,
        "agent.system.tool.blocked.md",
        '### blocked\nBlocked description\n{"tool_name":"blocked","tool_args":{}}',
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", _prompt_paths(tmp_path))
    monkeypatch.setattr(
        "plugins._model_config.helpers.model_config.get_chat_model_config",
        lambda agent: {"vision": False},
    )
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda agent: [])
    return _Agent(tmp_path)


@pytest.mark.asyncio
async def test_text_tool_prompt_omits_blocked_tool_and_description(
    monkeypatch, local_prompt_agent: _Agent
) -> None:
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(default="allow", blocked=["local:blocked"]),
    )

    prompt = await _11_tools_prompt.build_prompt(local_prompt_agent)

    assert "Allowed description" in prompt
    assert "Keyboard input remains documented." in prompt
    assert "Do not call" not in prompt
    assert "blocked" not in prompt.lower()
    assert "Blocked description" not in prompt


@pytest.mark.asyncio
async def test_policy_is_loaded_once_per_tool_surface(
    monkeypatch, local_prompt_agent: _Agent
) -> None:
    reads = 0

    def get_policy(_agent):
        nonlocal reads
        reads += 1
        return _custom_policy(default="allow", blocked=["local:blocked"])

    monkeypatch.setattr(tool_policy, "get_policy", get_policy)

    await _11_tools_prompt.build_prompt(local_prompt_agent)
    assert reads == 1

    await _11_tools_prompt.build_prompt(local_prompt_agent)
    assert reads == 2

    responses_tools.build_responses_function_tools(local_prompt_agent)
    assert reads == 3


def test_provider_native_schemas_omit_blocked_local_tool(
    monkeypatch, local_prompt_agent: _Agent
) -> None:
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(default="allow", blocked=["local:blocked"]),
    )

    tools, _name_map = responses_tools.build_responses_function_tools(
        local_prompt_agent
    )

    assert [tool["name"] for tool in tools] == ["allowed"]


@pytest.mark.asyncio
async def test_profile_policy_isolated_across_prompt_schema_and_execution(
    monkeypatch, local_prompt_agent: _Agent
) -> None:
    restricted = _Agent(local_prompt_agent.prompt_root, profile="restricted")

    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow",
            blocked=(
                ["local:allowed"]
                if agent.config.profile == "restricted"
                else []
            ),
        ),
    )

    allowed_prompt = await _11_tools_prompt.build_prompt(local_prompt_agent)
    restricted_prompt = await _11_tools_prompt.build_prompt(restricted)
    allowed_tools, _ = responses_tools.build_responses_function_tools(
        local_prompt_agent
    )
    restricted_tools, _ = responses_tools.build_responses_function_tools(restricted)

    assert "Allowed description" in allowed_prompt
    assert "Allowed description" not in restricted_prompt
    assert "allowed" in {tool["name"] for tool in allowed_tools}
    assert "allowed" not in {tool["name"] for tool in restricted_tools}
    await EnforceToolPolicy(local_prompt_agent).execute(tool_name="allowed")
    with pytest.raises(
        RepairableException,
        match='Tool "allowed" is blocked for agent profile "restricted"',
    ):
        await EnforceToolPolicy(restricted).execute(tool_name="allowed")


@pytest.mark.asyncio
async def test_execution_rechecks_policy_after_tool_was_advertised(
    monkeypatch, local_prompt_agent: _Agent
) -> None:
    disabled = False

    def get_policy(_agent):
        return _custom_policy(default="block" if disabled else "allow")

    monkeypatch.setattr(tool_policy, "get_policy", get_policy)

    prompt = await _11_tools_prompt.build_prompt(local_prompt_agent)
    tools, _ = responses_tools.build_responses_function_tools(local_prompt_agent)
    assert "Allowed description" in prompt
    assert "allowed" in {tool["name"] for tool in tools}

    disabled = True
    with pytest.raises(RepairableException, match='Tool "allowed" is blocked'):
        await EnforceToolPolicy(local_prompt_agent).execute(tool_name="allowed")


def test_inherited_prompt_filter_skips_tool_inventory(monkeypatch, tmp_path: Path):
    agent = _Agent(tmp_path)
    prompt = "### shell\nRun a command."
    policy_reads = 0

    def inherited_policy(_agent):
        nonlocal policy_reads
        policy_reads += 1
        return {
            "mode": "inherit",
            "default": "allow",
            "mcp_default": "allow",
            "allowed": [],
            "blocked": [],
        }

    monkeypatch.setattr(tool_policy, "get_policy", inherited_policy)
    monkeypatch.setattr(
        tool_policy,
        "_policy_tool_names",
        lambda _agent: pytest.fail("inherited policy inventoried tools"),
    )

    assert tool_policy.filter_tool_prompt(
        agent, "agent.system.tool.shell.md", prompt
    ) == prompt
    assert policy_reads == 1


def test_required_response_survives_default_block(monkeypatch, tmp_path: Path) -> None:
    _write_prompt(
        tmp_path,
        "agent.system.tool.response.md",
        '### response\nfinal answer\n{"tool_name":"response","tool_args":{"text":"done"}}',
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", _prompt_paths(tmp_path))
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(default="block", blocked=["local:response"]),
    )
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    agent = _Agent(tmp_path)

    decision = tool_policy.resolve_tool(agent, "response")

    assert decision.allowed is True
    assert decision.source == "framework-required"
    assert tool_policy.get_tool_catalog(agent) == []


def test_tool_and_mcp_defaults_are_independent(monkeypatch, tmp_path: Path) -> None:
    agent = _Agent(tmp_path)
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda _agent: _custom_policy(
            default="block",
            mcp_default="allow",
            allowed=["local:pinned"],
            blocked=["mcp:docs:delete"],
        ),
    )

    assert tool_policy.resolve_tool(agent, "shell", canonical_id="local:shell").allowed is False
    assert tool_policy.resolve_tool(agent, "read", canonical_id="mcp:docs:read").allowed is True
    assert tool_policy.resolve_tool(agent, "pinned", canonical_id="local:pinned").allowed is True
    assert tool_policy.resolve_tool(agent, "delete", canonical_id="mcp:docs:delete").allowed is False


def test_catalog_comes_from_executable_tools_not_prompt_names(
    monkeypatch, tmp_path: Path
) -> None:
    prompt_root = tmp_path / "prompts"
    tool_root = tmp_path / "tools"
    prompt_root.mkdir()
    tool_root.mkdir()
    _write_prompt(
        prompt_root,
        "agent.system.tool.actual.md",
        "### actual\nActual description",
    )
    _write_prompt(
        prompt_root,
        "agent.system.tool.prompt_only.md",
        "### prompt_only\nNo executable implementation",
    )
    (tool_root / "actual.py").write_text("class Actual: pass\n", encoding="utf-8")
    (tool_root / "response.py").write_text("class Response: pass\n", encoding="utf-8")

    def get_paths(agent, *parts, **kwargs):
        if parts[0] == "prompts":
            return [str(prompt_root)]
        if len(parts) == 1:
            return [str(tool_root)]
        return [str(tool_root / parts[1])]

    monkeypatch.setattr(tool_policy.subagents, "get_paths", get_paths)
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "inherit",
            "default": "allow",
            "allowed": [],
            "blocked": [],
        },
    )

    catalog = tool_policy.get_tool_catalog(_Agent(prompt_root))

    assert [item["id"] for item in catalog] == ["local:actual"]
    assert catalog[0]["description"] == "Actual description"


def test_catalog_keeps_installed_remote_tools_without_live_connector(
    monkeypatch, tmp_path: Path
) -> None:
    tool_root = tmp_path / "tools"
    tool_root.mkdir()
    (tool_root / "code_execution_remote.py").write_text("", encoding="utf-8")
    (tool_root / "shell.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        tool_policy.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(tool_root)],
    )
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "inherit",
            "default": "allow",
            "allowed": [],
            "blocked": [],
        },
    )

    catalog = tool_policy.get_tool_catalog(_Agent(tmp_path))

    assert [item["name"] for item in catalog] == ["code_execution_remote", "shell"]


def test_mcp_catalog_labels_include_humanized_server_and_tool(
    monkeypatch, tmp_path: Path
) -> None:
    class MCPTools:
        def get_tools(self):
            return [
                {
                    "deep_wiki.ask_question": {
                        "name": "ask_question",
                        "description": "Ask DeepWiki",
                        "server": "deep_wiki",
                    }
                }
            ]

    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(mcp_handler.MCPConfig, "get_for_agent", lambda agent: MCPTools())
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "inherit",
            "default": "allow",
            "allowed": [],
            "blocked": [],
        },
    )

    assert tool_policy.get_tool_catalog(_Agent(tmp_path)) == [
        {
            "id": "mcp:deep_wiki:ask_question",
            "name": "deep_wiki.ask_question",
            "label": "Deep Wiki · Ask Question",
            "description": "Ask DeepWiki",
            "origin": "MCP · deep_wiki",
            "available": True,
        }
    ]


@pytest.mark.asyncio
async def test_skills_catalog_prompt_is_absent_when_skills_tool_is_blocked(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(default="allow", blocked=["local:skills_tool"]),
    )
    monkeypatch.setattr(
        _13_skills_prompt.skills_helper,
        "list_skills",
        lambda **kwargs: pytest.fail("blocked skill discovery ran"),
    )

    assert await _13_skills_prompt.build_prompt(_Agent(tmp_path)) == ""


def test_tool_prompt_description_skips_fenced_examples() -> None:
    prompt = """### example
~~~json
{"tool_name":"example","tool_args":{}}
~~~
Visible summary
"""

    assert tool_policy.tool_prompt_description(prompt, "example") == "Visible summary"


def test_tool_prompt_description_prefers_declared_summary() -> None:
    prompt = """## tools
- `memory_load`: search stored memories by meaning and metadata
  args: `query`, optional `limit`
"""

    assert (
        tool_policy.tool_prompt_description(prompt, "memory_load")
        == "search stored memories by meaning and metadata"
    )


def test_prompt_filter_removes_complete_blocked_json_example(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        tool_policy,
        "_policy_tool_names",
        lambda agent, policy: {"memory_load", "memory_save"},
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow", blocked=["local:memory_load"]
        ),
    )
    prompt = """## memory tools
- `memory_load`: load memory
- `memory_save`: save memory
~~~json
{
  "tool_name": "memory_load",
  "tool_args": {"query": "blocked example"}
}
~~~
~~~json
{
  "tool_name": "memory_save",
  "tool_args": {"text": "allowed example"}
}
~~~
"""

    filtered = tool_policy.filter_tool_prompt(
        _Agent(tmp_path), "agent.system.tool.memory.md", prompt
    )

    assert "blocked example" not in filtered
    assert "memory_load" not in filtered
    assert "allowed example" in filtered
    assert filtered.count("~~~json") == 1
    assert filtered.count("~~~") == 2


def test_plugin_tool_identity_uses_canonical_plugin_roots(
    monkeypatch, tmp_path: Path
) -> None:
    plugin_root = tmp_path / "plugins" / "_example"
    plugin_tool = plugin_root / "tools" / "actual.py"
    plugin_tool.parent.mkdir(parents=True)
    plugin_tool.write_text("class Actual: pass\n", encoding="utf-8")
    monkeypatch.setattr(
        tool_policy.plugins,
        "get_plugin_roots",
        lambda: [str(tmp_path / "usr" / "plugins"), str(tmp_path / "plugins")],
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "inherit",
            "default": "allow",
            "allowed": [],
            "blocked": [],
        },
    )
    agent = _Agent(tmp_path)

    monkeypatch.setattr(
        tool_policy.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(plugin_tool)],
    )
    assert tool_policy.resolve_tool(agent, "actual").tool_id == "plugin:_example:actual"

    lookalike = tmp_path / "work" / "plugins" / "_example" / "tools" / "actual.py"
    lookalike.parent.mkdir(parents=True)
    lookalike.write_text("class Actual: pass\n", encoding="utf-8")
    monkeypatch.setattr(
        tool_policy.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(lookalike)],
    )
    assert tool_policy.resolve_tool(agent, "actual").tool_id == "local:actual"


def test_dotted_local_tool_keeps_local_identity_at_execution_gate(
    monkeypatch, tmp_path: Path
) -> None:
    tool_path = tmp_path / "docs.read.py"
    tool_path.write_text("class Tool: pass\n", encoding="utf-8")
    monkeypatch.setattr(
        tool_policy.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(tool_path)],
    )
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow", blocked=["local:docs.read"]
        ),
    )
    agent = _Agent(tmp_path)

    with pytest.raises(RepairableException, match='Tool "docs.read" is blocked'):
        tool_policy.ensure_tool_allowed(agent, "docs.read")


def test_legacy_response_and_vision_policy_ids_stay_out_of_catalog(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow",
            blocked=[
                "response",
                "local:response",
                "plugin:legacy:response",
                "vision_load",
                "local:vision_load",
                "plugin:legacy:vision_load",
            ],
        ),
    )

    assert tool_policy.get_tool_catalog(_Agent(tmp_path)) == []


@pytest.mark.asyncio
async def test_vision_tool_follows_chat_config_not_profile_policy(
    monkeypatch, tmp_path: Path
) -> None:
    _write_prompt(tmp_path, "agent.system.tools.md", "TOOLS\n{{tools}}")
    _write_prompt(
        tmp_path,
        "agent.system.tools_vision.md",
        '### vision_load\nload images\n{"tool_name":"vision_load","tool_args":{"paths":[]}}',
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", _prompt_paths(tmp_path))
    monkeypatch.setattr(
        "plugins._model_config.helpers.model_config.get_chat_model_config",
        lambda agent: {"vision": True},
    )
    monkeypatch.setattr(
        "plugins._model_config.helpers.model_config.get_vision_model_config",
        lambda agent: {},
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="block", blocked=["local:vision_load"]
        ),
    )
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda agent: [])
    agent = _Agent(tmp_path)

    prompt = await _11_tools_prompt.build_prompt(agent)
    schemas, _name_map = responses_tools.build_responses_function_tools(agent)

    assert "vision_load" in prompt
    assert [schema["name"] for schema in schemas] == ["vision_load"]
    assert tool_policy.resolve_tool(agent, "vision_load").source == "runtime-config"


@pytest.mark.asyncio
async def test_active_vision_model_uses_canonical_vision_prompt(
    monkeypatch, tmp_path: Path
) -> None:
    _write_prompt(tmp_path, "agent.system.tools.md", "TOOLS\n{{tools}}")
    _write_prompt(
        tmp_path,
        "agent.system.tools_vision.md",
        "### vision_load\ncanonical vision\nargs: `paths`, `query`",
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", _prompt_paths(tmp_path))
    monkeypatch.setattr(
        "plugins._model_config.helpers.model_config.get_chat_model_config",
        lambda agent: {"vision": False},
    )
    monkeypatch.setattr(
        "plugins._model_config.helpers.model_config.get_vision_model_config",
        lambda agent: {"provider": "test", "name": "vision"},
    )
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda agent: [])
    agent = _Agent(tmp_path)

    prompt = await _11_tools_prompt.build_prompt(agent)
    schemas, _name_map = responses_tools.build_responses_function_tools(agent)

    assert prompt.count("canonical vision") == 1
    assert schemas[0]["name"] == "vision_load"
    assert schemas[0]["description"] == "canonical vision"


def test_vision_prompt_stays_route_agnostic_and_batches_paths() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "prompts"
        / "agent.system.tools_vision.md"
    ).read_text(encoding="utf-8")
    schema = responses_tools._schema_from_prompt(source)

    assert schema == {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }
    assert "load all relevant images in one call" in source
    assert "Input schema for tool_args" not in source
    assert "Vision Model" not in source
    assert "sidecar" not in source.lower()
    assert "optional `query`" in source


def test_vision_framework_prompt_renders_optional_query() -> None:
    prompt_dir = str(Path(__file__).resolve().parents[1] / "prompts")

    without_query = files.read_prompt_file(
        "fw.vision_load.md",
        _directories=[prompt_dir],
        request="Review these screenshots.",
        query="",
    )
    with_query = files.read_prompt_file(
        "fw.vision_load.md",
        _directories=[prompt_dir],
        request="Review these screenshots.",
        query="Compare the error banners.",
    )

    assert "Visual query:" not in without_query
    assert "Current request:\nReview these screenshots." in with_query
    assert "Visual query:\nCompare the error banners." in with_query


def test_mcp_prompt_and_native_schema_omit_blocked_tool(
    monkeypatch, tmp_path: Path
) -> None:
    class Server:
        name = "docs"
        description = "Documentation"

        def get_tools(self):
            return [
                {
                    "name": "read",
                    "description": "Read docs",
                    "input_schema": {"type": "object"},
                },
                {
                    "name": "write",
                    "description": "Write docs",
                    "input_schema": {"type": "object"},
                },
            ]

    config = mcp_handler.MCPConfig(servers_list=[])
    config.servers = [Server()]
    allowed_agent = _Agent(tmp_path, profile="agent0")
    restricted_agent = _Agent(tmp_path, profile="researcher")
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow",
            blocked=(
                ["mcp:docs:write"]
                if agent.config.profile == "researcher"
                else []
            ),
        ),
    )
    monkeypatch.setattr(
        responses_tools,
        "_mcp_tools",
        lambda agent: [
            ("docs.read", Server().get_tools()[0]),
            ("docs.write", Server().get_tools()[1]),
        ],
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda agent: "")

    allowed_prompt = config.get_tools_prompt(agent=allowed_agent)
    restricted_prompt = config.get_tools_prompt(agent=restricted_agent)
    allowed_schemas, _ = responses_tools.build_responses_function_tools(allowed_agent)
    restricted_schemas, name_map = responses_tools.build_responses_function_tools(
        restricted_agent
    )

    assert "docs.write" in allowed_prompt
    assert "docs.write" not in restricted_prompt
    assert len(allowed_schemas) == 2
    assert len(restricted_schemas) == 1
    assert name_map[restricted_schemas[0]["name"]] == "docs.read"


@pytest.mark.asyncio
async def test_local_execution_gate_returns_stable_profile_error(
    monkeypatch, tmp_path: Path
) -> None:
    agent = _Agent(tmp_path, profile="researcher")
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(default="block"),
    )

    with pytest.raises(
        RepairableException,
        match='Tool "shell" is blocked for agent profile "researcher"',
    ):
        await EnforceToolPolicy(agent).execute(tool_name="shell")


@pytest.mark.asyncio
async def test_mcp_invocation_rechecks_policy_before_server_call(
    monkeypatch, tmp_path: Path
) -> None:
    agent = _Agent(tmp_path, profile="researcher")
    called = False

    class Config:
        async def call_tool(self, name, kwargs):
            nonlocal called
            called = True
            raise AssertionError("blocked MCP call reached the server")

    monkeypatch.setattr(mcp_handler.MCPConfig, "get_for_agent", lambda agent: Config())
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow", blocked=["mcp:docs:write"]
        ),
    )
    tool = mcp_handler.MCPTool(
        agent=agent,
        name="docs.write",
        method=None,
        args={},
        message="",
        loop_data=None,
    )

    with pytest.raises(RepairableException, match='Tool "docs.write" is blocked'):
        await tool.execute()
    assert called is False


@pytest.mark.asyncio
async def test_delegated_agent_uses_its_own_profile_policy_at_execution_gate(
    monkeypatch, tmp_path: Path
) -> None:
    parent = _Agent(tmp_path, profile="agent0")
    child = _Agent(tmp_path, profile="researcher")
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])

    def policy_for_profile(agent):
        if agent.config.profile == "researcher":
            return _custom_policy(default="block")
        return {"mode": "inherit"}

    monkeypatch.setattr(tool_policy, "get_policy", policy_for_profile)

    assert tool_policy.resolve_tool(parent, "shell").allowed is True
    assert tool_policy.resolve_tool(child, "shell").allowed is False
    await EnforceToolPolicy(parent).execute(tool_name="shell")
    with pytest.raises(
        RepairableException,
        match='Tool "shell" is blocked for agent profile "researcher"',
    ):
        await EnforceToolPolicy(child).execute(tool_name="shell")


def test_project_policy_precedes_profile_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class ProjectContext:
        def get_data(self, key: str, recursive: bool = True):
            return "demo" if key == "project" else None

    monkeypatch.setattr(tool_policy.files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy.plugins,
        "call_plugin_hook",
        lambda _plugin, _hook, default=None, **_kwargs: default,
    )
    agent = _Agent(tmp_path)
    agent.context = ProjectContext()

    tool_policy.plugins.save_plugin_config(
        tool_policy.PLUGIN_NAME,
        "",
        "researcher",
        _custom_policy(default="block"),
    )
    tool_policy.plugins.save_plugin_config(
        tool_policy.PLUGIN_NAME,
        "demo",
        "",
        _custom_policy(default="allow"),
    )
    tool_policy.plugins.save_plugin_config(
        tool_policy.PLUGIN_NAME,
        "demo",
        "researcher",
        _custom_policy(default="allow", blocked=["local:shell"]),
    )
    profile_path = Path(
        tool_policy.plugins.determine_plugin_asset_path(
            tool_policy.PLUGIN_NAME,
            "",
            "researcher",
            tool_policy.plugins.CONFIG_FILE_NAME,
        )
    )
    project_path = Path(
        tool_policy.plugins.determine_plugin_asset_path(
            tool_policy.PLUGIN_NAME,
            "demo",
            "",
            tool_policy.plugins.CONFIG_FILE_NAME,
        )
    )
    project_profile_path = Path(
        tool_policy.plugins.determine_plugin_asset_path(
            tool_policy.PLUGIN_NAME,
            "demo",
            "researcher",
            tool_policy.plugins.CONFIG_FILE_NAME,
        )
    )

    decision = tool_policy.resolve_tool(agent, "shell")
    assert decision.allowed is False
    assert decision.source == "scoped-policy"

    project_profile_path.write_text('{"manual": true}\n', encoding="utf-8")
    decision = tool_policy.resolve_tool(agent, "shell")
    assert decision.allowed is True
    assert decision.source == "scoped-default"
    assert project_profile_path.read_text(encoding="utf-8") == '{"manual": true}\n'

    project_profile_path.write_text(
        '{"manual": true, "mode": "inherit", "default": "block", '
        '"allowed": [], "blocked": ["local:shell"]}\n',
        encoding="utf-8",
    )
    decision = tool_policy.resolve_tool(agent, "shell")
    assert decision.allowed is True
    assert decision.source == "scoped-default"

    project_path.unlink()
    decision = tool_policy.resolve_tool(agent, "shell")
    assert decision.allowed is False
    assert decision.source == "scoped-default"
    assert profile_path.is_file()


def test_unknown_policy_ids_are_retained_as_unavailable(
    monkeypatch, tmp_path: Path
) -> None:
    agent = _Agent(tmp_path)
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_for_agent",
        lambda agent: _NoMCPTools(),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow", blocked=["plugin:missing:ghost"]
        ),
    )

    catalog = tool_policy.get_tool_catalog(agent)

    assert catalog == [
        {
            "id": "plugin:missing:ghost",
            "name": "ghost",
            "label": "Ghost",
            "description": "",
            "origin": "Unavailable",
            "available": False,
        }
    ]
