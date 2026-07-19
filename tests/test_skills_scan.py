import importlib.util
import json
import sys
import types
import zipfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_skills_import_module(tmp_path):
    module_name = "test_skills_import_module"
    stub_names = ("helpers", "helpers.files", "helpers.skills")
    missing = object()
    originals = {name: sys.modules.get(name, missing) for name in stub_names}

    helpers_pkg = types.ModuleType("helpers")
    helpers_pkg.__path__ = []

    files = types.ModuleType("helpers.files")
    files.get_abs_path = lambda *parts: str(tmp_path.joinpath(*parts))

    skills = types.ModuleType("helpers.skills")
    skills.discover_skill_md_files = lambda root: sorted(Path(root).rglob("SKILL.md"))

    helpers_pkg.files = files
    helpers_pkg.skills = skills
    sys.modules["helpers"] = helpers_pkg
    sys.modules["helpers.files"] = files
    sys.modules["helpers.skills"] = skills

    try:
        spec = importlib.util.spec_from_file_location(
            module_name,
            PROJECT_ROOT / "helpers" / "skills_import.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, original in originals.items():
            if original is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_extract_skills_zip_rejects_path_traversal(monkeypatch, tmp_path):
    skills_import = _load_skills_import_module(tmp_path)

    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", "nope")

    with pytest.raises(ValueError, match="Unsafe zip entry path"):
        skills_import.extract_skills_zip(archive_path)

    assert not (tmp_path / "escape.txt").exists()


def test_extract_skills_zip_returns_single_top_level_root(monkeypatch, tmp_path):
    skills_import = _load_skills_import_module(tmp_path)

    archive_path = tmp_path / "skills.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("pack/example/SKILL.md", "---\nname: Example\n---\nBody\n")

    source_root, cleanup_root = skills_import.extract_skills_zip(archive_path)

    assert source_root.name == "pack"
    assert cleanup_root.is_dir()
    assert (source_root / "example" / "SKILL.md").is_file()


def test_settings_skills_scan_section_and_prompt_assets_are_present():
    settings_store = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "settings-store.js"
    ).read_text(encoding="utf-8")
    skills_settings = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "skills-settings.html"
    ).read_text(encoding="utf-8")
    import_template = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "import.html"
    ).read_text(encoding="utf-8")
    scan_prompt = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "skill-scan-prompt.md"
    ).read_text(encoding="utf-8")
    scan_checks = json.loads(
        (
            PROJECT_ROOT
            / "webui"
            / "components"
            / "settings"
            / "skills"
            / "skill-scan-checks.json"
        ).read_text(encoding="utf-8")
    )
    scan_checks_text = json.dumps(scan_checks)

    assert "section-skills-scan" in settings_store
    assert "settings/skills/scan.html" in skills_settings
    assert "settings/skills/import.html" in skills_settings
    assert settings_store.index("section-skills-import") < settings_store.index(
        "section-skills-scan"
    )
    assert skills_settings.index("section-skills-import") < skills_settings.index(
        "section-skills-scan"
    )
    assert "scanSelectedFile()" in import_template
    assert "snyk-agent-scan@latest --json --no-bootstrap" in scan_prompt
    assert "E004" in scan_checks_text
    assert "W007" in scan_checks_text
    assert "W008" in scan_checks_text
    assert "W011" in scan_checks_text
    assert "W012" in scan_checks_text


def test_list_and_import_skills_filters_are_project_only():
    list_template = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "list.html"
    ).read_text(encoding="utf-8")
    list_store = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "skills-list-store.js"
    ).read_text(encoding="utf-8")
    import_template = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "import.html"
    ).read_text(encoding="utf-8")
    import_store = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "skills-import-store.js"
    ).read_text(encoding="utf-8")

    assert "Agent profile" not in list_template
    assert "agentProfile" not in list_store
    assert "agent_profile" not in list_store
    assert "Project" in list_template
    assert "project_name" in list_store
    assert "Limit to agent profile" not in import_template
    assert "agentProfile" not in import_store
    assert "agent_profile" not in import_store
    assert "Limit to project" in import_template
    assert "project_name" in import_store


def test_list_skills_has_mcp_style_search():
    list_template = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "list.html"
    ).read_text(encoding="utf-8")
    list_store = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "skills"
        / "skills-list-store.js"
    ).read_text(encoding="utf-8")

    assert 'type="search"' in list_template
    assert "placeholder=\"Search skills\"" in list_template
    assert "skills-search-clear" in list_template
    assert "filteredSkills" in list_template
    assert "No skills match this search." in list_template
    assert "skillSearch" in list_store
    assert "matchesSearchQuery" in list_store
    assert "clearSkillSearch()" in list_store
