import zipfile
from pathlib import Path

import pytest

from test_skills_scan import _load_skills_import_module


def _skill_pack(tmp_path: Path, body: str) -> Path:
    archive_path = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("probe/SKILL.md", f"---\nname: probe\ndescription: probe\n---\n{body}\n")
    return archive_path


def _installed_skill(skills_import, tmp_path: Path) -> Path:
    result = skills_import.import_skills(str(_skill_pack(tmp_path, "old")), namespace="ns")
    [installed] = result.imported
    (installed / "local-notes.md").write_text("user edits")
    return installed


@pytest.mark.parametrize("conflict", ["overwrite", "rename", "skip"])
def test_preview_leaves_an_existing_skill_untouched(tmp_path, conflict):
    skills_import = _load_skills_import_module(tmp_path)
    installed = _installed_skill(skills_import, tmp_path)
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if "skill_imports" not in p.parts)

    skills_import.import_skills(
        str(_skill_pack(tmp_path, "new")), namespace="ns", conflict=conflict, dry_run=True
    )

    assert (installed / "local-notes.md").read_text() == "user edits"
    assert "old" in (installed / "SKILL.md").read_text()
    after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if "skill_imports" not in p.parts)
    assert after == before


def test_preview_reports_the_same_plan_the_import_then_applies(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    installed = _installed_skill(skills_import, tmp_path)
    archive_path = _skill_pack(tmp_path, "new")

    preview = skills_import.import_skills(
        str(archive_path), namespace="ns", conflict="overwrite", dry_run=True
    )
    applied = skills_import.import_skills(str(archive_path), namespace="ns", conflict="overwrite")

    assert preview.imported == applied.imported == [installed]
    assert preview.skipped == applied.skipped == []


def test_overwrite_import_replaces_the_existing_skill(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    installed = _installed_skill(skills_import, tmp_path)

    skills_import.import_skills(str(_skill_pack(tmp_path, "new")), namespace="ns", conflict="overwrite")

    assert "new" in (installed / "SKILL.md").read_text()
    assert not (installed / "local-notes.md").exists()


def test_rename_import_keeps_the_existing_skill_and_adds_a_copy(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    installed = _installed_skill(skills_import, tmp_path)

    result = skills_import.import_skills(str(_skill_pack(tmp_path, "new")), namespace="ns", conflict="rename")

    [renamed] = result.imported
    assert renamed == installed.with_name(f"{installed.name}_2")
    assert "new" in (renamed / "SKILL.md").read_text()
    assert (installed / "local-notes.md").read_text() == "user edits"
