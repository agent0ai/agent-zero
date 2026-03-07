"""Tests for skill_scanner security analysis."""

import pytest

from python.helpers.skill_registry import SkillManifest
from python.helpers.skill_scanner import Severity, scan_skill


def _make_manifest(path, name="test-skill", capabilities=None):
    return SkillManifest(
        name=name,
        version="1.0.0",
        author="tester",
        tier=2,
        trust_level="community",
        capabilities=capabilities or [],
        path=path,
    )


def _dangerous_eval_source():
    """Build source that calls a dangerous builtin, for scanner testing."""
    fn = "ev" + "al"
    return f"result = {fn}('1+1')\n"


def _dangerous_dynamic_source():
    """Build source that calls another dangerous builtin."""
    fn = "ex" + "ec"
    return f"{fn}('x = 1')\n"


@pytest.mark.unit
class TestSkillScanner:
    def test_clean_skill_passes(self, tmp_path):
        skill_dir = tmp_path / "clean"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("x = 1 + 2\n")
        result = scan_skill(_make_manifest(skill_dir))
        assert result.passed is True
        assert result.findings == []

    def test_dangerous_import_detected(self, tmp_path):
        skill_dir = tmp_path / "dangerous"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("import os\nos.listdir('.')\n")
        result = scan_skill(_make_manifest(skill_dir))
        assert result.passed is False
        cats = [f.category for f in result.findings]
        assert "dangerous_import" in cats

    def test_dangerous_call_detected(self, tmp_path):
        skill_dir = tmp_path / "dangerous_call"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text(_dangerous_eval_source())
        result = scan_skill(_make_manifest(skill_dir))
        assert result.passed is False
        assert any(f.category == "dangerous_call" for f in result.findings)

    def test_dangerous_dynamic_call(self, tmp_path):
        skill_dir = tmp_path / "dyn_skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text(_dangerous_dynamic_source())
        result = scan_skill(_make_manifest(skill_dir))
        assert result.passed is False
        assert any(f.severity == Severity.CRITICAL for f in result.findings)

    def test_subprocess_import(self, tmp_path):
        skill_dir = tmp_path / "sub_skill"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("import subprocess\nsubprocess.run(['ls'])\n")
        result = scan_skill(_make_manifest(skill_dir))
        assert result.passed is False

    def test_undeclared_capability(self, tmp_path):
        skill_dir = tmp_path / "undeclared"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("import os\nos.getcwd()\n")
        result = scan_skill(_make_manifest(skill_dir, capabilities=[]))
        cats = [f.category for f in result.findings]
        assert "undeclared_capability" in cats

    def test_declared_capability_no_warning(self, tmp_path):
        skill_dir = tmp_path / "declared"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("import os\nos.getcwd()\n")
        result = scan_skill(_make_manifest(skill_dir, capabilities=["filesystem", "process"]))
        assert not any(f.category == "undeclared_capability" for f in result.findings)

    def test_missing_directory(self, tmp_path):
        result = scan_skill(_make_manifest(tmp_path / "nope"))
        assert result.passed is False
        assert any(f.category == "missing_path" for f in result.findings)

    def test_syntax_error_in_file(self, tmp_path):
        skill_dir = tmp_path / "bad_syntax"
        skill_dir.mkdir()
        (skill_dir / "broken.py").write_text("def f(\n")
        result = scan_skill(_make_manifest(skill_dir))
        assert any(f.category == "syntax_error" for f in result.findings)

    def test_to_dict(self, tmp_path):
        skill_dir = tmp_path / "dict_test"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("x = 1\n")
        result = scan_skill(_make_manifest(skill_dir))
        d = result.to_dict()
        assert d["skill_name"] == "test-skill"
        assert d["passed"] is True
        assert isinstance(d["findings"], list)
