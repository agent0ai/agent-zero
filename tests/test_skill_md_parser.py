"""Tests for SKILL.md YAML frontmatter parser."""

import pytest

from python.helpers.skill_md_parser import parse_skill_md, parse_skill_md_file


@pytest.mark.unit
class TestParseSkillMd:
    def test_valid_frontmatter_and_body(self):
        content = "---\nname: my-skill\nversion: '1.0'\n---\n# Hello\nBody text\n"
        fm, body = parse_skill_md(content)
        assert fm["name"] == "my-skill"
        assert fm["version"] == "1.0"
        assert "# Hello" in body

    def test_empty_input(self):
        fm, body = parse_skill_md("")
        assert fm == {}
        assert body == ""

    def test_none_input(self):
        fm, body = parse_skill_md(None)
        assert fm == {}
        assert body == ""

    def test_no_frontmatter(self):
        content = "# Just markdown\nNo frontmatter here."
        fm, body = parse_skill_md(content)
        assert fm == {}
        assert body == content

    def test_no_closing_delimiter(self):
        content = "---\nname: oops\nno closing"
        fm, body = parse_skill_md(content)
        assert fm == {}
        assert body == content

    def test_malformed_yaml(self):
        content = "---\n: : :\n  [invalid\n---\nBody"
        fm, body = parse_skill_md(content)
        assert fm == {}
        assert body == content

    def test_windows_line_endings(self):
        content = "---\r\nname: win\r\nversion: '1'\r\n---\r\n# Body\r\n"
        fm, _body = parse_skill_md(content)
        assert fm["name"] == "win"

    def test_list_values(self):
        content = "---\ncategories:\n  - web\n  - cli\n---\n# Body\n"
        fm, _body = parse_skill_md(content)
        assert fm["categories"] == ["web", "cli"]

    def test_empty_frontmatter_block(self):
        content = "---\n---\n# Body only\n"
        fm, body = parse_skill_md(content)
        assert fm == {}
        assert "# Body only" in body


@pytest.mark.unit
class TestParseSkillMdFile:
    def test_parse_file(self, tmp_path):
        f = tmp_path / "SKILL.md"
        f.write_text("---\nname: from-file\nversion: '2'\nauthor: test\n---\n# Doc\n")
        fm, body = parse_skill_md_file(str(f))
        assert fm["name"] == "from-file"
        assert "# Doc" in body

    def test_parse_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_skill_md_file("/nonexistent/SKILL.md")
