from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from extensions.python.system_prompt import _11_tools_prompt
from helpers import mcp_handler, responses_tools, tool_policy
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


def _custom_policy(*, default: str, allowed=(), blocked=()):
    return {
        "mode": "custom",
        "default": default,
        "allowed": list(allowed),
        "blocked": list(blocked),
    }


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


def test_tool_prompt_description_skips_fenced_examples() -> None:
    prompt = """### example
~~~json
{"tool_name":"example","tool_args":{}}
~~~
Visible summary
"""

    assert tool_policy.tool_prompt_description(prompt, "example") == "Visible summary"


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
    agent = _Agent(tmp_path)
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: _custom_policy(
            default="allow", blocked=["mcp:docs:write"]
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

    prompt = config.get_tools_prompt(agent=agent)
    schemas, name_map = responses_tools.build_responses_function_tools(agent)

    assert "docs.read" in prompt
    assert "docs.write" not in prompt
    assert len(schemas) == 1
    assert name_map[schemas[0]["name"]] == "docs.read"


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

    def config_for_profile(plugin_name, agent=None, **kwargs):
        if agent.config.profile == "researcher":
            return _custom_policy(default="block")
        return {"mode": "inherit"}

    monkeypatch.setattr(tool_policy.plugins, "get_plugin_config", config_for_profile)

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

    project_profile_path.unlink()
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
