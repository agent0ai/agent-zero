import importlib.util
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_HELPER_PATH = PROJECT_ROOT / "helpers" / "skills.py"
HELPER_STUB_MODULES = (
    "helpers",
    "helpers.files",
    "helpers.projects",
    "helpers.plugins",
    "helpers.subagents",
    "helpers.file_tree",
    "helpers.runtime",
)


def _register_helpers_stubs():
    helpers_pkg = types.ModuleType("helpers")
    helpers_pkg.__path__ = []

    files = types.ModuleType("helpers.files")
    files.normalize_a0_path = lambda path: str(path).replace("\\", "/")
    files.fix_dev_path = lambda path: str(path).replace("\\", "/")
    files.get_abs_path = lambda *parts: "/" + "/".join(str(part).strip("/") for part in parts if part)
    files.exists = lambda path: False
    files.is_in_dir = lambda path, root: str(path).startswith(str(root))
    files.find_existing_paths_by_pattern = lambda pattern: []
    files.read_file = lambda path: ""

    projects = types.ModuleType("helpers.projects")
    projects.get_context_project_name = lambda context: context.get_data("project")
    projects.get_project_meta = lambda project_name, *parts: (
        f"/projects/{project_name}/" + "/".join(str(part).strip("/") for part in parts if part)
        if project_name
        else ""
    )

    plugins = types.ModuleType("helpers.plugins")
    plugins.get_plugin_config = lambda *args, **kwargs: {}
    plugins.get_enabled_plugin_paths = lambda *args, **kwargs: []

    subagents = types.ModuleType("helpers.subagents")
    subagents.get_paths = lambda agent, *parts: []

    file_tree = types.ModuleType("helpers.file_tree")
    file_tree.file_tree = lambda *args, **kwargs: ""

    runtime = types.ModuleType("helpers.runtime")
    runtime.is_development = lambda: False

    helpers_pkg.files = files
    helpers_pkg.projects = projects
    helpers_pkg.plugins = plugins
    helpers_pkg.subagents = subagents
    helpers_pkg.file_tree = file_tree
    helpers_pkg.runtime = runtime

    sys.modules["helpers"] = helpers_pkg
    sys.modules["helpers.files"] = files
    sys.modules["helpers.projects"] = projects
    sys.modules["helpers.plugins"] = plugins
    sys.modules["helpers.subagents"] = subagents
    sys.modules["helpers.file_tree"] = file_tree
    sys.modules["helpers.runtime"] = runtime


