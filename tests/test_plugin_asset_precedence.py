"""User plugin assets must take precedence over bundled plugin assets."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from agent import Agent
from helpers import cache, extension, files, plugins, subagents


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
