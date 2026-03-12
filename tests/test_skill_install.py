"""
Tests for SkillInstall: source parsing, skill discovery, and install flow.
Uses temp directories -- no real git clones or network access.

The methods under test (_parse_source, _find_skills) are extracted from
skill_install.py via AST to avoid pulling the full Agent Zero import chain.
"""
import ast
import os
import re
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SOURCE_FILE = PROJECT_ROOT / "python" / "api" / "skill_install.py"


def _extract_method(name: str):
    """Extract a method body from SkillInstall class and return a callable."""
    source = SOURCE_FILE.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "SkillInstall":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    code = ast.get_source_segment(source, item)
                    code = code.replace(f"def {name}(self,", f"def {name}(")
                    code = code.replace(f"def {name}(self)", f"def {name}()")
                    ns = {"__builtins__": __builtins__, "re": re, "os": os}
                    exec(compile(code, "<extract>", "exec"), ns)
                    return ns[name]

    raise ValueError(f"{name} not found in SkillInstall")


_parse_source = _extract_method("_parse_source")
_find_skills = _extract_method("_find_skills")
_normalize_skill_md = _extract_method("_normalize_skill_md")


# ---------------------------------------------------------------------------
# _parse_source
# ---------------------------------------------------------------------------

class TestParseSource:
    def test_owner_repo(self):
        owner, repo, skill = _parse_source("alice/my-skills")
        assert owner == "alice"
        assert repo == "my-skills"
        assert skill is None

    def test_owner_repo_skill(self):
        owner, repo, skill = _parse_source("alice/my-skills/coding-assistant")
        assert owner == "alice"
        assert repo == "my-skills"
        assert skill == "coding-assistant"

    def test_full_url(self):
        owner, repo, skill = _parse_source(
            "https://skills.sh/bob/agent-pack/launch-strategy"
        )
        assert owner == "bob"
        assert repo == "agent-pack"
        assert skill == "launch-strategy"

    def test_url_without_skill(self):
        owner, repo, skill = _parse_source(
            "https://skills.sh/bob/agent-pack"
        )
        assert owner == "bob"
        assert repo == "agent-pack"
        assert skill is None

    def test_www_url(self):
        owner, repo, skill = _parse_source(
            "https://www.skills.sh/org/repo/s1"
        )
        assert owner == "org"
        assert repo == "repo"
        assert skill == "s1"

    def test_http_url(self):
        owner, repo, skill = _parse_source(
            "http://skills.sh/alice/repo"
        )
        assert owner == "alice"
        assert repo == "repo"
        assert skill is None

    def test_trailing_slashes(self):
        owner, repo, skill = _parse_source("alice/repo/")
        assert owner == "alice"
        assert repo == "repo"
        assert skill is None

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="Expected format"):
            _parse_source("only-one-part")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Expected format"):
            _parse_source("")

    def test_invalid_owner_chars(self):
        with pytest.raises(ValueError, match="Invalid owner"):
            _parse_source("bad owner/repo")

    def test_invalid_repo_chars(self):
        with pytest.raises(ValueError, match="Invalid repo"):
            _parse_source("owner/bad repo")

    def test_dots_underscores_allowed(self):
        owner, repo, _ = _parse_source("my.org/my_repo-v2")
        assert owner == "my.org"
        assert repo == "my_repo-v2"

    def test_nested_skill_path(self):
        owner, repo, skill = _parse_source("alice/repo/subdir/deep-skill")
        assert owner == "alice"
        assert repo == "repo"
        assert skill == "subdir/deep-skill"


# ---------------------------------------------------------------------------
# _find_skills
# ---------------------------------------------------------------------------