def _load_skills_helper_module():
    missing = object()
    original_modules = {name: sys.modules.get(name, missing) for name in HELPER_STUB_MODULES}
    _register_helpers_stubs()
    try:
        spec = importlib.util.spec_from_file_location("test_skills_helper_module", SKILLS_HELPER_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, original in original_modules.items():
            if original is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


runtime = _load_skills_helper_module()


class DummyContext:
    def __init__(self):
        self.data = {}

    def get_data(self, key, recursive=True):
        return self.data.get(key)

    def set_data(self, key, value, recursive=True):
        self.data[key] = value


class DummyAgent:
    def __init__(self):
        self.context = DummyContext()
        self.data = {}


def _scope_config(entries):
    return {"active_skills": entries}


def test_active_skills_cap_is_twenty():
    assert runtime.MAX_ACTIVE_SKILLS == 20
    assert runtime.get_max_active_skills() == 20


def test_chat_activation_can_override_scope_defaults(monkeypatch):
    monkeypatch.setattr(
        runtime.plugin_helpers,
        "get_plugin_config",
        lambda *args, **kwargs: _scope_config([{"name": "Pinned"}]),
    )
    agent = DummyAgent()

    assert [entry["name"] for entry in runtime.get_active_skills(agent)] == [
        "Pinned"
    ]

    runtime.activate_chat_skill(agent, {"name": "Extra"})
    assert [entry["name"] for entry in runtime.get_active_skills(agent)] == [
        "Pinned",
        "Extra",
    ]
    assert [entry["name"] for entry in runtime.get_chat_active_skills(agent.context)] == [
        "Extra"
    ]

    runtime.deactivate_chat_skill(agent, {"name": "Pinned"})
    assert [entry["name"] for entry in runtime.get_active_skills(agent)] == [
        "Extra"
    ]
    assert [entry["name"] for entry in runtime.get_chat_disabled_skills(agent.context)] == [
        "Pinned"
    ]

    runtime.activate_chat_skill(agent, {"name": "Pinned"})
    assert [entry["name"] for entry in runtime.get_active_skills(agent)] == [
        "Pinned",
        "Extra",
    ]
    assert runtime.get_chat_disabled_skills(agent.context) == []


def test_chat_deactivation_hides_name_only_scope_default_by_path(monkeypatch):
    monkeypatch.setattr(
        runtime.plugin_helpers,
        "get_plugin_config",
        lambda *args, **kwargs: _scope_config([{"name": "Pinned"}]),
    )
    agent = DummyAgent()

    runtime.deactivate_chat_skill(
        agent,
        {"name": "Pinned", "path": "/a0/usr/skills/custom/pinned"},
    )

    assert runtime.get_active_skills(agent) == []
    assert runtime.get_chat_disabled_skills(agent.context) == [
        {"name": "Pinned", "path": "/a0/usr/skills/custom/pinned"}
    ]


def test_reactivating_name_only_scope_default_by_path_clears_hidden_override(monkeypatch):
    monkeypatch.setattr(
        runtime.plugin_helpers,
        "get_plugin_config",
        lambda *args, **kwargs: _scope_config([{"name": "Pinned"}]),
    )
    agent = DummyAgent()

    runtime.deactivate_chat_skill(
        agent,
        {"name": "Pinned", "path": "/a0/usr/skills/custom/pinned"},
    )
    runtime.activate_chat_skill(
        agent,
        {"name": "Pinned", "path": "/a0/usr/skills/custom/pinned"},
    )

    assert runtime.get_active_skills(agent) == [{"name": "Pinned"}]
    assert runtime.get_chat_active_skills(agent.context) == []
    assert runtime.get_chat_disabled_skills(agent.context) == []


def test_loaded_skill_entries_come_from_agent_data():
    agent = DummyAgent()
    agent.data[runtime.AGENT_DATA_NAME_LOADED_SKILLS] = [
        "host-computer-use",
        "",
        "a0-development",
    ]

    assert runtime.get_loaded_skill_entries(agent) == [
        {"name": "host-computer-use"},
        {"name": "a0-development"},
    ]


def test_skill_runtime_does_not_alias_old_office_skill_references():
    entries = runtime.normalize_active_skills(
        [
            "office-artifacts",
            {"name": "word-documents"},
            {"path": "/a0/plugins/_office/skills/excel-workbooks"},
            {"name": "Desktop", "path": "/a0/plugins/_office/skills/linux-desktop"},
            "presentation-decks",
        ]
    )

    assert entries == [
        {"name": "office-artifacts"},
        {"name": "word-documents"},
        {"path": "/a0/plugins/_office/skills/excel-workbooks"},
        {"name": "Desktop", "path": "/a0/plugins/_office/skills/linux-desktop"},
        {"name": "presentation-decks"},
    ]

    agent = DummyAgent()
    agent.data[runtime.AGENT_DATA_NAME_LOADED_SKILLS] = [
        "office-artifacts",
        "word-documents",
        "excel-workbooks",
        "presentation-decks",
    ]

    assert runtime.get_loaded_skill_entries(agent) == [
        {"name": "office-artifacts"},
        {"name": "word-documents"},
        {"name": "excel-workbooks"},
        {"name": "presentation-decks"},
    ]

    assert runtime.unload_agent_skill(agent, {"name": "office-artifacts"}) is True
    assert agent.data[runtime.AGENT_DATA_NAME_LOADED_SKILLS] == [
        "word-documents",
        "excel-workbooks",
        "presentation-decks",
    ]


def test_builtin_plugin_skill_delete_is_rejected_before_filesystem_delete():
    with pytest.raises(PermissionError, match="Built-in plugin skills cannot be deleted"):
        runtime.delete_skill("/a0/plugins/_office/skills/document-artifacts")


def test_invalid_skill_frontmatter_reports_yaml_errors():
    frontmatter, errors = runtime.parse_frontmatter("name: [unterminated\n")

    assert frontmatter == {}
    assert errors
    assert errors[0].startswith("Invalid YAML frontmatter")


def test_a0_manage_plugin_skill_frontmatter_is_valid_yaml():
    text = (PROJECT_ROOT / "skills" / "a0-manage-plugin" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    frontmatter, body, errors = runtime.split_frontmatter(text)

    assert errors == []
    assert frontmatter["name"] == "a0-manage-plugin"
    assert "Agent Zero Plugin Management" in body


def test_renamed_skills_use_standard_frontmatter_only():
    skill_paths = [
        PROJECT_ROOT / "skills" / "build-skill" / "SKILL.md",
        PROJECT_ROOT / "skills" / "scheduled-tasks" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_a0_connector" / "skills" / "host-code-execution" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_a0_connector" / "skills" / "host-computer-use" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_a0_connector" / "skills" / "host-file-editing" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_a0_connector" / "skills" / "setup-a0-cli" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_browser" / "skills" / "browser-automation" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_browser" / "skills" / "browser-extension-control" / "SKILL.md",
        PROJECT_ROOT / "plugins" / "_browser" / "skills" / "browser-form-workflows" / "SKILL.md",
    ]

    for path in skill_paths:
        frontmatter, body, errors = runtime.split_frontmatter(path.read_text(encoding="utf-8"))
        assert errors == []
        assert set(frontmatter) == {"name", "description"}
        assert frontmatter["name"] == path.parent.name
        assert frontmatter["description"]
        assert body


def test_unload_agent_skill_removes_loaded_skill_by_name():
    agent = DummyAgent()
    agent.data[runtime.AGENT_DATA_NAME_LOADED_SKILLS] = [
        "host-computer-use",
        "a0-development",
    ]

    removed = runtime.unload_agent_skill(
        agent,
        {
            "name": "host-computer-use",
            "path": "/a0/plugins/_a0_connector/skills/host-computer-use",
        },
    )

    assert removed is True
    assert agent.data[runtime.AGENT_DATA_NAME_LOADED_SKILLS] == [
        "a0-development"
    ]


def test_clearing_chat_overrides_restores_scope_defaults(monkeypatch):
    monkeypatch.setattr(
        runtime.plugin_helpers,
        "get_plugin_config",
        lambda *args, **kwargs: _scope_config([{"name": "Pinned"}]),
    )
    agent = DummyAgent()
    runtime.activate_chat_skill(agent, {"name": "Extra"})
    runtime.deactivate_chat_skill(agent, {"name": "Pinned"})

    runtime.clear_chat_skill_overrides(agent)

    assert [entry["name"] for entry in runtime.get_active_skills(agent)] == [
        "Pinned"
    ]
    assert runtime.get_chat_active_skills(agent.context) == []
    assert runtime.get_chat_disabled_skills(agent.context) == []


def test_activating_new_skill_fails_once_limit_is_full(monkeypatch):
    monkeypatch.setattr(
        runtime.plugin_helpers,
        "get_plugin_config",
        lambda *args, **kwargs: _scope_config(
            [{"name": f"Pinned {index}"} for index in range(20)]
        ),
    )
    agent = DummyAgent()

    with pytest.raises(ValueError, match="at most 20"):
        runtime.activate_chat_skill(agent, {"name": "Overflow"})

    assert len(runtime.get_active_skills(agent)) == 20
