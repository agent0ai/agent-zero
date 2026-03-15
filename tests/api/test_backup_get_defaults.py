"""Tests for python/api/backup_get_defaults.py — BackupGetDefaults API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_get_defaults import BackupGetDefaults


def _make_handler():
    return BackupGetDefaults(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupGetDefaults:
    def test_requires_auth(self):
        assert BackupGetDefaults.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupGetDefaults.requires_loopback() is False

    @pytest.mark.asyncio
    async def test_returns_default_patterns_successfully(self):
        handler = _make_handler()
        default_metadata = {
            "include_patterns": ["usr/**"],
            "exclude_patterns": ["*.log"],
            "backup_name": "agent-zero-backup",
        }

        with patch("python.api.backup_get_defaults.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.get_default_backup_metadata = MagicMock(return_value=default_metadata)
            MockBackup.return_value = mock_svc

            result = await handler.process({}, MagicMock())

        assert result["success"] is True
        assert result["default_patterns"]["include_patterns"] == ["usr/**"]
        assert result["default_patterns"]["exclude_patterns"] == ["*.log"]
        assert result["metadata"] == default_metadata

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        handler = _make_handler()
        with patch("python.api.backup_get_defaults.BackupService") as MockBackup:
            MockBackup.side_effect = Exception("Init failed")

            result = await handler.process({}, MagicMock())

        assert result["success"] is False
        assert "Init failed" in result["error"]
