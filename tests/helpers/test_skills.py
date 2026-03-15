"""Tests for python/helpers/skills.py — skill discovery, loading, installation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- get_skills_base_dir ---

class TestGetSkillsBaseDir:
    def test_returns_path_with_usr_skills(self):
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.get_abs_path.return_value = "/a0/usr/skills"
            from python.helpers.skills import get_skills_base_dir
            result = get_skills_base_dir()
            assert "skills" in str(result)
            mock_files.get_abs_path.assert_called_with("usr", "skills")


# --- get_skill_roots ---

class TestGetSkillRoots:
    def test_global_roots_without_agent(self):
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.get_abs_path.side_effect = lambda *p: "/a0/" + "/".join(str(x) for x in p)
            mock_files.find_existing_paths_by_pattern.return_value = []
            from python.helpers.skills import get_skill_roots
            roots = get_skill_roots(agent=None)
            assert mock_files.get_abs_path.called
            assert any("skills" in str(r) for r in roots)

    def test_agent_roots_with_agent(self, mock_agent):
        with patch("python.helpers.skills.subagents") as mock_subagents:
            mock_subagents.get_paths.return_value = ["/a0/agents/some/skills"]
            from python.helpers.skills import get_skill_roots
            roots = get_skill_roots(agent=mock_agent)
            mock_subagents.get_paths.assert_called_once_with(mock_agent, "skills")
            assert roots == ["/a0/agents/some/skills"]


# --- _is_hidden_path ---

class TestIsHiddenPath:
    def test_dot_folder_hidden(self):
        from python.helpers.skills import _is_hidden_path
        assert _is_hidden_path(Path(".git/config")) is True

    def test_visible_path_not_hidden(self):
        from python.helpers.skills import _is_hidden_path
        assert _is_hidden_path(Path("usr/skills/foo/SKILL.md")) is False

    def test_nested_dot_hidden(self):
        from python.helpers.skills import _is_hidden_path
        assert _is_hidden_path(Path("a/.b/c")) is True


# --- discover_skill_md_files ---

class TestDiscoverSkillMdFiles:
    def test_empty_when_root_not_exists(self):
        from python.helpers.skills import discover_skill_md_files
        result = discover_skill_md_files(Path("/nonexistent/path"))
        assert result == []

    def test_finds_skill_md_in_root(self, tmp_workdir):
        from python.helpers.skills import discover_skill_md_files
        skill_dir = tmp_workdir / "skill1"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\nbody")
        result = discover_skill_md_files(tmp_workdir)
        assert len(result) == 1
        assert result[0].name == "SKILL.md"

    def test_ignores_hidden_folders(self, tmp_workdir):
        from python.helpers.skills import discover_skill_md_files
        hidden = tmp_workdir / ".hidden"
        hidden.mkdir()
        (hidden / "SKILL.md").write_text("---\nname: hidden\n---\n")
        result = discover_skill_md_files(tmp_workdir)
        assert len(result) == 0

    def test_returns_sorted_paths(self, tmp_workdir):
        from python.helpers.skills import discover_skill_md_files
        for name in ["z", "a", "m"]:
            d = tmp_workdir / name
            d.mkdir()
            (d / "SKILL.md").write_text("---\nname: x\n---\n")
        result = discover_skill_md_files(tmp_workdir)
        paths = [str(p) for p in result]
        assert paths == sorted(paths)


# --- _coerce_list ---

class TestCoerceList:
    def test_none_returns_empty(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list(None) == []

    def test_list_passthrough(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list(["a", "b"]) == ["a", "b"]

    def test_comma_separated_string(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list("a, b, c") == ["a", "b", "c"]

    def test_space_separated_string(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list("a b c") == ["a", "b", "c"]

    def test_tuple_converted(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list(("x", "y")) == ["x", "y"]

    def test_empty_strings_filtered(self):
        from python.helpers.skills import _coerce_list
        assert _coerce_list(["a", "", "b"]) == ["a", "b"]


# --- _normalize_name ---

class TestNormalizeName:
    def test_lowercase_and_hyphens(self):
        from python.helpers.skills import _normalize_name
        assert _normalize_name("My Skill Name") == "my-skill-name"

    def test_strips_whitespace(self):
        from python.helpers.skills import _normalize_name
        assert _normalize_name("  foo  ") == "foo"


# --- split_frontmatter ---

class TestSplitFrontmatter:
    def test_valid_frontmatter(self):
        from python.helpers.skills import split_frontmatter
        text = "---\nname: test\ndescription: desc\n---\n\nBody content"
        fm, body, errors = split_frontmatter(text)
        assert errors == []
        assert fm.get("name") == "test"
        assert fm.get("description") == "desc"
        assert "Body content" in body

    def test_missing_frontmatter(self):
        from python.helpers.skills import split_frontmatter
        text = "No frontmatter here"
        fm, body, errors = split_frontmatter(text)
        assert "Missing YAML frontmatter" in errors

    def test_unterminated_frontmatter(self):
        from python.helpers.skills import split_frontmatter
        text = "---\nname: test\nBody without closing"
        fm, body, errors = split_frontmatter(text)
        assert "Unterminated" in errors[0]

    def test_content_before_fence_invalid(self):
        from python.helpers.skills import split_frontmatter
        text = "Some text\n---\nname: test\n---\nbody"
        fm, body, errors = split_frontmatter(text)
        assert "must start at the top" in errors[0]


# --- parse_frontmatter ---

class TestParseFrontmatter:
    def test_empty_returns_empty_dict(self):
        from python.helpers.skills import parse_frontmatter
        result, errors = parse_frontmatter("")
        assert result == {}
        assert errors == []

    def test_simple_key_value(self):
        from python.helpers.skills import parse_frontmatter
        result, errors = parse_frontmatter("name: test\ndescription: desc")
        assert result.get("name") == "test"
        assert result.get("description") == "desc"
        assert errors == []

    def test_list_syntax(self):
        from python.helpers.skills import parse_frontmatter
        result, errors = parse_frontmatter("tags:\n  - a\n  - b")
        assert "tags" in result
        assert result["tags"] in ([["a", "b"]], ["a", "b"])  # yaml or fallback


# --- skill_from_markdown ---

class TestSkillFromMarkdown:
    def test_valid_skill_parsed(self, tmp_workdir):
        from python.helpers.skills import skill_from_markdown
        skill_md = tmp_workdir / "SKILL.md"
        skill_md.write_text("""---
