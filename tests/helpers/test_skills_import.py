"""Tests for python/helpers/skills_import.py."""

import sys
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def tmp_skills_source(tmp_path):
    """Create a source dir with a skill."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: Test\n---\n\nContent"
    )
    return tmp_path, skills_dir


@pytest.fixture
def patch_files_and_skills(tmp_path):
    """Patch files.get_abs_path and skills.discover_skill_md_files."""
    with patch("python.helpers.skills_import.files") as mock_files:
        mock_files.get_abs_path.side_effect = lambda *parts: str(
            tmp_path.joinpath(*[str(p) for p in parts])
        )
        with patch(
            "python.helpers.skills_import.discover_skill_md_files"
        ) as mock_discover:
            yield mock_files, mock_discover, tmp_path


# --- _is_within ---


class TestIsWithin:
    def test_child_inside_parent(self, tmp_path):
        from python.helpers.skills_import import _is_within

        parent = tmp_path / "a" / "b"
        parent.mkdir(parents=True)
        child = parent / "c" / "file"
        child.parent.mkdir(parents=True)
        child.touch()
        assert _is_within(child, parent) is True

    def test_child_outside_parent(self, tmp_path):
        from python.helpers.skills_import import _is_within

        parent = tmp_path / "a" / "b"
        parent.mkdir(parents=True)
        child = tmp_path / "x" / "y"
        child.mkdir(parents=True)
        assert _is_within(child, parent) is False


# --- _derive_namespace ---


class TestDeriveNamespace:
    def test_zip_stem(self):
        from python.helpers.skills_import import _derive_namespace

        assert _derive_namespace(Path("/x/repo.zip")) == "repo"

    def test_dir_name(self):
        from python.helpers.skills_import import _derive_namespace

        assert _derive_namespace(Path("/x/my-repo")) == "my-repo"


# --- _resolve_conflict ---


class TestResolveConflict:
    def test_nonexistent_returns_copy_true(self):
        from python.helpers.skills_import import _resolve_conflict

        dest = Path("/nonexistent/path")
        result, should_copy = _resolve_conflict(dest, "skip")
        assert should_copy is True

    def test_skip_policy_returns_false_when_exists(self, tmp_path):
        from python.helpers.skills_import import _resolve_conflict

        (tmp_path / "exists").mkdir()
        _, should_copy = _resolve_conflict(tmp_path / "exists", "skip")
        assert should_copy is False

    def test_overwrite_policy_removes_existing(self, tmp_path):
        from python.helpers.skills_import import _resolve_conflict

        existing = tmp_path / "existing"
        existing.mkdir()
        (existing / "file.txt").write_text("x")
        result, should_copy = _resolve_conflict(existing, "overwrite")
        assert should_copy is True
        assert not existing.exists()

    def test_rename_policy_creates_new_name(self, tmp_path):
        from python.helpers.skills_import import _resolve_conflict

        (tmp_path / "skill").mkdir()
        result, should_copy = _resolve_conflict(tmp_path / "skill", "rename")
        assert should_copy is True
        assert result.name == "skill_2"


# --- build_import_plan ---


class TestBuildImportPlan:
    def test_builds_plan_from_skill_dirs(self, tmp_skills_source, patch_files_and_skills):
        from python.helpers.skills_import import build_import_plan

        src_root, skills_dir = tmp_skills_source
        mock_files, mock_discover, tmp_path = patch_files_and_skills
        dest_root = tmp_path / "usr" / "skills"
        dest_root.mkdir(parents=True)

        mock_discover.return_value = [skills_dir / "my-skill" / "SKILL.md"]

        plan, root_used = build_import_plan(skills_dir, dest_root)

        assert len(plan) == 1
        assert plan[0].src_skill_dir.name == "my-skill"
        assert "my-skill" in str(plan[0].dest_skill_dir)

    def test_skips_skills_already_in_dest(self, tmp_path, patch_files_and_skills):
        from python.helpers.skills_import import build_import_plan

        mock_files, mock_discover, tmp_path = patch_files_and_skills
        dest_root = tmp_path / "dest"
        dest_root.mkdir()
        skill_in_dest = dest_root / "existing" / "SKILL.md"
        skill_in_dest.parent.mkdir(parents=True)
        skill_in_dest.write_text("x")

        mock_discover.return_value = [skill_in_dest]

        plan, _ = build_import_plan(dest_root, dest_root)

        assert len(plan) == 0


# --- resolve_skills_destination_root ---


class TestResolveSkillsDestinationRoot:
    def test_project_and_profile(self):
        from python.helpers.skills_import import resolve_skills_destination_root

        with patch(
            "python.helpers.skills_import.get_project_agent_profile_skills_folder"
        ) as mock_get:
            mock_get.return_value = Path("/proj/agent/skills")
            result = resolve_skills_destination_root("proj", "agent")
            assert result == Path("/proj/agent/skills")
            mock_get.assert_called_once_with("proj", "agent")

    def test_project_only(self):
        from python.helpers.skills_import import resolve_skills_destination_root

        with patch(
            "python.helpers.skills_import.get_project_skills_folder"
        ) as mock_get:
            mock_get.return_value = Path("/proj/skills")
            result = resolve_skills_destination_root("proj", None)
            assert result == Path("/proj/skills")

    def test_profile_only(self):
        from python.helpers.skills_import import resolve_skills_destination_root

        with patch(
            "python.helpers.skills_import.get_agent_profile_skills_folder"
        ) as mock_get:
            mock_get.return_value = Path("/agent/skills")
            result = resolve_skills_destination_root(None, "agent")
            assert result == Path("/agent/skills")

    def test_default_usr_skills(self):
        from python.helpers.skills_import import resolve_skills_destination_root

        with patch("python.helpers.skills_import.files") as mock_files:
            mock_files.get_abs_path.return_value = "/usr/skills"
            result = resolve_skills_destination_root(None, None)
            assert "skills" in str(result)


# --- import_skills ---


class TestImportSkills:
    def test_raises_when_source_not_found(self, patch_files_and_skills):
        from python.helpers.skills_import import import_skills

        mock_files, mock_discover, tmp_path = patch_files_and_skills

        with pytest.raises(FileNotFoundError, match="not found"):
            import_skills("/nonexistent/path")

    def test_raises_for_non_dir_non_zip(self, tmp_path, patch_files_and_skills):
        from python.helpers.skills_import import import_skills

        mock_files, mock_discover, tmp_path = patch_files_and_skills
        (tmp_path / "file.txt").write_text("x")

        with pytest.raises(ValueError, match="directory or .zip"):
            import_skills(str(tmp_path / "file.txt"))

    def test_imports_from_directory(self, tmp_skills_source, patch_files_and_skills):
        from python.helpers.skills_import import import_skills

        src_root, skills_dir = tmp_skills_source
        mock_files, mock_discover, tmp_path = patch_files_and_skills
        dest_root = tmp_path / "usr" / "skills"
        dest_root.mkdir(parents=True)

        skill_md = skills_dir / "my-skill" / "SKILL.md"
        mock_discover.return_value = [skill_md]

        result = import_skills(
            str(skills_dir),
            namespace="test",
            conflict="overwrite",
        )

        assert len(result.imported) == 1
        assert result.namespace == "test"
        assert result.source_root == skills_dir

    def test_dry_run_does_not_copy(self, tmp_skills_source, patch_files_and_skills):
        from python.helpers.skills_import import import_skills

        src_root, skills_dir = tmp_skills_source
        mock_files, mock_discover, tmp_path = patch_files_and_skills
        dest_root = tmp_path / "usr" / "skills"
        dest_root.mkdir(parents=True)

        mock_discover.return_value = [skills_dir / "my-skill" / "SKILL.md"]

        result = import_skills(
            str(skills_dir),
            namespace="dry",
            dry_run=True,
        )

        assert len(result.imported) == 1
        # In dry run, imported contains paths that would be created
        assert not (dest_root / "dry" / "my-skill").exists()
