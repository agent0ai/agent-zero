from pathlib import Path

from helpers import dirty_json, files, projects


def _prepare_project_tree(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    (tmp_path / "usr" / "projects").mkdir(parents=True, exist_ok=True)
    (tmp_path / "usr" / "plugins").mkdir(parents=True, exist_ok=True)
    (tmp_path / "plugins").mkdir(parents=True, exist_ok=True)


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