name: my-skill
description: A test skill
---
Body content here.
""")
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            skill = skill_from_markdown(skill_md)
            assert skill is not None
            assert skill.name == "my-skill"
            assert skill.description == "A test skill"

    def test_skill_returns_none_when_invalid(self, tmp_workdir):
        from python.helpers.skills import skill_from_markdown
        skill_md = tmp_workdir / "SKILL.md"
        skill_md.write_text("No frontmatter")
        skill = skill_from_markdown(skill_md)
        assert skill is None

    def test_skill_returns_none_when_invalid_name(self, tmp_workdir):
        from python.helpers.skills import skill_from_markdown
        skill_md = tmp_workdir / "SKILL.md"
        skill_md.write_text("""---
name: Invalid Name!
description: Bad
---
""")
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            skill = skill_from_markdown(skill_md)
            assert skill is None

    def test_include_content_populates_body(self, tmp_workdir):
        from python.helpers.skills import skill_from_markdown
        skill_md = tmp_workdir / "SKILL.md"
        skill_md.write_text("""---
name: my-skill
description: A test
---
Body content here.
""")
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            skill = skill_from_markdown(skill_md, include_content=True)
            assert skill is not None
            assert "Body content" in skill.content


# --- list_skills ---

class TestListSkills:
    def test_empty_when_no_roots(self):
        with patch("python.helpers.skills.get_skill_roots", return_value=[]):
            from python.helpers.skills import list_skills
            assert list_skills() == []

    def test_finds_skills_from_roots(self, tmp_workdir):
        skill_dir = tmp_workdir / "skill1"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: x\n---\n")
        with (
            patch("python.helpers.skills.get_skill_roots", return_value=[str(tmp_workdir)]),
            patch("python.helpers.skills.files") as mock_files,
        ):
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            from python.helpers.skills import list_skills
            skills = list_skills()
            assert len(skills) >= 1
            names = [s.name for s in skills]
            assert "test-skill" in names or any("test" in n for n in names)


# --- find_skill ---

class TestFindSkill:
    def test_returns_none_for_empty_name(self):
        with patch("python.helpers.skills.get_skill_roots", return_value=[]):
            from python.helpers.skills import find_skill
            assert find_skill("") is None
            assert find_skill("   ") is None

    def test_finds_skill_by_name(self, tmp_workdir):
        skill_dir = tmp_workdir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\ndescription: x\n---\n")
        with (
            patch("python.helpers.skills.get_skill_roots", return_value=[str(tmp_workdir)]),
            patch("python.helpers.skills.files") as mock_files,
        ):
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            from python.helpers.skills import find_skill
            skill = find_skill("my-skill")
            assert skill is not None
            assert skill.name == "my-skill"


# --- delete_skill ---

class TestDeleteSkill:
    def test_raises_when_root_not_in_scope(self):
        with (
            patch("python.helpers.skills.get_skill_roots", return_value=["/allowed/root"]),
            patch("python.helpers.skills.files") as mock_files,
        ):
            mock_files.get_abs_path.side_effect = lambda *p: "/other/path/skill"
            mock_files.is_in_dir.return_value = False
            from python.helpers.skills import delete_skill
            with pytest.raises(ValueError, match="not in current scope"):
                delete_skill("skill")

    def test_raises_when_directory_not_found(self):
        with (
            patch("python.helpers.skills.get_skill_roots", return_value=["/root"]),
            patch("python.helpers.skills.files") as mock_files,
            patch("python.helpers.skills.runtime") as mock_runtime,
        ):
            mock_files.get_abs_path.side_effect = lambda *p: "/root/skill"
            mock_files.is_in_dir.return_value = True
            mock_runtime.is_development.return_value = False
            from python.helpers.skills import delete_skill
            with pytest.raises(FileNotFoundError, match="not found"):
                delete_skill("skill")


# --- load_skill_for_agent ---

class TestLoadSkillForAgent:
    def test_returns_error_when_not_found(self):
        with patch("python.helpers.skills.find_skill", return_value=None):
            from python.helpers.skills import load_skill_for_agent
            result = load_skill_for_agent("nonexistent")
            assert "not found" in result

    def test_returns_formatted_skill_when_found(self):
        from python.helpers.skills import Skill, load_skill_for_agent
        skill = Skill(
            name="test-skill",
            description="A test",
            path=Path("/a/skill"),
            skill_md_path=Path("/a/skill/SKILL.md"),
            content="Body content",
        )
        with (
            patch("python.helpers.skills.find_skill", return_value=skill),
            patch("python.helpers.skills.runtime") as mock_runtime,
            patch("python.helpers.skills._get_skill_files", return_value=""),
        ):
            mock_runtime.is_development.return_value = False
            from python.helpers.skills import load_skill_for_agent
            result = load_skill_for_agent("test-skill")
            assert "test-skill" in result
            assert "Body content" in result


# --- search_skills ---

class TestSearchSkills:
    def test_empty_query_returns_empty(self):
        with patch("python.helpers.skills.list_skills", return_value=[]):
            from python.helpers.skills import search_skills
            assert search_skills("") == []
            assert search_skills("   ") == []

    def test_scores_by_name_match(self):
        from python.helpers.skills import Skill, search_skills
        skills = [
            Skill("foo-bar", "desc", Path("/a"), Path("/a/SKILL.md")),
            Skill("other", "desc", Path("/b"), Path("/b/SKILL.md")),
        ]
        with patch("python.helpers.skills.list_skills", return_value=skills):
            result = search_skills("foo")
            assert len(result) >= 1
            if result:
                assert "foo" in result[0].name.lower()


# --- validate_skill ---

class TestValidateSkill:
    def test_missing_name(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("", "desc", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert "Missing required field: name" in issues

    def test_missing_description(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("valid-name", "", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert "Missing required field: description" in issues

    def test_name_too_short_or_long(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("a" * 65, "desc", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert "1-64" in str(issues)

    def test_name_invalid_chars(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("Invalid!", "desc", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert any("lowercase" in i or "hyphens" in i for i in issues)

    def test_name_starts_with_hyphen(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("-bad", "desc", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert any("hyphen" in i for i in issues)

    def test_valid_skill_no_issues(self):
        from python.helpers.skills import validate_skill, Skill
        skill = Skill("valid-skill", "A description", Path("/x"), Path("/x/SKILL.md"))
        issues = validate_skill(skill)
        assert issues == []


# --- validate_skill_md ---

class TestValidateSkillMd:
    def test_unreadable_file(self):
        from python.helpers.skills import validate_skill_md
        issues = validate_skill_md(Path("/nonexistent/SKILL.md"))
        assert "Unable to read" in issues[0]

    def test_valid_skill_md_returns_empty(self, tmp_workdir):
        skill_dir = tmp_workdir / "skill-dir"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: valid-skill\ndescription: x\n---\n")
        with patch("python.helpers.skills.files") as mock_files:
            mock_files.normalize_a0_path.side_effect = lambda x: str(Path(x))
            from python.helpers.skills import validate_skill_md
            issues = validate_skill_md(skill_md)
            assert issues == []
