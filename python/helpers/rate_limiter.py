import asyncio
import threading
import time
from typing import Callable, Awaitable


class RateLimiter:
    def __init__(self, seconds: int = 60, **limits: int):
        self.timeframe = seconds
        self.limits = {key: value if isinstance(value, (int, float)) else 0 for key, value in (limits or {}).items()}
        self.values = {key: [] for key in self.limits.keys()}
        self._lock = asyncio.Lock()
        self._concurrent_limit = 0
        self._semaphore = threading.Semaphore(0)

    def set_concurrent_limit(self, limit: int):
        """Set the maximum number of concurrent requests allowed."""
        if limit != self._concurrent_limit:
            self._concurrent_limit = limit
            self._semaphore = threading.Semaphore(self._concurrent_limit)

    async def acquire(self, callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None) -> threading.Semaphore | None:
        """Acquire a semaphore slot, waiting if concurrent limit is reached. Returns the semaphore for release."""
        if self._concurrent_limit <= 0:
            return None
        semaphore = self._semaphore
        if semaphore._value == 0 and callback:
            total = self._concurrent_limit - semaphore._value
            msg = f"Concurrent request limit reached ({total}/{self._concurrent_limit}), waiting..."
            await callback(msg, "concurrent", total, self._concurrent_limit)
        await asyncio.to_thread(semaphore.acquire)
        return semaphore

    def release(self, semaphore: threading.Semaphore | None):
        """Release a semaphore slot on the specific semaphore that was acquired."""
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
