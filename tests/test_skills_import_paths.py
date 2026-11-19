import zipfile
from pathlib import Path

import pytest

from test_skills_scan import _load_skills_import_module


def _skill_pack(tmp_path: Path) -> Path:
    archive_path = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("probe/SKILL.md", "---\nname: probe\ndescription: probe\n---\nprobe\n")
        archive.writestr("probe/evil.py", "PROOF = True\n")
    return archive_path


@pytest.mark.parametrize(
    "namespace",
    ["../api/leadprobe", "..", ".", "a/b", "a\\b", "/abs", "..\\api"],
)
def test_import_skills_rejects_namespace_that_is_not_one_directory(tmp_path, namespace):
    skills_import = _load_skills_import_module(tmp_path)

    with pytest.raises(ValueError, match="Invalid namespace"):
        skills_import.import_skills(
            str(_skill_pack(tmp_path)), namespace=namespace, conflict="overwrite"
        )

    assert not (tmp_path / "usr" / "api").exists()
    assert not (tmp_path / "usr" / "skills").exists()


def test_traversing_namespace_cannot_overwrite_a_directory_outside_skills(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    victim = tmp_path / "usr" / "api" / "leadprobe" / "probe"
    victim.mkdir(parents=True)
    (victim / "keep.txt").write_text("keep")

    with pytest.raises(ValueError):
        skills_import.import_skills(
            str(_skill_pack(tmp_path)), namespace="../api/leadprobe", conflict="overwrite"
        )

    assert (victim / "keep.txt").read_text() == "keep"
    assert not (victim / "evil.py").exists()


@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize(
    "scope",
    [
        {"agent_profile": "../../api"},
        {"agent_profile": ".."},
        {"project_name": "../outside"},
        {"project_name": "ok", "agent_profile": "../../../api"},
    ],
)
def test_import_skills_rejects_traversing_scope_before_creating_anything(tmp_path, scope, dry_run):
    skills_import = _load_skills_import_module(tmp_path)
    archive_path = _skill_pack(tmp_path)
    before = sorted(p for p in tmp_path.rglob("*"))

    with pytest.raises(ValueError, match="Invalid (project name|agent profile)"):
        skills_import.import_skills(str(archive_path), dry_run=dry_run, **scope)

    assert sorted(p for p in tmp_path.rglob("*")) == before


def test_build_import_plan_rejects_traversing_namespace(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    source = tmp_path / "src"
    (source / "probe").mkdir(parents=True)
    (source / "probe" / "SKILL.md").write_text("---\nname: probe\n---\n")

    with pytest.raises(ValueError, match="Invalid namespace"):
        skills_import.build_import_plan(source, tmp_path / "dest", namespace="../escape")


def test_import_skills_keeps_valid_namespace_and_scopes(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    archive_path = _skill_pack(tmp_path)

    result = skills_import.import_skills(str(archive_path), namespace="  my-pack.v2_1  ")
    assert result.namespace == "my-pack.v2_1"
    [imported] = result.imported
    assert imported.is_relative_to(tmp_path / "usr" / "skills" / "my-pack.v2_1")
    assert (imported / "SKILL.md").is_file()

    result = skills_import.import_skills(str(archive_path), agent_profile="researcher")
    assert result.destination_root == tmp_path / "usr" / "agents" / "researcher" / "skills"
    [imported] = result.imported
    assert imported.is_relative_to(result.destination_root / "pack")
    assert (imported / "SKILL.md").is_file()


def test_missing_or_blank_namespace_keeps_existing_fallbacks(tmp_path):
    skills_import = _load_skills_import_module(tmp_path)
    archive_path = _skill_pack(tmp_path)

    assert skills_import.import_skills(str(archive_path), dry_run=True).namespace == "pack"
    assert (
        skills_import.import_skills(str(archive_path), namespace="   ", dry_run=True).namespace
        == "import"
    )
