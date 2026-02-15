import asyncio
import time
from typing import Callable, Awaitable


class RateLimiter:
    def __init__(self, seconds: int = 60, **limits: int):
        self.timeframe = seconds
        self.limits = {key: value if isinstance(value, (int, float)) else 0 for key, value in (limits or {}).items()}
        self.values = {key: [] for key in self.limits.keys()}
        self._lock = asyncio.Lock()
        self._concurrent_limit = 0
        self._semaphore: asyncio.Semaphore | None = None
        self._semaphore_loop_id: int | None = None

    def _get_current_loop_id(self) -> int:
        """Get ID of the current running event loop."""
        return id(asyncio.get_running_loop())

    def _ensure_semaphore(self) -> asyncio.Semaphore | None:
        """Ensure we have a Semaphore bound to the current event loop."""
        if self._concurrent_limit <= 0:
            return None
        loop_id = self._get_current_loop_id()
        if self._semaphore_loop_id != loop_id:
            self._semaphore = asyncio.Semaphore(self._concurrent_limit)
            self._semaphore_loop_id = loop_id
        return self._semaphore

    def set_concurrent_limit(self, limit: int):
        """Set the maximum number of concurrent requests allowed."""
        if limit != self._concurrent_limit:
            self._concurrent_limit = limit
            self._semaphore = None  # Reset to be recreated lazily

    async def acquire(self, callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None):
        """Acquire a semaphore slot, waiting if concurrent limit is reached."""
        semaphore = self._ensure_semaphore()
        if semaphore:
            if semaphore._value == 0 and callback:
                total = self._concurrent_limit - semaphore._value
                msg = f"Concurrent request limit reached ({total}/{self._concurrent_limit}), waiting..."
                await callback(msg, "concurrent", total, self._concurrent_limit)
            await semaphore.acquire()

    def release(self):
        """Release a semaphore slot, allowing another request to proceed."""
        semaphore = self._semaphore  # Use cached, don't create new
        if semaphore:
            try:
                semaphore.release()
            except ValueError:
                pass

    def add(self, **kwargs: int):
        now = time.time()
        for key, value in kwargs.items():
            if not key in self.values:
                self.values[key] = []
            self.values[key].append((now, value))

    async def cleanup(self):
        async with self._lock:
            now = time.time()
            cutoff = now - self.timeframe
            for key in self.values:
                self.values[key] = [(t, v) for t, v in self.values[key] if t > cutoff]

    async def get_total(self, key: str) -> int:
        async with self._lock:
            if not key in self.values:
                return 0
            return sum(value for _, value in self.values[key])

    async def wait(
        self,
        callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
    ):
        while True:
            await self.cleanup()
            should_wait = False

            for key, limit in self.limits.items():
                if limit <= 0:  # Skip if no limit set
                    continue

                total = await self.get_total(key)
                if total > limit:
                    if callback:
                        msg = f"Rate limit exceeded for {key} ({total}/{limit}), waiting..."
                        should_wait = not await callback(msg, key, total, limit)
                    else:
                        should_wait = True
                    break

            if not should_wait:
                break

            await asyncio.sleep(1)
