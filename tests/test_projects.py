import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

import initialize
from agent import AgentConfig, AgentContext
from helpers import dirty_json, files, persist_chat, projects, subagents
from helpers import state_monitor_integration


def _prepare_project_tree(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    (tmp_path / "usr" / "projects").mkdir(parents=True, exist_ok=True)
    (tmp_path / "usr" / "plugins").mkdir(parents=True, exist_ok=True)
    (tmp_path / "plugins").mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize(
    "destination_project", ["project-y", None], ids=["project", "global"]
)
def test_project_switch_resets_only_profiles_missing_from_the_new_scope(
    monkeypatch, destination_project
):
    context_id = "ctx-project-profile-switch"
    AgentContext.remove(context_id)
    context = AgentContext(
        config=AgentConfig(mcp_servers="", profile="project-only"),
        id=context_id,
        set_current=False,
    )
    monkeypatch.setattr(
        projects,
        "load_edit_project_data",
        lambda name: {"title": name.title(), "color": ""},
    )
    monkeypatch.setattr(persist_chat, "save_tmp_chat", lambda _context: None)
    monkeypatch.setattr(
        subagents,
        "get_agents_dict",
        lambda project_name=None: {
            "agent0": subagents.SubAgentListItem(name="agent0"),
            **(
                {
                    "project-only": subagents.SubAgentListItem(
                        name="project-only"
                    )
                }
                if project_name == "project-x"
                else {}
            ),
        },
    )
    monkeypatch.setattr(
        initialize,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "agent0"),
        ),
    )

    try:
        projects.activate_project(context_id, "project-x", mark_dirty=False)
        assert context.config.profile == "project-only"

        if destination_project:
            projects.activate_project(
                context_id, destination_project, mark_dirty=False
            )
        else:
            projects.deactivate_project(context_id, mark_dirty=False)
        assert context.config.profile == "agent0"
        assert context.agent0.config.profile == "agent0"
    finally:
        AgentContext.remove(context_id)


def test_project_agent_availability_retains_project_only_profiles(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        subagents,
        "get_agents_dict",
        lambda project_name=None: {
            "global": subagents.SubAgentListItem(name="global", enabled=True),
            **(
                {
                    "project-only": subagents.SubAgentListItem(
                        name="project-only", enabled=True
                    )
                }
                if project_name == "demo"
                else {}
            ),
        },
    )

    assert projects._normalize_subagents(
        {
            "global": {"enabled": True},
            "project-only": {"enabled": False},
            "missing": {"enabled": False},
        },
        "demo",
    ) == {"project-only": {"enabled": False}}


def test_profile_reconciliation_uses_an_available_fallback(monkeypatch) -> None:
    context_id = "ctx-profile-availability-fallback"
    AgentContext.remove(context_id)
    context = AgentContext(
        config=AgentConfig(mcp_servers="", profile="disabled"),
        id=context_id,
        set_current=False,
    )
    monkeypatch.setattr(
        subagents,
        "get_available_agents_dict",
        lambda _project_name: {
            "researcher": subagents.SubAgentListItem(name="researcher")
        },
    )
    monkeypatch.setattr(
        initialize,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "default"),
        ),
    )

    try:
        assert projects.reconcile_agent_profile(context, None) is True
        assert context.config.profile == "researcher"
        assert context.agent0.config.profile == "researcher"
    finally:
        AgentContext.remove(context_id)


def test_context_lookup_reconciles_only_new_contexts(monkeypatch) -> None:
    from helpers.context_utils import use_context

    existing_id = "ctx-existing-profile"
    created_id = "ctx-new-profile"
    AgentContext.remove(existing_id)
    AgentContext.remove(created_id)
    existing = AgentContext(
        config=AgentConfig(mcp_servers="", profile="default"),
        id=existing_id,
        set_current=False,
    )
    reconciled: list[str] = []
    monkeypatch.setattr(
        initialize,
        "initialize_agent",
        lambda: AgentConfig(mcp_servers="", profile="default"),
    )
    monkeypatch.setattr(
        projects,
        "reconcile_agent_profile",
        lambda context, _project: reconciled.append(context.id),
    )

    try:
        assert use_context(threading.RLock(), existing_id) is existing
        assert reconciled == []

        assert use_context(threading.RLock(), created_id).id == created_id
        assert reconciled == [created_id]
    finally:
        AgentContext.remove(existing_id)
        AgentContext.remove(created_id)


