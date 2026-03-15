"""Tests for python/api/backup_restore.py — BackupRestore API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_restore import BackupRestore


def _make_handler():
    return BackupRestore(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupRestore:
    def test_requires_auth(self):
        assert BackupRestore.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupRestore.requires_loopback() is False

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
    async def test_restores_successfully(self):
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

        restore_result = {
            "restored_files": ["usr/data.json"],
            "deleted_files": [],
            "skipped_files": [],
            "errors": [],
            "backup_metadata": {},
            "clean_before_restore": False,
        }

        with patch("python.api.backup_restore.BackupService") as MockBackup, \
             patch("python.api.backup_restore.load_tmp_chats"):
            mock_svc = MagicMock()
            mock_svc.restore_backup = AsyncMock(return_value=restore_result)
            MockBackup.return_value = mock_svc

            result = await handler.process({}, mock_request)

        assert result["success"] is True
        assert result["restored_files"] == ["usr/data.json"]
        mock_svc.restore_backup.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_error_on_invalid_metadata_json(self):
        handler = _make_handler()
        mock_file = MagicMock()
        mock_file.filename = "backup.zip"
        mock_request = MagicMock()
        mock_request.files = {"backup_file": mock_file}
        mock_request.form = {"metadata": "invalid json"}

        result = await handler.process({}, mock_request)

        assert result["success"] is False
        assert "Invalid metadata" in result["error"]
