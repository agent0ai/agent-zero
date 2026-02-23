from __future__ import annotations

import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import projects
from python.helpers.skills_import import (
    build_import_plan,
    import_skills,
    resolve_display_destination,
)


def _write_skill(root: Path, skill_name: str = "demo-skill") -> Path:
    skill_dir = root / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: demo\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    return skill_dir


def _mock_get_project_meta_factory(base_dir: Path):
    def _mock_get_project_meta(project_name: str, *sub_dirs: str) -> str:
        return str(base_dir / "usr" / "projects" / project_name / ".a0proj" / Path(*sub_dirs))

    return _mock_get_project_meta


def test_build_import_plan_does_not_duplicate_skills_segment_for_project_destination(tmp_path: Path):
    source_root = tmp_path / "source"
    _write_skill(source_root)

    project_skills_root = tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "skills"

    plan, _ = build_import_plan(source_root, project_skills_root, namespace="skills")

    assert len(plan) == 1
    assert plan[0].dest_skill_dir == project_skills_root / "demo-skill"
    assert "/skills/skills/" not in str(plan[0].dest_skill_dir).replace("\\", "/")


def test_import_skills_project_scope_does_not_produce_skills_skills_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(projects, "get_project_meta", _mock_get_project_meta_factory(tmp_path))

    source_root = tmp_path / "source"
    _write_skill(source_root)

    result = import_skills(
        str(source_root),
        namespace="skills",
        dry_run=True,
        project_name="demo",
    )

    expected_destination_root = tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "skills"

    assert result.destination_root == expected_destination_root
    assert result.imported
    assert result.imported[0] == expected_destination_root / "demo-skill"
    assert "/skills/skills/" not in str(result.imported[0]).replace("\\", "/")


def test_import_zip_named_skills_defaults_namespace_but_does_not_duplicate_segment(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(projects, "get_project_meta", _mock_get_project_meta_factory(tmp_path))

    source_root = tmp_path / "source"
    _write_skill(source_root)

    zip_path = tmp_path / "skills.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in source_root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source_root))

    result = import_skills(
        str(zip_path),
        namespace=None,
        dry_run=True,
        project_name="demo",
    )

    expected_destination_root = tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "skills"

    assert result.namespace == "skills"
    assert result.destination_root == expected_destination_root
    assert result.imported
    assert result.imported[0] == expected_destination_root / "demo-skill"
    assert "/skills/skills/" not in str(result.imported[0]).replace("\\", "/")


def test_resolve_display_destination_does_not_duplicate_terminal_namespace(tmp_path: Path):
    destination_root = tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "skills"
    assert resolve_display_destination(destination_root, "skills") == destination_root


def test_resolve_display_destination_appends_distinct_namespace(tmp_path: Path):
    destination_root = tmp_path / "usr" / "skills"
    assert resolve_display_destination(destination_root, "my-pack") == destination_root / "my-pack"
