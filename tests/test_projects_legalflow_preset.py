import shutil
import uuid
from pathlib import Path

def _rmtree(path: str) -> None:
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return


def _make_minimal_project_data(projects_module):
    return {
        "title": "Test Matter",
        "description": "",
        "instructions": "",
        "color": "",
        "git_url": "",
        "memory": "own",
        "file_structure": projects_module._default_file_structure_settings(),
    }


def test_new_project_defaults_to_legalflow_and_writes_template(monkeypatch, tmp_path):
    from python.helpers import files, projects, settings

    monkeypatch.setattr(settings, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    name = f"test_matter_{uuid.uuid4().hex[:8]}"
    created = None
    try:
        monkeypatch.setenv("A0_SET_projects_default_preset", "legalflow")
        settings.reload_settings()

        created = projects.create_project(name, _make_minimal_project_data(projects))
        header = projects.load_project_header(created)

        assert header.get("preset") == "legalflow"
        template = Path(files.get_abs_path("conf/projects.preset.legalflow.instructions.md")).read_text(
            encoding="utf-8"
        ).strip()
        assert (header.get("instructions") or "").strip() == template

        project_root = Path(files.get_abs_path("usr/projects", created))
        assert (project_root / ".a0proj" / "project.json").exists()
        assert (project_root / ".a0proj" / "knowledge").is_dir()
        assert (project_root / "README.md").exists()
        assert (project_root / "00-intake").is_dir()
        assert (project_root / "03-drafts").is_dir()
    finally:
        settings.reload_settings()
        if created:
            _rmtree(files.get_abs_path("usr/projects", created))
        else:
            _rmtree(files.get_abs_path("usr/projects", name))


def test_new_project_can_default_to_generic_without_legalflow_artifacts(monkeypatch, tmp_path):
    from python.helpers import files, projects, settings

    monkeypatch.setattr(settings, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    name = f"test_generic_{uuid.uuid4().hex[:8]}"
    created = None
    try:
        monkeypatch.setenv("A0_SET_projects_default_preset", "generic")
        settings.reload_settings()

        created = projects.create_project(name, _make_minimal_project_data(projects))
        header = projects.load_project_header(created)

        assert header.get("preset") == "generic"
        assert (header.get("instructions") or "").strip() == ""

        project_root = Path(files.get_abs_path("usr/projects", created))
        assert (project_root / ".a0proj" / "project.json").exists()
        assert (project_root / ".a0proj" / "knowledge").is_dir()
        assert not (project_root / "README.md").exists()
        assert not (project_root / "00-intake").exists()
        assert not (project_root / "03-drafts").exists()
    finally:
        settings.reload_settings()
        if created:
            _rmtree(files.get_abs_path("usr/projects", created))
        else:
            _rmtree(files.get_abs_path("usr/projects", name))
