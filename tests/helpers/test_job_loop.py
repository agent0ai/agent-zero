"""Tests for python/helpers/job_loop.py."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- run_loop ---


@pytest.mark.asyncio
class TestRunLoop:
    async def test_run_loop_calls_scheduler_tick_when_keep_running(self):
        from python.helpers import job_loop

        with patch.object(job_loop, "keep_running", True):
            with patch.object(job_loop, "scheduler_tick", new_callable=AsyncMock) as mock_tick:
                with patch.object(job_loop, "asyncio") as mock_asyncio:
                    mock_asyncio.sleep = AsyncMock(side_effect=asyncio.CancelledError)
                    mock_asyncio.sleep.side_effect = asyncio.CancelledError
                    with pytest.raises(asyncio.CancelledError):
                        await job_loop.run_loop()
                    mock_tick.assert_called()

    async def test_run_loop_sleeps_between_ticks(self):
        from python.helpers import job_loop

        call_count = 0

        async def mock_sleep(secs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError()

        with patch.object(job_loop, "keep_running", True):
            with patch.object(job_loop, "scheduler_tick", new_callable=AsyncMock):
                with patch.object(job_loop, "asyncio") as mock_asyncio:
                    mock_asyncio.sleep = mock_sleep
                    with pytest.raises(asyncio.CancelledError):
                        await job_loop.run_loop()
                    assert call_count >= 1


# --- scheduler_tick ---


@pytest.mark.asyncio
class TestSchedulerTick:
    async def test_scheduler_tick_calls_task_scheduler_tick(self):
        from python.helpers.job_loop import scheduler_tick

        with patch("python.helpers.job_loop.TaskScheduler.get") as mock_get:
            mock_scheduler = MagicMock()
            mock_scheduler.tick = AsyncMock()
            mock_get.return_value = mock_scheduler
            await scheduler_tick()
            mock_scheduler.tick.assert_called_once()


# --- pause_loop / resume_loop ---


class TestPauseResumeLoop:
    def test_pause_loop_sets_keep_running_false(self):
        from python.helpers import job_loop
        import time

        job_loop.keep_running = True
        job_loop.pause_loop()
        assert job_loop.keep_running is False
        assert job_loop.pause_time > 0
        job_loop.resume_loop()

    def test_resume_loop_sets_keep_running_true(self):
        from python.helpers import job_loop

        job_loop.keep_running = False
        job_loop.pause_time = 10
        job_loop.resume_loop()
        assert job_loop.keep_running is True
        assert job_loop.pause_time == 0


# --- SLEEP_TIME ---


def test_sleep_time_constant():
    from python.helpers.job_loop import SLEEP_TIME

    assert SLEEP_TIME == 60


# --- run_loop development mode ---


@pytest.mark.asyncio
async def test_run_loop_attempts_pause_in_development():
    from python.helpers import job_loop

    with patch("python.helpers.job_loop.runtime.is_development", return_value=True):
        with patch("python.helpers.job_loop.runtime.call_development_function", new_callable=AsyncMock) as mock_pause:
            mock_pause.return_value = None
            with patch.object(job_loop, "keep_running", True):
                with patch.object(job_loop, "scheduler_tick", new_callable=AsyncMock):
                    with patch.object(job_loop, "asyncio") as mock_asyncio:
                        mock_asyncio.sleep = AsyncMock(side_effect=asyncio.CancelledError)
                        with pytest.raises(asyncio.CancelledError):
                            await job_loop.run_loop()
                        mock_pause.assert_called()
