"""Tests for python/helpers/backup.py — backup creation, restoration, validation, preview, rollback."""

import json
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def backup_service(tmp_workdir):
    """BackupService with mocked agent_zero_root pointing to tmp_workdir."""
    with patch("python.helpers.backup.files.get_abs_path", return_value=str(tmp_workdir)):
        with patch("python.helpers.backup.git.get_git_info", return_value={"version": "test-1.0"}):
            from python.helpers.backup import BackupService

            svc = BackupService()
            svc.agent_zero_root = str(tmp_workdir)
            svc.base_paths = {str(tmp_workdir): str(tmp_workdir)}
            yield svc


@pytest.fixture
def mock_backup_file(tmp_path):
    """Create a mock backup file object with save() that writes to given path."""

    def _make_backup_file(zip_path: Path):
        mock = MagicMock()

        def save(dest):
            import shutil

            shutil.copy(zip_path, dest)

        mock.save = save
        return mock

    return _make_backup_file


@pytest.fixture
def valid_backup_zip(tmp_path, tmp_workdir):
    """Create a valid backup zip with metadata.json and sample files."""
    usr = tmp_path / "usr"
    usr.mkdir()
    (usr / "data.json").write_text('{"key": "value"}')
    (usr / "settings.json").write_text('{"theme": "dark"}')

    root = str(tmp_workdir).replace("\\", "/")
    arc_data = (root + "/usr/data.json").lstrip("/")
    arc_settings = (root + "/usr/settings.json").lstrip("/")

    metadata = {
        "agent_zero_version": "test-1.0",
        "timestamp": "2026-03-15T12:00:00",
        "backup_name": "test-backup",
        "include_patterns": [root + "/usr/**"],
        "exclude_patterns": [],
        "environment_info": {"agent_zero_root": root},
        "files": [
            {"path": arc_data, "size": 15, "modified": "2026-03-15T12:00:00", "type": "file"},
            {"path": arc_settings, "size": 18, "modified": "2026-03-15T12:00:00", "type": "file"},
        ],
    }

    zip_path = tmp_path / "backup.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))
        zf.write(usr / "data.json", arc_data)
        zf.write(usr / "settings.json", arc_settings)

    return zip_path


# --- _parse_patterns ---


class TestParsePatterns:
    def test_parses_include_patterns(self, backup_service):
        patterns = "/foo/**\n/bar/**"
        inc, exc = backup_service._parse_patterns(patterns)
        assert inc == ["/foo/**", "/bar/**"]
        assert exc == []

    def test_parses_exclude_patterns(self, backup_service):
        patterns = "/foo/**\n!/bar/**"
        inc, exc = backup_service._parse_patterns(patterns)
        assert inc == ["/foo/**"]
        assert exc == ["/bar/**"]

    def test_skips_empty_and_comments(self, backup_service):
        patterns = "\n# comment\n  \n/foo/**\n"
        inc, exc = backup_service._parse_patterns(patterns)
        assert inc == ["/foo/**"]
        assert exc == []


# --- _patterns_to_string ---


class TestPatternsToString:
    def test_converts_include_and_exclude(self, backup_service):
        inc = ["/foo/**"]
        exc = ["/bar/**"]
        s = backup_service._patterns_to_string(inc, exc)
        assert "/foo/**" in s
        assert "!/bar/**" in s


# --- _count_directories ---


class TestCountDirectories:
    def test_counts_unique_dirs(self, backup_service):
        files = [
            {"path": "/a/b/file1.txt"},
            {"path": "/a/b/file2.txt"},
            {"path": "/a/c/file3.txt"},
        ]
        assert backup_service._count_directories(files) == 2

    def test_returns_zero_for_empty(self, backup_service):
        assert backup_service._count_directories([]) == 0


# --- _get_explicit_patterns ---


class TestGetExplicitPatterns:
    def test_extracts_non_wildcard(self, backup_service):
        inc = ["/foo/bar", "/baz/**"]
        explicit = backup_service._get_explicit_patterns(inc)
        assert "/foo/bar" in explicit
        assert "/foo" in explicit
        assert "/baz/**" not in explicit

    def test_adds_parent_dirs(self, backup_service):
        inc = ["/a/b/c"]
        explicit = backup_service._get_explicit_patterns(inc)
        assert "a" in explicit
        assert "a/b" in explicit
        assert "a/b/c" in explicit


# --- _translate_patterns ---