@pytest.mark.parametrize(
    ("all_scopes", "expected"),
    [
        (False, ["global-changed"]),
        (True, ["global-changed", "project-changed"]),
    ],
)
def test_bulk_profile_reconciliation_persists_only_changed_chats(
    monkeypatch, all_scopes: bool, expected: list[str]
) -> None:
    unchanged = SimpleNamespace(id="global-unchanged", project=None)
    global_changed = SimpleNamespace(id="global-changed", project=None)
    project_changed = SimpleNamespace(id="project-changed", project="demo")
    saved: list[str] = []
    dirty: list[str] = []
    catalog_lookups: list[str | None] = []
    monkeypatch.setattr(
        AgentContext,
        "all",
        classmethod(
            lambda _cls: [unchanged, global_changed, project_changed]
        ),
    )
    monkeypatch.setattr(
        projects, "get_context_project_name", lambda context: context.project
    )
    monkeypatch.setattr(
        projects,
        "reconcile_agent_profile",
        lambda context, _project, _available: context is not unchanged,
    )
    monkeypatch.setattr(
        subagents,
        "get_available_agents_dict",
        lambda project: catalog_lookups.append(project) or {},
    )
    monkeypatch.setattr(
        persist_chat, "save_tmp_chat", lambda context: saved.append(context.id)
    )
    monkeypatch.setattr(
        state_monitor_integration,
        "mark_dirty_for_context",
        lambda context_id, **_kwargs: dirty.append(context_id),
    )

    projects.reconcile_agent_profiles(None, all_scopes=all_scopes)

    assert saved == expected
    assert dirty == expected
    assert catalog_lookups == ([None, "demo"] if all_scopes else [None])


