"""Tests for python/helpers/skills_cli.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def patch_files(tmp_path):
    """Patch files.get_abs_path for skills dirs."""
    skills_base = tmp_path / "usr" / "skills"
    (skills_base / "custom").mkdir(parents=True)
    (skills_base / "default").mkdir(parents=True)

    with patch("python.helpers.skills_cli.files") as mock_files:
        mock_files.get_abs_path.side_effect = lambda *parts: str(
            tmp_path.joinpath(*[str(p) for p in parts])
        )
        yield mock_files, tmp_path


# --- get_skills_dirs ---


class TestGetSkillsDirs:
    def test_returns_custom_and_default(self, patch_files):
        from python.helpers.skills_cli import get_skills_dirs

        mock_files, tmp_path = patch_files
        mock_files.get_abs_path.return_value = str(tmp_path / "usr" / "skills")

        dirs = get_skills_dirs()
        assert len(dirs) == 2
        assert any("custom" in str(d) for d in dirs)
        assert any("default" in str(d) for d in dirs)


# --- parse_skill_file ---


class TestParseSkillFile:
    def test_returns_none_for_no_frontmatter(self, tmp_path):
        from python.helpers.skills_cli import parse_skill_file

        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("Just body content")

        result = parse_skill_file(skill_file)
        assert result is None

    def test_parses_valid_frontmatter(self, tmp_path):
        from python.helpers.skills_cli import parse_skill_file

        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            """---
name: "test-skill"
description: "A test skill for unit testing"
version: "1.0.0"
author: "Tester"
tags: ["custom", "test"]
trigger_patterns: ["test"]
---

# Test Skill

Body content here with at least 100 characters to satisfy validation requirements.
"""
        )

        result = parse_skill_file(skill_file)
        assert result is not None
        assert result.name == "test-skill"
        assert result.description == "A test skill for unit testing"
        assert result.version == "1.0.0"
        assert result.path == tmp_path
        assert "Body content" in result.content


# --- validate_skill ---


class TestValidateSkill:
    def test_missing_name(self):
        from python.helpers.skills_cli import validate_skill, Skill

        skill = Skill(name="", description="x" * 20, path=Path("/x"), content="x" * 100)
        issues = validate_skill(skill)
        assert any("name" in i.lower() for i in issues)

    def test_missing_description(self):
        from python.helpers.skills_cli import validate_skill, Skill

        skill = Skill(name="valid", description="", path=Path("/x"), content="x" * 100)
        issues = validate_skill(skill)
        assert any("description" in i.lower() for i in issues)

    def test_invalid_name_format(self):
        from python.helpers.skills_cli import validate_skill, Skill

        skill = Skill(
            name="InvalidName",
            description="A valid description here",
            path=Path("/x"),
            content="x" * 100,
        )
        issues = validate_skill(skill)
        assert any("name" in i.lower() or "format" in i.lower() for i in issues)

    def test_content_too_short(self):
        from python.helpers.skills_cli import validate_skill, Skill

        skill = Skill(
            name="valid-skill",
            description="A valid description here",
            path=Path("/x"),
            content="short",
        )
        issues = validate_skill(skill)
        assert any("content" in i.lower() or "100" in i for i in issues)

    def test_valid_skill_returns_empty_issues(self):
        from python.helpers.skills_cli import validate_skill, Skill

        skill = Skill(
            name="valid-skill",
            description="A valid description with at least twenty chars",
            path=Path("/x"),
            content="x" * 100,
        )
        issues = validate_skill(skill)
        assert issues == []


# --- search_skills ---


class TestSearchSkills:
    def test_matches_by_name(self):
        from python.helpers.skills_cli import search_skills, Skill

        with patch("python.helpers.skills_cli.list_skills") as mock_list:
            mock_list.return_value = [
                Skill(
                    name="python-skill",
                    description="Python stuff",
                    path=Path("/x"),
                    content="",
                ),
            ]
            results = search_skills("python")
            assert len(results) == 1
            assert results[0].name == "python-skill"

    def test_matches_by_tag(self):
        from python.helpers.skills_cli import search_skills, Skill

        with patch("python.helpers.skills_cli.list_skills") as mock_list:
            mock_list.return_value = [
                Skill(
                    name="x",
                    description="",
                    path=Path("/x"),
                    content="",
                    tags=["automation"],
                ),
            ]
            results = search_skills("automation")
            assert len(results) == 1


# --- create_skill ---


class TestCreateSkill:
    def test_creates_skill_directory_structure(self, patch_files):
        from python.helpers.skills_cli import create_skill

        mock_files, tmp_path = patch_files
        custom_dir = tmp_path / "usr" / "skills" / "custom"
        mock_files.get_abs_path.side_effect = lambda *args: str(
            tmp_path / "usr" / "skills" / "custom"
            if args == ("usr", "skills", "custom")
            else tmp_path / "usr" / "skills"
        )

        result = create_skill("my-new-skill", description="Test desc", author="Me")

        assert result.exists()
        assert (result / "SKILL.md").exists()
        assert (result / "scripts").exists()
        assert (result / "docs").exists()
        assert (result / "docs" / "README.md").exists()

    def test_raises_when_skill_exists(self, patch_files):
        from python.helpers.skills_cli import create_skill

        mock_files, tmp_path = patch_files
        (tmp_path / "usr" / "skills" / "custom" / "existing").mkdir(parents=True)

        with pytest.raises(ValueError, match="already exists"):
            create_skill("existing")


# --- find_skill ---


class TestFindSkill:
    def test_finds_by_name(self):
        from python.helpers.skills_cli import find_skill, Skill

        with patch("python.helpers.skills_cli.list_skills") as mock_list:
            skill = Skill(
                name="target",
                description="",
                path=Path("/x/target"),
                content="",
            )
            mock_list.return_value = [skill]
            result = find_skill("target")
            assert result is not None
            assert result.name == "target"

    def test_returns_none_when_not_found(self):
        from python.helpers.skills_cli import find_skill

        with patch("python.helpers.skills_cli.list_skills", return_value=[]):
            assert find_skill("nonexistent") is None


# --- print_skill_table ---


class TestPrintSkillTable:
    def test_prints_no_skills_message(self, capsys):
        from python.helpers.skills_cli import print_skill_table

        print_skill_table([])
        out = capsys.readouterr().out
        assert "No skills" in out

    def test_prints_table_with_skills(self, capsys):
        from python.helpers.skills_cli import print_skill_table, Skill

        skills = [
            Skill(
                name="a",
                description="Desc A",
                path=Path("/x"),
                version="1.0",
                tags=["t1"],
                content="",
            ),
        ]
        print_skill_table(skills)
        out = capsys.readouterr().out
        assert "a" in out
        assert "Desc A" in out
        assert "1.0" in out