class TestTranslatePatterns:
    def test_translates_backed_up_root_to_current(self, backup_service, tmp_workdir):
        backup_metadata = {
            "environment_info": {"agent_zero_root": "/old/agent/root"},
        }
        patterns = ["/old/agent/root/usr/**", "/other/path"]
        result = backup_service._translate_patterns(patterns, backup_metadata)
        assert any(str(tmp_workdir) in p for p in result)
        assert "/other/path" in result

    def test_returns_as_is_when_no_backed_up_root(self, backup_service):
        backup_metadata = {"environment_info": {}}
        patterns = ["/foo/**"]
        assert backup_service._translate_patterns(patterns, backup_metadata) == ["/foo/**"]


# --- _translate_restore_path ---


class TestTranslateRestorePath:
    def test_translates_archive_path_to_current_root(self, backup_service, tmp_workdir):
        backup_metadata = {
            "environment_info": {"agent_zero_root": "/old/root"},
        }
        path = backup_service._translate_restore_path("usr/data.json", backup_metadata)
        assert path.startswith(str(tmp_workdir))
        assert "usr/data.json" in path or path.endswith("usr/data.json")

    def test_returns_leading_slash_when_no_backed_up_root(self, backup_service):
        backup_metadata = {"environment_info": {}}
        path = backup_service._translate_restore_path("usr/data.json", backup_metadata)
        assert path.startswith("/")


# --- get_default_backup_metadata ---


class TestGetDefaultBackupMetadata:
    def test_returns_metadata_structure(self, backup_service):
        meta = backup_service.get_default_backup_metadata()
        assert "backup_name" in meta
        assert "include_patterns" in meta
        assert "exclude_patterns" in meta
        assert "include_hidden" in meta
        assert "backup_config" in meta
        assert "agent-zero-backup" in meta["backup_name"]


# --- test_patterns ---


class TestTestPatterns:
    @pytest.mark.asyncio
    async def test_returns_empty_for_no_matches(self, backup_service):
        meta = {"include_patterns": ["/nonexistent/path/**"], "exclude_patterns": [], "include_hidden": True}
        result = await backup_service.test_patterns(meta, max_files=100)
        assert result == []

    @pytest.mark.asyncio
    async def test_matches_files_in_usr(self, backup_service, tmp_workdir):
        usr = tmp_workdir / "usr"
        usr.mkdir(exist_ok=True)
        (usr / "test.txt").write_text("hello")

        meta = {
            "include_patterns": [str(tmp_workdir) + "/usr/**"],
            "exclude_patterns": [],
            "include_hidden": True,
        }
        result = await backup_service.test_patterns(meta, max_files=100)
        assert len(result) >= 1
        assert any("test.txt" in f["path"] for f in result)


# --- create_backup ---


class TestCreateBackup:
    @pytest.mark.asyncio
    async def test_raises_when_no_files_matched(self, backup_service):
        with patch.object(backup_service, "test_patterns", new_callable=AsyncMock, return_value=[]):
            with pytest.raises(Exception, match="No files matched"):
                await backup_service.create_backup(
                    include_patterns=["/nonexistent/**"],
                    exclude_patterns=[],
                    backup_name="empty-backup",
                )

    @pytest.mark.asyncio
    async def test_creates_zip_with_metadata(self, backup_service, tmp_workdir):
        usr = tmp_workdir / "usr"
        usr.mkdir(exist_ok=True)
        (usr / "data.txt").write_text("data")

        with patch("python.helpers.backup.tempfile.mkdtemp", return_value=str(tmp_workdir)):
            with patch.object(
                backup_service,
                "test_patterns",
                new_callable=AsyncMock,
                return_value=[
                    {
                        "path": str(usr / "data.txt"),
                        "real_path": str(usr / "data.txt"),
                        "size": 4,
                        "modified": "2026-03-15T12:00:00",
                        "type": "file",
                    }
                ],
            ):
                with patch("python.helpers.backup.PrintStyle"):
                    with patch.object(backup_service, "_get_system_info", new_callable=AsyncMock, return_value={}):
                        with patch.object(
                            backup_service, "_get_environment_info", new_callable=AsyncMock, return_value={}
                        ):
                            with patch.object(
                                backup_service, "_get_backup_author", new_callable=AsyncMock, return_value="test@host"
                            ):
                                path = await backup_service.create_backup(
                                    include_patterns=[str(usr) + "/**"],
                                    exclude_patterns=[],
                                    backup_name="test-backup",
                                )
        assert path.endswith("test-backup.zip")
        assert os.path.exists(path)
        with zipfile.ZipFile(path, "r") as zf:
            assert "metadata.json" in zf.namelist()
            meta = json.loads(zf.read("metadata.json").decode("utf-8"))
            assert meta["backup_name"] == "test-backup"
            assert "files" in meta