def test_project_include_agents_md_defaults_true_and_saves(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    meta = tmp_path / "usr" / "projects" / "demo" / ".a0proj"
    meta.mkdir(parents=True)
    (meta / "project.json").write_text('{"title": "Demo"}', encoding="utf-8")

    data = projects.load_basic_project_data("demo")

    assert data["include_agents_md"] is True

    projects.save_project_header("demo", data)
    saved = dirty_json.parse((meta / "project.json").read_text(encoding="utf-8"))

    assert saved["include_agents_md"] is True


def test_project_mcp_servers_persist_in_project_meta(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    config = '{"mcpServers":{"demo":{"url":"https://example.com/mcp"}}}'

    projects.create_project(
        "demo",
        {
            "title": "Demo",
            "mcp_servers": config,
        },
    )

    assert projects.load_project_mcp_servers("demo") == config
    assert projects.load_edit_project_data("demo")["mcp_servers"] == config

    updated = '{"mcpServers":{"other":{"command":"uvx","args":["pkg"]}}}'
    projects.save_project_mcp_servers("demo", updated)

    assert projects.load_project_mcp_servers("demo") == updated


def test_project_mcp_servers_reject_path_names(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)

    for name in ("../escape", "nested/project", ".", "..", ""):
        try:
            projects.save_project_mcp_servers(name, '{"mcpServers":{}}')
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid project name: {name!r}")


def test_project_creation_creates_skills_folder(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)

    projects.create_project("demo", {"title": "Demo"})

    assert (tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "skills").is_dir()


def test_project_load_repairs_missing_skills_folder(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    meta = tmp_path / "usr" / "projects" / "demo" / ".a0proj"
    meta.mkdir(parents=True)
    (meta / "project.json").write_text('{"title": "Demo"}', encoding="utf-8")

    assert not (meta / "skills").exists()

    projects.load_edit_project_data("demo")

    assert (meta / "skills").is_dir()


def test_project_system_prompt_includes_root_agents_md_with_path(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    projects.create_project(
        "demo",
        {
            "title": "Demo",
            "instructions": "Main project rule.",
        },
    )
    project_root = tmp_path / "usr" / "projects" / "demo"
    (project_root / "AGENTS.md").write_text("Root AGENTS rule.", encoding="utf-8")
    (
        project_root / ".a0proj" / "instructions" / "extra.md"
    ).write_text("Folder instruction rule.", encoding="utf-8")

    prompt_vars = projects.build_system_prompt_vars("demo")
    instructions = prompt_vars["project_instructions"]

    assert "Main project rule." in instructions
    assert instructions.count("## project instruction files") == 1
    assert "## project instruction file\n" not in instructions
    assert "### path: /a0/usr/projects/demo/AGENTS.md" in instructions
    assert "Root AGENTS rule." in instructions
    assert "### path: /a0/usr/projects/demo/.a0proj/instructions/extra.md" in instructions
    assert "Folder instruction rule." in instructions


def test_project_system_prompt_prefers_agents_override_md(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    projects.create_project("demo", {"title": "Demo"})
    project_root = tmp_path / "usr" / "projects" / "demo"
    (project_root / "AGENTS.md").write_text("Standard rule.", encoding="utf-8")
    (project_root / "AGENTS.override.md").write_text("Override rule.", encoding="utf-8")

    instructions = projects.build_system_prompt_vars("demo")["project_instructions"]

    assert "### path: /a0/usr/projects/demo/AGENTS.override.md" in instructions
    assert "Override rule." in instructions
    assert "Standard rule." not in instructions


def test_project_system_prompt_respects_disabled_agents_md(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    projects.create_project(
        "demo",
        {
            "title": "Demo",
            "include_agents_md": False,
        },
    )
    project_root = tmp_path / "usr" / "projects" / "demo"
    (project_root / "AGENTS.md").write_text("Root AGENTS rule.", encoding="utf-8")

    prompt_vars = projects.build_system_prompt_vars("demo")

    assert "Root AGENTS rule." not in prompt_vars["project_instructions"]
    assert "AGENTS.md" not in prompt_vars["project_instructions"]


def test_agents_md_chain_walks_direct_path_only(monkeypatch, tmp_path):
    _prepare_project_tree(monkeypatch, tmp_path)
    root = tmp_path
    (root / "AGENTS.md").write_text("root doc", encoding="utf-8")
    target = root / "services" / "payments"
    sibling = root / "services" / "auth"
    target.mkdir(parents=True)
    sibling.mkdir(parents=True)
    (root / "services" / "AGENTS.md").write_text("services doc", encoding="utf-8")
    (target / "AGENTS.md").write_text("payments doc", encoding="utf-8")
    (sibling / "AGENTS.md").write_text("auth doc", encoding="utf-8")

    chain = projects.get_agents_md_chain(str(root), str(target / "handler.py"))
    contents = [content for _, content in chain]

    assert contents == ["root doc", "services doc", "payments doc"]


def test_agents_md_protocol_excludes_project_root_and_keeps_subdir(
    monkeypatch, tmp_path
):
    _prepare_project_tree(monkeypatch, tmp_path)
    prompt_name = "agent.protocol.projects.agents_md.md"
    prompt_source = Path(__file__).resolve().parents[1] / "prompts" / prompt_name
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / prompt_name).write_text(
        prompt_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    projects.create_project("demo", {"title": "Demo"})
    (tmp_path / "AGENTS.md").write_text("framework doc", encoding="utf-8")
    project_root = tmp_path / "usr" / "projects" / "demo"
    (project_root / "AGENTS.md").write_text("project root doc", encoding="utf-8")
    api_dir = project_root / "api"
    api_dir.mkdir()
    (api_dir / "AGENTS.md").write_text("api doc", encoding="utf-8")

    protocol = projects.build_agents_md_protocol(
        "demo",
        target=str(api_dir / "handler.py"),
    )

    assert "framework doc" in protocol
    assert "api doc" in protocol
    assert "project root doc" not in protocol
