"""Tests for SkillPackager: package, sha256, verify, extract."""

import pytest

from python.helpers.skill_packager import SkillPackager


def _create_skill(tmp_path, name="test-skill"):
    """Create a minimal skill directory for testing."""
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\nversion: '1.0'\nauthor: test\n---\n# Test\n")
    (skill_dir / "main.py").write_text("def run(): pass\n")
    (skill_dir / "requirements.txt").write_text("requests>=2.0\n")
    return skill_dir


@pytest.mark.unit
class TestSkillPackager:
    def test_package_creates_tarball(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        packager = SkillPackager()
        archive = packager.package(skill_dir, output_dir=tmp_path / "out")
        assert archive.exists()
        assert archive.name == "test-skill.tar.gz"

    def test_package_missing_dir_raises(self, tmp_path):
        packager = SkillPackager()
        with pytest.raises(FileNotFoundError):
            packager.package(tmp_path / "nope")

    def test_package_missing_skill_md_raises(self, tmp_path):
        skill_dir = tmp_path / "no-md"
        skill_dir.mkdir()
        (skill_dir / "main.py").write_text("x = 1\n")
        packager = SkillPackager()
        with pytest.raises(FileNotFoundError, match=r"SKILL\.md"):
            packager.package(skill_dir)

    def test_get_sha256(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        packager = SkillPackager()
        archive = packager.package(skill_dir)
        sha = packager.get_sha256(archive)
        assert isinstance(sha, str)
        assert len(sha) == 64

    def test_get_sha256_missing_file(self, tmp_path):
        packager = SkillPackager()
        with pytest.raises(FileNotFoundError):
            packager.get_sha256(tmp_path / "nope.tar.gz")

    def test_verify_correct_hash(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        packager = SkillPackager()
        archive = packager.package(skill_dir)
        sha = packager.get_sha256(archive)
        assert packager.verify(archive, sha) is True

    def test_verify_wrong_hash(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        packager = SkillPackager()
        archive = packager.package(skill_dir)
        assert packager.verify(archive, "0" * 64) is False

    def test_extract(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        packager = SkillPackager()
        archive = packager.package(skill_dir, output_dir=tmp_path / "pkg")
        extract_dir = tmp_path / "extracted"
        result = packager.extract(archive, extract_dir)
        assert result.exists()
        assert (result / "SKILL.md").exists()
        assert (result / "main.py").exists()

    def test_extract_missing_package(self, tmp_path):
        packager = SkillPackager()
        with pytest.raises(FileNotFoundError):
            packager.extract(tmp_path / "nope.tar.gz", tmp_path / "out")

    def test_pycache_excluded(self, tmp_path):
        skill_dir = _create_skill(tmp_path)
        cache_dir = skill_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "main.cpython-311.pyc").write_bytes(b"\x00")
        packager = SkillPackager()
        archive = packager.package(skill_dir, output_dir=tmp_path / "pkg")
        extract_dir = tmp_path / "check"
        result = packager.extract(archive, extract_dir)
        assert not (result / "__pycache__").exists()

    def test_package_real_example_skill(self):
        """Test packaging the actual example-skill from the repo."""
        from pathlib import Path

        skill_dir = Path("/mnt/wdblack/dev/projects/agent-zero/.worktrees/agent-jumbo/skills/example-skill")
        if not skill_dir.exists():
            pytest.skip("example-skill not found")
        packager = SkillPackager()
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = packager.package(skill_dir, output_dir=Path(tmpdir))
            assert archive.exists()
            sha = packager.get_sha256(archive)
            assert len(sha) == 64
