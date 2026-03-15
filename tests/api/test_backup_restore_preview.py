"""Tests for python/api/backup_restore_preview.py — BackupRestorePreview API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_restore_preview import BackupRestorePreview


def _make_handler():
    return BackupRestorePreview(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupRestorePreview:
    def test_requires_auth(self):
        assert BackupRestorePreview.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupRestorePreview.requires_loopback() is False

    @pytest.mark.asyncio
    async def test_returns_error_when_no_backup_file(self):
        handler = _make_handler()
        mock_request = MagicMock()
        mock_request.files = {}

        result = await handler.process({}, mock_request)

        assert result["success"] is False
        assert "No backup file" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_empty_filename(self):
        handler = _make_handler()
        mock_file = MagicMock()
        mock_file.filename = ""
        mock_request = MagicMock()
        mock_request.files = {"backup_file": mock_file}

        result = await handler.process({}, mock_request)

        assert result["success"] is False
        assert "No file selected" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_preview_successfully(self):
        handler = _make_handler()
        mock_file = MagicMock()
        mock_file.filename = "backup.zip"
        mock_request = MagicMock()
        mock_request.files = {"backup_file": mock_file}
        mock_request.form = {
            "metadata": '{"include_patterns": ["usr/**"], "exclude_patterns": []}',
            "overwrite_policy": "overwrite",
            "clean_before_restore": "false",
        }

        preview_result = {
            "files": [{"path": "usr/data.json", "size": 100}],
            "files_to_delete": [],
            "files_to_restore": ["usr/data.json"],
            "skipped_files": [],
            "total_count": 1,
            "delete_count": 0,
            "restore_count": 1,
            "skipped_count": 0,
            "backup_metadata": {},
            "overwrite_policy": "overwrite",
            "clean_before_restore": False,
        }

        with patch("python.api.backup_restore_preview.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.preview_restore = AsyncMock(return_value=preview_result)
            MockBackup.return_value = mock_svc

            result = await handler.process({}, mock_request)

        assert result["success"] is True
        assert result["files"] == preview_result["files"]
        assert result["total_count"] == 1
        mock_svc.preview_restore.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_error_on_invalid_metadata_json(self):
        handler = _make_handler()
        mock_file = MagicMock()
        mock_file.filename = "backup.zip"
        mock_request = MagicMock()
        mock_request.files = {"backup_file": mock_file}
        mock_request.form = {"metadata": "not json"}

        result = await handler.process({}, mock_request)

        assert result["success"] is False
        assert "Invalid metadata" in result["error"]
