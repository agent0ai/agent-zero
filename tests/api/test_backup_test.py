"""Tests for python/api/backup_test.py — BackupTest API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_test import BackupTest


def _make_handler():
    return BackupTest(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupTest:
    def test_requires_auth(self):
        assert BackupTest.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupTest.requires_loopback() is False

    @pytest.mark.asyncio
    async def test_returns_empty_files_when_no_include_patterns(self):
        handler = _make_handler()
        result = await handler.process({}, MagicMock())

        assert result["success"] is True
        assert result["files"] == []
        assert result["total_count"] == 0
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_returns_matched_files_successfully(self):
        handler = _make_handler()
        matched_files = [
            {"path": "usr/data.json", "size": 100},
            {"path": "usr/settings.json", "size": 200},
        ]

        with patch("python.api.backup_test.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=matched_files)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "include_patterns": ["usr/**"],
            }, MagicMock())

        assert result["success"] is True
        assert result["files"] == matched_files
        assert result["total_count"] == 2
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_indicates_truncated_when_at_max_files(self):
        handler = _make_handler()
        many_files = [{"path": f"usr/file{i}.json", "size": 10} for i in range(1000)]

        with patch("python.api.backup_test.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=many_files)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "include_patterns": ["usr/**"],
                "max_files": 1000,
            }, MagicMock())

        assert result["success"] is True
        assert result["truncated"] is True
        assert result["total_count"] == 1000

    @pytest.mark.asyncio
    async def test_parses_legacy_patterns_string(self):
        handler = _make_handler()
        with patch("python.api.backup_test.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=[])
            MockBackup.return_value = mock_svc

            await handler.process({
                "patterns": "usr/**\n!*.tmp",
            }, MagicMock())

        metadata = mock_svc.test_patterns.call_args[0][0]
        assert "usr/**" in metadata["include_patterns"]
        assert "*.tmp" in metadata["exclude_patterns"]
