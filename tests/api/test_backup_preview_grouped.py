"""Tests for python/api/backup_preview_grouped.py — BackupPreviewGrouped API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.backup_preview_grouped import BackupPreviewGrouped


def _make_handler():
    return BackupPreviewGrouped(app=MagicMock(), thread_lock=threading.Lock())


class TestBackupPreviewGrouped:
    def test_requires_auth(self):
        assert BackupPreviewGrouped.requires_auth() is True

    def test_requires_loopback_false(self):
        assert BackupPreviewGrouped.requires_loopback() is False

    @pytest.mark.asyncio
    async def test_returns_empty_groups_when_no_include_patterns(self):
        handler = _make_handler()
        result = await handler.process({}, MagicMock())

        assert result["success"] is True
        assert result["groups"] == []
        assert result["stats"]["total_groups"] == 0
        assert result["total_files"] == 0

    @pytest.mark.asyncio
    async def test_parses_legacy_patterns_string(self):
        handler = _make_handler()
        all_files = [
            {"path": "/usr/data.json", "size": 100},
        ]

        with patch("python.api.backup_preview_grouped.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=all_files)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "patterns": "usr/**\n!*.log",
            }, MagicMock())

        assert result["success"] is True
        mock_svc.test_patterns.assert_called_once()
        metadata = mock_svc.test_patterns.call_args[0][0]
        assert "usr/**" in metadata["include_patterns"]
        assert "*.log" in metadata["exclude_patterns"]

    @pytest.mark.asyncio
    async def test_groups_files_by_directory(self):
        handler = _make_handler()
        all_files = [
            {"path": "usr/data.json", "size": 100},
            {"path": "usr/settings.json", "size": 200},
        ]

        with patch("python.api.backup_preview_grouped.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=all_files)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "include_patterns": ["usr/**"],
            }, MagicMock())

        assert result["success"] is True
        assert result["total_files"] == 2
        assert result["total_size"] == 300
        assert len(result["groups"]) >= 1

    @pytest.mark.asyncio
    async def test_applies_search_filter(self):
        handler = _make_handler()
        all_files = [
            {"path": "/usr/data.json", "size": 100},
            {"path": "/usr/other.txt", "size": 50},
        ]

        with patch("python.api.backup_preview_grouped.BackupService") as MockBackup:
            mock_svc = MagicMock()
            mock_svc.test_patterns = AsyncMock(return_value=all_files)
            MockBackup.return_value = mock_svc

            result = await handler.process({
                "include_patterns": ["usr/**"],
                "search_filter": "data",
            }, MagicMock())

        assert result["success"] is True
        assert result["stats"]["search_applied"] is True
        assert result["total_files"] == 1
