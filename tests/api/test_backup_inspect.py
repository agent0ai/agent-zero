"""Tests for python/api/backup_inspect.py — BackupInspect API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_inspect import BackupInspect


def _make_handler():
    return BackupInspect(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupInspect:
    def test_requires_auth(self):
        assert BackupInspect.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupInspect.requires_loopback() is False

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
    async def test_returns_metadata_successfully(self):
        handler = _make_handler()
        mock_file = MagicMock()
        mock_file.filename = "backup.zip"
        mock_request = MagicMock()
        mock_request.files = {"backup_file": mock_file}

        metadata = {
            "files": [{"path": "usr/data.json"}],
            "include_patterns": ["usr/**"],
            "exclude_patterns": [],
            "backup_config": {"default_patterns": "usr/**"},
            "agent_zero_version": "1.0",
            "timestamp": "2026-03-15",
            "backup_name": "test",
            "total_files": 1,
            "backup_size": 1024,
            "include_hidden": True,
            "files_in_archive": ["usr/data.json"],
        }

        with patch("python.api.backup_inspect.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.inspect_backup = AsyncMock(return_value=metadata)
            MockBackup.return_value = mock_svc

            result = await handler.process({}, mock_request)

        assert result["success"] is True
        assert result["metadata"] == metadata
        assert result["files"] == metadata["files"]
        assert result["agent_zero_version"] == "1.0"
        assert result["total_files"] == 1