class TestFindSkills:
    @staticmethod
    def _make_repo(structure: dict, base: str) -> str:
        for rel_path in structure:
            skill_dir = os.path.join(base, rel_path)
            os.makedirs(skill_dir, exist_ok=True)
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: test\n---\nTest skill\n")
        return base

    def test_single_skill(self, tmp_path):
        repo = self._make_repo({"coding": True}, str(tmp_path / "repo"))
        skills = _find_skills(repo)
        assert len(skills) == 1
        assert skills[0]["name"] == "coding"
        assert os.path.isfile(os.path.join(skills[0]["path"], "SKILL.md"))

    def test_multiple_skills(self, tmp_path):
        repo = self._make_repo({
            "skill-a": True,
            "skill-b": True,
            "nested/skill-c": True,
        }, str(tmp_path / "repo"))
        skills = _find_skills(repo)
        names = sorted(s["name"] for s in skills)
        assert names == ["skill-a", "skill-b", "skill-c"]

    def test_no_skills(self, tmp_path):
        repo = str(tmp_path / "empty-repo")
        os.makedirs(repo)
        skills = _find_skills(repo)
        assert skills == []

    def test_root_skill_gets_default_name(self, tmp_path):
        repo = str(tmp_path / "repo")
        os.makedirs(repo)
        with open(os.path.join(repo, "SKILL.md"), "w") as f:
            f.write("---\nname: root\n---\n")
        skills = _find_skills(repo)
        assert len(skills) == 1
        assert skills[0]["name"] == "default"

    def test_case_insensitive_filename(self, tmp_path):
        repo = str(tmp_path / "repo")
        skill_dir = os.path.join(repo, "my-skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "skill.md"), "w") as f:
            f.write("test")
        skills = _find_skills(repo)
        assert len(skills) == 1
        assert skills[0]["name"] == "my-skill"

    def test_original_filename_preserved(self, tmp_path):
        repo = str(tmp_path / "repo")
        skill_dir = os.path.join(repo, "my-skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "Skill.md"), "w") as f:
            f.write("test")
        skills = _find_skills(repo)
        assert skills[0]["original_filename"] == "Skill.md"

    def test_uppercase_filename_preserved(self, tmp_path):
        repo = str(tmp_path / "repo")
        skill_dir = os.path.join(repo, "my-skill")
        os.makedirs(skill_dir)
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write("test")
        skills = _find_skills(repo)
        assert skills[0]["original_filename"] == "SKILL.md"


# ---------------------------------------------------------------------------
# _normalize_skill_md
# ---------------------------------------------------------------------------

class TestNormalizeSkillMd:
    def test_renames_lowercase(self, tmp_path):
        dest = str(tmp_path / "skill-dir")
        os.makedirs(dest)
        with open(os.path.join(dest, "skill.md"), "w") as f:
            f.write("content")
        _normalize_skill_md(dest, "skill.md")
        assert os.path.isfile(os.path.join(dest, "SKILL.md"))
        actual_names = os.listdir(dest)
        assert "SKILL.md" in actual_names

    def test_skips_already_uppercase(self, tmp_path):
        dest = str(tmp_path / "skill-dir")
        os.makedirs(dest)
        with open(os.path.join(dest, "SKILL.md"), "w") as f:
            f.write("content")
        _normalize_skill_md(dest, "SKILL.md")
        assert os.path.isfile(os.path.join(dest, "SKILL.md"))

    def test_renames_mixed_case(self, tmp_path):
        dest = str(tmp_path / "skill-dir")
        os.makedirs(dest)
        with open(os.path.join(dest, "Skill.MD"), "w") as f:
            f.write("content")
        _normalize_skill_md(dest, "Skill.MD")
        assert os.path.isfile(os.path.join(dest, "SKILL.md"))


# ---------------------------------------------------------------------------
# Integration: install flow with filesystem (no git)
# ---------------------------------------------------------------------------

class TestInstallFlow:
    @staticmethod
    def _fake_clone(base_dir, skills_dict):
        repo_dir = os.path.join(base_dir, "fake-repo")
        os.makedirs(repo_dir)
        for name, content in skills_dict.items():
            skill_dir = os.path.join(repo_dir, name)
            os.makedirs(skill_dir)
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write(content or "---\nname: test\n---\n")
        return repo_dir

    def test_copies_skills(self, tmp_path):
        clone_dir = self._fake_clone(str(tmp_path / "clone"), {
            "skill-a": "# Skill A",
            "skill-b": "# Skill B",
        })
        target = str(tmp_path / "target")
        os.makedirs(target)

        skills = _find_skills(clone_dir)
        installed = []
        for skill in skills:
            dest = os.path.join(target, skill["name"])
            shutil.copytree(skill["path"], dest)
            installed.append(skill["name"])

        assert sorted(installed) == ["skill-a", "skill-b"]
        assert os.path.isfile(os.path.join(target, "skill-a", "SKILL.md"))
        assert os.path.isfile(os.path.join(target, "skill-b", "SKILL.md"))

    def test_skip_existing(self, tmp_path):
        target = str(tmp_path / "target")
        os.makedirs(os.path.join(target, "existing-skill"))
        with open(os.path.join(target, "existing-skill", "SKILL.md"), "w") as f:
            f.write("old")

        clone_dir = self._fake_clone(str(tmp_path / "clone"), {
            "existing-skill": "new content",
            "new-skill": "brand new",
        })

        skills = _find_skills(clone_dir)
        installed, skipped = [], []
        for skill in skills:
            dest = os.path.join(target, skill["name"])
            if os.path.exists(dest):
                skipped.append(skill["name"])
            else:
                shutil.copytree(skill["path"], dest)
                installed.append(skill["name"])

        assert installed == ["new-skill"]
        assert skipped == ["existing-skill"]
        with open(os.path.join(target, "existing-skill", "SKILL.md")) as f:
            assert f.read() == "old"

    def test_filter_by_name(self, tmp_path):
        clone_dir = self._fake_clone(str(tmp_path / "clone"), {
            "alpha": "A",
            "beta": "B",
            "gamma": "C",
        })
        all_skills = _find_skills(clone_dir)
        filtered = [s for s in all_skills if s["name"].lower() == "beta"]
        assert len(filtered) == 1
        assert filtered[0]["name"] == "beta"
