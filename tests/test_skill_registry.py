"""Tests for SkillRegistry CRUD, search, and scan."""

import pytest

from python.helpers.skill_registry import SkillManifest, SkillRegistry, get_registry


def _make_manifest(name: str = "test-skill", **kwargs) -> SkillManifest:
    defaults = {
        "name": name,
        "version": "1.0.0",
        "author": "tester",
        "tier": 1,
        "trust_level": "community",
    }
    defaults.update(kwargs)
    return SkillManifest(**defaults)


@pytest.mark.unit
class TestSkillRegistry:
    def test_install_and_get(self):
        reg = SkillRegistry()
        m = _make_manifest("alpha")
        reg.install(m)
        assert reg.get("alpha") is not None
        assert reg.get("alpha").version == "1.0.0"

    def test_install_sets_installed_at(self):
        reg = SkillRegistry()
        m = _make_manifest("beta")
        assert m.installed_at is None
        reg.install(m)
        assert m.installed_at is not None

    def test_uninstall(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("gamma"))
        reg.uninstall("gamma")
        assert reg.get("gamma") is None

    def test_uninstall_missing_is_noop(self):
        reg = SkillRegistry()
        reg.uninstall("nonexistent")  # should not raise

    def test_enable_disable(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("delta"))
        reg.disable("delta")
        assert reg.get("delta").enabled is False
        reg.enable("delta")
        assert reg.get("delta").enabled is True

    def test_list_all(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("a"))
        reg.install(_make_manifest("b"))
        assert len(reg.list()) == 2

    def test_list_by_category(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("a", categories=["web"]))
        reg.install(_make_manifest("b", categories=["cli"]))
        assert len(reg.list(category="web")) == 1
        assert reg.list(category="web")[0].name == "a"

    def test_search(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("weather-skill", description="Get weather data"))
        reg.install(_make_manifest("music-skill", description="Play music"))
        results = reg.search("weather")
        assert len(results) == 1
        assert results[0].name == "weather-skill"

    def test_search_case_insensitive(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("MySkill", description="does things"))
        assert len(reg.search("myskill")) == 1

    def test_check_dependencies_all_met(self):
        reg = SkillRegistry()
        reg.install(_make_manifest("base"))
        m = _make_manifest("child", dependencies=["base"])
        assert reg.check_dependencies(m) == []

    def test_check_dependencies_missing(self):
        reg = SkillRegistry()
        m = _make_manifest("child", dependencies=["missing-dep"])
        assert reg.check_dependencies(m) == ["missing-dep"]

    def test_to_dict(self):
        m = _make_manifest("x", description="desc")
        d = m.to_dict()
        assert d["name"] == "x"
        assert d["description"] == "desc"
        assert d["tier"] == 1

    def test_scan_directory(self, tmp_path):
        # Create a skill directory with SKILL.md
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\nversion: '2.0'\nauthor: tester\n---\n# My Skill\n")
        reg = SkillRegistry()
        discovered = reg.scan_directory(tmp_path)
        assert len(discovered) == 1
        assert discovered[0].name == "my-skill"
        assert reg.get("my-skill") is not None

    def test_scan_directory_nonexistent(self, tmp_path):
        reg = SkillRegistry()
        result = reg.scan_directory(tmp_path / "nope")
        assert result == []

    def test_get_registry_singleton(self):
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2
