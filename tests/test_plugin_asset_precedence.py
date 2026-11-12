"""User plugin assets must take precedence over bundled plugin assets."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent import Agent
from helpers import cache, extension, files, plugins, providers, responses_tools, subagents


@pytest.fixture
def plugin_tree(monkeypatch, tmp_path):
    # Exercise real discovery and activation against isolated plugin roots.
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(cache, "_cache", {})
    for root in plugins.get_plugin_roots():
        Path(root).mkdir(parents=True)

    def create(name, *, bundled=False):
        root = tmp_path / ("plugins" if bundled else "usr/plugins") / name
        root.mkdir(parents=True)
        (root / "plugin.yaml").write_text(f"name: {name}\n", encoding="utf-8")
        for directory in ("tools", "prompts", "extensions/python/monologue_start"):
            (root / directory).mkdir(parents=True)
        (root / "tools/memory_save.py").write_text(
            "from helpers.tool import Tool, Response\n"
            "class MemorySave(Tool):\n"
            f"    source = {name!r}\n"
            "    async def execute(self, **kwargs):\n"
            "        return Response(self.source, False)\n",
            encoding="utf-8",
        )
        (root / "prompts/memory.md").write_text(name, encoding="utf-8")
        (root / "extensions/python/monologue_start/_10_memory_init.py").write_text(
            "from helpers.extension import Extension\n"
            "class MemoryInit(Extension):\n"
            f"    source = {name!r}\n"
            "    async def execute(self, **kwargs): pass\n",
            encoding="utf-8",
        )
        return root

    return create


@pytest.mark.parametrize(
    "subpaths, asset",
    [
        ((), ""),
        (("tools", "memory_save.py"), "tools/memory_save.py"),
        (("tools", "*.py"), "tools/memory_save.py"),
        (("prompts", "memory.md"), "prompts/memory.md"),
    ],
)
def test_user_assets_precede_alphabetically_earlier_bundled_plugins(
    plugin_tree, subpaths, asset
):
    bundled = plugin_tree("_memory", bundled=True)
    user = plugin_tree("community_memory")

    assert plugins.get_enabled_plugins(None) == ["_memory", "community_memory"]
    assert plugins.get_enabled_plugin_paths(None, *subpaths) == [
        str(user / asset), str(bundled / asset)
    ]
    # Asset priority must not reorder the cached discovery/activation list.
    assert plugins.get_enabled_plugins(None) == ["_memory", "community_memory"]


def test_same_root_order_and_duplicate_plugin_identity_are_preserved(plugin_tree):
    builtin_z = plugin_tree("_zulu", bundled=True)
    user_z = plugin_tree("zulu")
    builtin_a = plugin_tree("_alpha", bundled=True)
    user_a = plugin_tree("alpha")
    plugin_tree("alpha", bundled=True)

    assert plugins.get_enabled_plugin_paths(None) == [
        str(user_a), str(user_z), str(builtin_a), str(builtin_z)
    ]
    assert plugins.get_plugins_list().count("alpha") == 1


def test_order_follows_declared_roots_not_hardcoded_user_directory(
    plugin_tree, monkeypatch
):
    bundled = plugin_tree("_memory", bundled=True)
    user = plugin_tree("community_memory")
    roots = list(reversed(plugins.get_plugin_roots()))
    monkeypatch.setattr(
        plugins, "get_plugin_roots",
        lambda name="": [str(Path(root) / name) for root in roots],
    )

    assert plugins.get_enabled_plugin_paths(None) == [str(bundled), str(user)]


def test_missing_and_noncanonical_paths_do_not_break_priority(
    plugin_tree, monkeypatch, tmp_path
):
    user = plugin_tree("community_memory")
    bundled = plugin_tree("_memory", bundled=True)
    outside = tmp_path / "usr/plugins-other/example"
    outside.mkdir(parents=True)
    locations = {
        "outside": str(outside), "missing": None,
        "_memory": str(bundled), "community_memory": str(user),
    }
    monkeypatch.setattr(plugins, "get_enabled_plugins", lambda _agent: list(locations))
    monkeypatch.setattr(plugins, "find_plugin_dir", locations.get)

    assert plugins.get_enabled_plugin_paths(None) == [
        str(user), str(bundled), str(outside)
    ]


def test_tool_and_background_hook_use_user_plugin_then_restore_builtin(plugin_tree):
    plugin_tree("_memory", bundled=True)
    user = plugin_tree("community_memory")

    tool = Agent.get_tool(None, "memory_save", None, {}, "", None)
    assert tool.source == "community_memory"
    hooks = extension._get_extension_classes("monologue_start")
    assert [hook.source for hook in hooks] == ["community_memory"]

    (user / ".toggle-0").touch()
    cache.clear("*(plugins)*")
    cache.clear("*(extensions)*")
    cache.clear(subagents.PATHS_CACHE_AREA)

    tool = Agent.get_tool(None, "memory_save", None, {}, "", None)
    assert tool.source == "_memory"
    hooks = extension._get_extension_classes("monologue_start")
    assert [hook.source for hook in hooks] == ["_memory"]


def test_project_profile_and_user_overrides_stay_ahead_of_plugin_assets(
    plugin_tree, tmp_path
):
    bundled = plugin_tree("_memory", bundled=True)
    user = plugin_tree("community_memory")
    directories = [
        "usr/projects/demo/.a0proj/agents/researcher",
        "usr/projects/demo/.a0proj",
        "usr/agents/researcher",
        "agents/researcher",
        "usr",
    ]
    overrides = []
    for directory in directories:
        prompt = tmp_path / directory / "prompts/memory.md"
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(directory, encoding="utf-8")
        overrides.append(str(prompt))
    agent = SimpleNamespace(
        config=SimpleNamespace(profile="researcher"),
        context=SimpleNamespace(get_data=lambda key: "demo" if key == "project" else None),
    )

    assert subagents.get_paths(agent, "prompts", "memory.md") == [
        *overrides, str(user / "prompts/memory.md"), str(bundled / "prompts/memory.md")
    ]
    assert Agent.read_prompt(agent, "memory.md") == directories[0]


def test_plugin_prompt_wins_without_higher_priority_override(plugin_tree):
    plugin_tree("_memory", bundled=True)
    plugin_tree("community_memory")

    assert Agent.read_prompt(None, "memory.md") == "community_memory"


def test_empty_asset_results_are_cached(plugin_tree, monkeypatch):
    plugin_tree("_memory", bundled=True)
    assert plugins.get_enabled_plugin_paths(None, "missing") == []

    def unexpected_lookup(*_args):
        pytest.fail("A cached empty result should not rediscover plugins")

    monkeypatch.setattr(plugins, "get_enabled_plugins", unexpected_lookup)
    assert plugins.get_enabled_plugin_paths(None, "missing") == []


def test_provider_merges_apply_user_roots_last_and_preserve_same_root_order(plugin_tree):
    roots = [
        plugin_tree("_alpha", bundled=True), plugin_tree("_zulu", bundled=True),
        plugin_tree("alpha"), plugin_tree("zulu"),
    ]
    for root in roots:
        (root / "conf").mkdir()
        (root / "conf/model_providers.yaml").write_text(
            json.dumps({"chat": {"codex_oauth": {
                "name": root.name,
                "kwargs": {"api_base": f"https://{root.name}.example/v1"},
            }}}),
            encoding="utf-8",
        )

    config = providers.ProviderManager().get_provider_config("chat", "codex_oauth")
    assert config["name"] == "zulu"
    assert config["kwargs"]["api_base"] == "https://zulu.example/v1"

    for root in roots[2:]:
        (root / ".toggle-0").touch()
    cache.clear("*(plugins)*")
    config = providers.ProviderManager().get_provider_config("chat", "codex_oauth")
    assert config["name"] == "_zulu"


@pytest.mark.parametrize("reader", ["load", "catalog", "all_catalog", "editor"])
def test_profile_merges_preserve_root_order_and_higher_scope_overrides(
    plugin_tree, tmp_path, monkeypatch, reader
):
    from plugins._agent_editor.helpers import editor

    monkeypatch.setattr(editor, "USER_AGENTS_ROOT", tmp_path / "usr/agents")
    roots = [
        plugin_tree("_alpha", bundled=True), plugin_tree("_zulu", bundled=True),
        plugin_tree("alpha"), plugin_tree("zulu"),
    ]

    def write_profile(root, title):
        profile = root / "agents/researcher"
        (profile / "prompts").mkdir(parents=True)
        (profile / "agent.yaml").write_text(
            f"title: {title}\ncontext: {title}\n", encoding="utf-8"
        )
        (profile / "prompts/agent.system.main.specifics.md").write_text(
            title, encoding="utf-8"
        )

    def assert_profile(title, project_name=None):
        if reader == "load":
            profile = subagents.load_agent_data("researcher", project_name)
            assert profile.title == profile.context == title
            assert profile.prompts["agent.system.main.specifics.md"] == title
        elif reader == "catalog":
            assert subagents.get_agents_dict(project_name)["researcher"].title == title
        elif reader == "editor":
            state = editor.metadata_state("researcher", editor._EditorContext(project_name or ""))
            assert state["title"]["effective"] == state["context"]["effective"] == title
        else:
            # The global catalog includes profiles from every project.
            assert subagents.get_all_agents_list() == [{"key": "researcher", "label": title}]

    for root in roots:
        write_profile(root, root.name)
    assert_profile("zulu")
    assert plugins.get_enabled_plugin_paths(None, "agents") == [
        str(root / "agents") for root in [*roots[2:], *roots[:2]]
    ]

    for root in roots[2:]:
        (root / ".toggle-0").touch()
    cache.clear("*(plugins)*")
    assert_profile("_zulu")

    for root in roots[2:]:
        (root / ".toggle-0").unlink()
    cache.clear("*(plugins)*")
    write_profile(tmp_path / "usr", "User profile")
    assert_profile("User profile")
    write_profile(tmp_path / "usr/projects/demo/.a0proj", "Project profile")
    assert_profile("Project profile", "demo")


def test_profile_settings_merge_preserves_root_and_scope_priorities(
    plugin_tree, tmp_path, monkeypatch
):
    from extensions.python.agent_init import _15_load_profile_settings as hook

    roots = [
        plugin_tree("_alpha", bundled=True), plugin_tree("_zulu", bundled=True),
        plugin_tree("alpha"), plugin_tree("zulu"),
    ]

    def write_settings(root, **values):
        root.mkdir(parents=True, exist_ok=True)
        path = root / "settings.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path

    for root in roots:
        write_settings(root, root_value=root.name, winner=root.name)
        write_settings(
            root / "agents/researcher", profile_value=root.name, winner=root.name
        )
    write_settings(tmp_path / "agents/researcher", default_only="inherited", winner="default")
    write_settings(tmp_path, excluded_default=True)
    write_settings(tmp_path / "usr", excluded_user=True)

    received = []
    errors = []
    monkeypatch.setattr(
        hook, "initialize_agent",
        lambda override_settings: received.append(override_settings)
        or SimpleNamespace(profile="default", mcp_servers=""),
    )
    agent = SimpleNamespace(
        config=SimpleNamespace(profile="researcher", mcp_servers="inherited MCP"),
        context=SimpleNamespace(
            get_data=lambda *_args: "demo",
            log=SimpleNamespace(log=lambda **entry: errors.append(entry)),
        ),
    )

    def assert_settings(winner, plugin_winner="zulu"):
        hook.LoadProfileSettings(agent).execute()
        values = received[-1]
        assert values["winner"] == winner
        assert values["root_value"] == values["profile_value"] == plugin_winner
        assert values["default_only"] == "inherited"
        assert "excluded_default" not in values and "excluded_user" not in values
        assert agent.config.profile == "researcher"
        assert agent.config.mcp_servers == "inherited MCP"

    assert_settings("zulu")
    assert plugins.get_enabled_plugin_paths(agent, "settings.json") == [
        str(root / "settings.json") for root in [*roots[2:], *roots[:2]]
    ]
    write_settings(tmp_path / "usr/agents/researcher", winner="user")
    assert_settings("user")
    project = tmp_path / "usr/projects/demo/.a0proj"
    write_settings(project, winner="project")
    assert_settings("project")
    project_profile = write_settings(project / "agents/researcher", winner="")
    assert_settings("")

    for root in roots[2:]:
        (root / ".toggle-0").touch()
    cache.clear("*(plugins)*")
    assert_settings("", "_zulu")

    project_profile.write_text("[]", encoding="utf-8")
    assert_settings("project", "_zulu")
    assert len(errors) == 1 and errors[0]["type"] == "error"
    assert str(project_profile) in errors[0]["content"]


def test_model_prompt_native_schema_and_dispatch_use_the_same_plugin(
    plugin_tree, monkeypatch, tmp_path
):
    from extensions.python.system_prompt._11_tools_prompt import build_prompt
    from plugins._model_config.helpers import model_config

    bundled = plugin_tree("_memory", bundled=True)
    user = plugin_tree("db_hub")
    for root, field in [(bundled, "text"), (user, "content")]:
        schema = {"type": "object", "properties": {field: {"type": "string"}}}
        (root / "prompts/agent.system.tool.memory.md").write_text(
            f"### memory_save\n{root.name}\nInput schema for tool_args:\n"
            + json.dumps(schema),
            encoding="utf-8",
        )
    template = tmp_path / "usr/prompts/agent.system.tools.md"
    template.parent.mkdir(parents=True)
    template.write_text("{{tools}}", encoding="utf-8")
    agent = object.__new__(Agent)
    agent.config = SimpleNamespace(profile="")
    agent.context = SimpleNamespace(get_data=lambda *args: None)
    agent.data = {}
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda _agent: [])
    monkeypatch.setattr(model_config, "get_chat_model_config", lambda _agent: {})
    monkeypatch.setattr(model_config, "get_vision_model_config", lambda _agent: {})

    for root, field, other in [(user, "content", bundled), (bundled, "text", user)]:
        prompt = asyncio.run(build_prompt(agent))
        assert prompt.count(root.name) == 1 and other.name not in prompt
        native, names = responses_tools.build_responses_function_tools(agent)
        assert len(native) == 1 and names == {"memory_save": "memory_save"}
        assert root.name in native[0]["description"]
        assert other.name not in native[0]["description"]
        assert set(native[0]["parameters"]["properties"]) == {field}
        tool = agent.get_tool("memory_save", None, {field: "probe"}, "", None)
        assert asyncio.run(tool.execute()).message == root.name
        (user / ".toggle-0").touch()
        cache.clear("*(plugins)*")
        cache.clear("*(extensions)*")
