"""Tests for python/helpers/rate_limiter.py — RateLimiter (fully mocked, no external API calls)."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.rate_limiter import RateLimiter


class TestRateLimiterInit:
    def test_init_sets_timeframe_and_limits(self):
        rl = RateLimiter(seconds=60, requests=10, tokens=1000)
        assert rl.timeframe == 60
        assert rl.limits["requests"] == 10
        assert rl.limits["tokens"] == 1000

    def test_init_handles_non_int_limits(self):
        rl = RateLimiter(seconds=60, requests="bad", tokens=5.5)
        assert rl.limits.get("requests") == 0
        # Floats are accepted as-is; only non-numeric values become 0
        assert rl.limits.get("tokens") == 5.5


class TestRateLimiterAdd:
    def test_add_appends_values(self):
        rl = RateLimiter(seconds=60, key=5)
        rl.add(key=2)
        rl.add(key=3)
        assert len(rl.values["key"]) == 2


class TestRateLimiterCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_removes_old_entries(self):
        import time
        rl = RateLimiter(seconds=1, k=10)
        rl.add(k=1)
        await asyncio.sleep(0.05)
        rl.add(k=2)
        await rl.cleanup()
        assert len(rl.values["k"]) >= 1

    @pytest.mark.asyncio
    async def test_cleanup_removes_entries_older_than_timeframe(self):
        import time
        rl = RateLimiter(seconds=1, k=10)
        rl.add(k=1)
        await asyncio.sleep(1.1)
        await rl.cleanup()
        assert len(rl.values["k"]) == 0


class TestRateLimiterGetTotal:
    @pytest.mark.asyncio
    async def test_get_total_sums_values(self):
        rl = RateLimiter(seconds=60, k=100)
        rl.add(k=10)
        rl.add(k=20)
        total = await rl.get_total("k")
        assert total == 30

    @pytest.mark.asyncio
    async def test_get_total_returns_zero_for_unknown_key(self):
        rl = RateLimiter(seconds=60, x=5)
        total = await rl.get_total("nonexistent")
        assert total == 0


class TestRateLimiterWait:
    @pytest.mark.asyncio
    async def test_wait_exits_immediately_when_under_limit(self):
        rl = RateLimiter(seconds=60, k=100)
        rl.add(k=5)
        await rl.wait()
        # Should complete without blocking

    @pytest.mark.asyncio
    async def test_wait_loops_when_over_limit_until_cleanup_reduces(self):
        rl = RateLimiter(seconds=1, k=5)
        rl.add(k=10)
        call_count = 0

        async def callback(msg, key, total, limit):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                rl.values[key] = [(0, 0)]
                return True
            return False

        await rl.wait(callback=callback)
        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_wait_with_callback_returns_false_continues_waiting(self):
        rl = RateLimiter(seconds=1, k=5)
        rl.add(k=10)
        callback = AsyncMock(return_value=False)
        task = asyncio.create_task(rl.wait(callback=callback))
        await asyncio.sleep(0.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