# --- inspect_backup ---


class TestInspectBackup:
    @pytest.mark.asyncio
    async def test_returns_metadata_for_valid_backup(
        self, backup_service, valid_backup_zip, mock_backup_file
    ):
        bf = mock_backup_file(valid_backup_zip)
        result = await backup_service.inspect_backup(bf)
        assert result["backup_name"] == "test-backup"
        assert "files_in_archive" in result
        assert any("data.json" in p for p in result["files_in_archive"])

    @pytest.mark.asyncio
    async def test_raises_for_missing_metadata(self, backup_service, tmp_path, mock_backup_file):
        zip_path = tmp_path / "bad.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other.txt", "data")
        bf = mock_backup_file(zip_path)
        with pytest.raises(Exception, match="missing metadata.json"):
            await backup_service.inspect_backup(bf)

    @pytest.mark.asyncio
    async def test_raises_for_bad_zip(self, backup_service, tmp_path):
        bad_file = MagicMock()

        def save(dest):
            Path(dest).write_text("not a zip")

        bad_file.save = save
        with pytest.raises(Exception, match="not a valid zip"):
            await backup_service.inspect_backup(bad_file)


# --- preview_restore ---


class TestPreviewRestore:
    @pytest.mark.asyncio
    async def test_preview_returns_files_to_restore(
        self, backup_service, valid_backup_zip, mock_backup_file, tmp_workdir
    ):
        bf = mock_backup_file(valid_backup_zip)
        result = await backup_service.preview_restore(bf, overwrite_policy="overwrite")
        assert "files_to_restore" in result
        assert "files_to_delete" in result
        assert "skipped_files" in result
        assert result["restore_count"] >= 1
        assert "backup_metadata" in result

    @pytest.mark.asyncio
    async def test_preview_skips_existing_with_skip_policy(
        self, backup_service, valid_backup_zip, mock_backup_file, tmp_workdir
    ):
        usr = tmp_workdir / "usr"
        usr.mkdir(exist_ok=True)
        (usr / "data.json").write_text("existing")

        bf = mock_backup_file(valid_backup_zip)
        result = await backup_service.preview_restore(bf, overwrite_policy="skip")
        skipped = [s for s in result["skipped_files"] if s.get("reason") == "file_exists_skip_policy"]
        assert len(skipped) >= 1


# --- restore_backup ---


class TestRestoreBackup:
    @pytest.mark.asyncio
    async def test_restore_extracts_files(
        self, backup_service, valid_backup_zip, mock_backup_file, tmp_workdir
    ):
        bf = mock_backup_file(valid_backup_zip)
        result = await backup_service.restore_backup(bf, overwrite_policy="overwrite")
        assert "restored_files" in result
        assert len(result["restored_files"]) >= 1
        for r in result["restored_files"]:
            assert os.path.exists(r["target_path"])

    @pytest.mark.asyncio
    async def test_restore_with_backup_policy_creates_backup(
        self, backup_service, valid_backup_zip, mock_backup_file, tmp_workdir
    ):
        usr = tmp_workdir / "usr"
        usr.mkdir(exist_ok=True)
        (usr / "data.json").write_text("existing")

        bf = mock_backup_file(valid_backup_zip)
        result = await backup_service.restore_backup(bf, overwrite_policy="backup")
        assert len(result["restored_files"]) >= 1
        backups = list(tmp_workdir.rglob("*.backup.*"))
        assert len(backups) >= 1


# --- Invalid backup handling ---


class TestInvalidBackupHandling:
    @pytest.mark.asyncio
    async def test_inspect_raises_for_corrupted_metadata(self, backup_service, tmp_path, mock_backup_file):
        zip_path = tmp_path / "corrupt.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("metadata.json", "not valid json")
        bf = mock_backup_file(zip_path)
        with pytest.raises(Exception, match="corrupted metadata"):
            await backup_service.inspect_backup(bf)

    @pytest.mark.asyncio
    async def test_preview_raises_for_bad_zip(self, backup_service):
        bad = MagicMock()

        def save(dest):
            Path(dest).write_text("invalid")

        bad.save = save
        with pytest.raises(Exception, match="not a valid zip"):
            await backup_service.preview_restore(bad)

    @pytest.mark.asyncio
    async def test_restore_raises_for_bad_zip(self, backup_service):
        bad = MagicMock()

        def save(dest):
            Path(dest).write_text("invalid")

        bad.save = save
        with pytest.raises(Exception, match="not a valid zip"):
            await backup_service.restore_backup(bad)
