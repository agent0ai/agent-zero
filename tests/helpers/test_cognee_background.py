"""Tests for python/helpers/cognee_background.py — Background cognify worker."""

import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.cognee_background import CogneeBackgroundWorker


@pytest.fixture
def worker():
    CogneeBackgroundWorker._instance = None
    w = CogneeBackgroundWorker()
    yield w
    CogneeBackgroundWorker._instance = None


# --- mark_dirty ---

class TestMarkDirty:
    def test_adds_dataset(self, worker):
        worker.mark_dirty("ds_main")
        assert "ds_main" in worker._dirty_datasets

    def test_increments_insert_count(self, worker):
        worker.mark_dirty("ds_main")
        worker.mark_dirty("ds_main")
        worker.mark_dirty("ds_solutions")
        assert worker._insert_count == 3

    def test_deduplicates_datasets(self, worker):
        worker.mark_dirty("ds_main")
        worker.mark_dirty("ds_main")
        assert len(worker._dirty_datasets) == 1


# --- get_status ---

class TestGetStatus:
    def test_initial_status(self, worker):
        status = worker.get_status()
        assert status["running"] is False
        assert status["dirty_datasets"] == []
        assert status["insert_count"] == 0
        assert status["last_error"] is None
        assert status["last_run_success"] is False

    def test_status_after_dirty(self, worker):
        worker.mark_dirty("ds1")
        worker.mark_dirty("ds2")
        status = worker.get_status()
        assert set(status["dirty_datasets"]) == {"ds1", "ds2"}
        assert status["insert_count"] == 2


# --- _get_config ---

class TestGetConfig:
    def test_uses_get_cognee_setting(self, worker):
        with patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 10,
                "cognee_cognify_after_n_inserts": 20,
                "cognee_temporal_enabled": False,
                "cognee_memify_enabled": True,
            }.get(name, default)
            config = worker._get_config()

        assert config["cognify_interval"] == 10
        assert config["cognify_after_n_inserts"] == 20
        assert config["temporal_enabled"] is False
        assert config["memify_enabled"] is True


# --- _should_run ---

class TestShouldRun:
    @pytest.mark.asyncio
    async def test_false_when_no_dirty(self, worker):
        assert await worker._should_run() is False

    @pytest.mark.asyncio
    async def test_true_on_insert_threshold(self, worker):
        with patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 999,
                "cognee_cognify_after_n_inserts": 3,
                "cognee_temporal_enabled": True,
                "cognee_memify_enabled": True,
            }.get(name, default)
            for i in range(3):
                worker.mark_dirty(f"ds_{i}")
            result = await worker._should_run()
        assert result is True

    @pytest.mark.asyncio
    async def test_true_on_time_threshold(self, worker):
        with patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 0,
                "cognee_cognify_after_n_inserts": 999,
                "cognee_temporal_enabled": True,
                "cognee_memify_enabled": True,
            }.get(name, default)
            worker.mark_dirty("ds1")
            worker._last_cognify_time = 0
            result = await worker._should_run()
        assert result is True

    @pytest.mark.asyncio
    async def test_false_when_below_both_thresholds(self, worker):
        with patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 999,
                "cognee_cognify_after_n_inserts": 999,
                "cognee_temporal_enabled": True,
                "cognee_memify_enabled": True,
            }.get(name, default)
            worker.mark_dirty("ds1")
            worker._last_cognify_time = time.monotonic()
            result = await worker._should_run()
        assert result is False


# --- run_pipeline ---

class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_cognify_with_temporal(self, worker):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock()
        mock_cognee.memify = AsyncMock()

        worker.mark_dirty("ds1")
        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 5,
                "cognee_cognify_after_n_inserts": 10,
                "cognee_temporal_enabled": True,
                "cognee_memify_enabled": False,
            }.get(name, default)
            await worker.run_pipeline()

        mock_cognee.cognify.assert_called_once_with(
            datasets=["ds1"], temporal_cognify=True
        )
        assert worker._last_run_success is True
        assert len(worker._dirty_datasets) == 0
        assert worker._insert_count == 0

    @pytest.mark.asyncio
    async def test_cognify_without_temporal(self, worker):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock()

        worker.mark_dirty("ds1")
        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 5,
                "cognee_cognify_after_n_inserts": 10,
                "cognee_temporal_enabled": False,
                "cognee_memify_enabled": False,
            }.get(name, default)
            await worker.run_pipeline()

        mock_cognee.cognify.assert_called_once_with(
            datasets=["ds1"], temporal_cognify=False
        )

    @pytest.mark.asyncio
    async def test_memify_failure_continues(self, worker):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock()
        mock_cognee.memify = AsyncMock(side_effect=Exception("memify broken"))

        worker.mark_dirty("ds1")
        worker.mark_dirty("ds2")
        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 5,
                "cognee_cognify_after_n_inserts": 10,
                "cognee_temporal_enabled": False,
                "cognee_memify_enabled": True,
            }.get(name, default)
            await worker.run_pipeline()

        assert mock_cognee.memify.call_count == 2
        assert worker._last_run_success is True
        assert worker._last_error == "memify broken"
        assert len(worker._dirty_datasets) == 0

    @pytest.mark.asyncio
    async def test_cognify_failure_sets_error(self, worker):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock(side_effect=Exception("cognify crash"))

        worker.mark_dirty("ds1")
        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_background.get_cognee_setting") as mock_setting:
            mock_setting.side_effect = lambda name, default: {
                "cognee_cognify_interval": 5,
                "cognee_cognify_after_n_inserts": 10,
                "cognee_temporal_enabled": False,
                "cognee_memify_enabled": False,
            }.get(name, default)
            await worker.run_pipeline()

        assert worker._last_run_success is False
        assert "cognify crash" in worker._last_error

    @pytest.mark.asyncio
    async def test_no_op_when_no_dirty(self, worker):
        mock_cognee = MagicMock()
        mock_cognee.cognify = AsyncMock()
        with patch.dict("sys.modules", {"cognee": mock_cognee}):
            await worker.run_pipeline()
        mock_cognee.cognify.assert_not_called()


# --- singleton ---

class TestSingleton:
    def test_get_instance_returns_same(self):
        CogneeBackgroundWorker._instance = None
        a = CogneeBackgroundWorker.get_instance()
        b = CogneeBackgroundWorker.get_instance()
        assert a is b
        CogneeBackgroundWorker._instance = None
