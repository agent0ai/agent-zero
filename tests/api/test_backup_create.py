"""Tests for python/api/backup_create.py — BackupCreate API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_create import BackupCreate


def _make_handler():
    return BackupCreate(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupCreate:
    def test_requires_auth(self):
        assert BackupCreate.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupCreate.requires_loopback() is False

    @pytest.mark.asyncio
    async def test_returns_send_file_response_on_success(self):
        handler = _make_handler()
        zip_path = "/tmp/backup.zip"
        mock_response = MagicMock()

        with patch("python.api.backup_create.save_tmp_chats"), \
             patch("python.api.backup_create.BackupService") as MockBackup, \
             patch("python.api.backup_create.send_file", return_value=mock_response):
            mock_svc = MagicMock()
            mock_svc.create_backup = AsyncMock(return_value=zip_path)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "include_patterns": ["usr/**"],
                "backup_name": "test-backup",
            }, MagicMock())

        assert result is mock_response
        mock_svc.create_backup.assert_called_once_with(
            include_patterns=["usr/**"],
            exclude_patterns=[],
            include_hidden=True,
            backup_name="test-backup",
        )

    @pytest.mark.asyncio
    async def test_parses_legacy_patterns_string(self):
        handler = _make_handler()
        zip_path = "/tmp/backup.zip"
        mock_response = MagicMock()

        with patch("python.api.backup_create.save_tmp_chats"), \
             patch("python.api.backup_create.BackupService") as MockBackup, \
             patch("python.api.backup_create.send_file", return_value=mock_response):
            mock_svc = MagicMock()
            mock_svc.create_backup = AsyncMock(return_value=zip_path)
            MockBackup.return_value = mock_svc

            await handler.process({
                "patterns": "usr/**\n!*.log",
                "backup_name": "legacy",
            }, MagicMock())

        mock_svc.create_backup.assert_called_once()
        call_kwargs = mock_svc.create_backup.call_args[1]
        assert "usr/**" in call_kwargs["include_patterns"]
        assert "*.log" in call_kwargs["exclude_patterns"]

    @pytest.mark.asyncio
    async def test_returns_error_dict_on_exception(self):
        handler = _make_handler()
        with patch("python.api.backup_create.save_tmp_chats"), \
             patch("python.api.backup_create.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.create_backup = AsyncMock(side_effect=Exception("Disk full"))
            MockBackup.return_value = mock_svc

            result = await handler.process({"backup_name": "test"}, MagicMock())

        assert result["success"] is False
        assert "Disk full" in result["error"]
