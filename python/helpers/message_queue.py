"""Async message queue with dead-letter support.

Provides backpressure handling (configurable max size), automatic retry
with exponential back-off, and a dead-letter queue for messages that
exceed the maximum retry count.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from python.helpers.channel_bridge import NormalizedMessage

logger = logging.getLogger(__name__)

# Type alias for the async handler invoked per message.
MessageHandler = Callable[[NormalizedMessage], Awaitable[str]]


@dataclass
class QueueEntry:
    """Wraps a NormalizedMessage with retry metadata."""

    message: NormalizedMessage
    retries: int = 0
    enqueued_at: float = field(default_factory=time.time)
    last_error: str | None = None


class MessageQueue:
    """Async message queue with dead-letter support.

    Parameters
    ----------
    max_size:
        Maximum number of messages allowed in the main queue before
        backpressure kicks in (new ``enqueue`` calls will block).
    max_retries:
        How many times a failed message is re-tried before being moved
        to the dead-letter queue.
    retry_delay:
        Base delay in seconds between retries (doubled each attempt).
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.max_size = max_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._queue: asyncio.Queue[QueueEntry] = asyncio.Queue(maxsize=max_size)
        self._dead_letters: list[QueueEntry] = []
        self._handler: MessageHandler | None = None
        self._running = False
        self._worker_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def set_handler(self, handler: MessageHandler) -> None:
        """Set the async callable that processes each message."""
        self._handler = handler

    async def enqueue(self, message: NormalizedMessage) -> None:
        """Add a message to the queue.

        Blocks (with backpressure) if the queue has reached *max_size*.
        """
        entry = QueueEntry(message=message)
        await self._queue.put(entry)
        logger.debug("Enqueued message %s (queue size: %d)", message.id, self._queue.qsize())

    async def start(self) -> None:
        """Start the background worker loop."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("MessageQueue worker started (max_size=%d)", self.max_size)

    async def stop(self) -> None:
        """Gracefully stop the worker loop."""
        self._running = False
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        logger.info("MessageQueue worker stopped")

    @property
    def dead_letters(self) -> list[QueueEntry]:
        """Return a *copy* of the dead-letter list."""
        return list(self._dead_letters)

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def dead_letter_count(self) -> int:
        return len(self._dead_letters)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    async def _worker_loop(self) -> None:
        """Continuously process entries from the queue."""
        while self._running:
            try:
                entry = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            await self._process_entry(entry)
            self._queue.task_done()

    async def _process_entry(self, entry: QueueEntry) -> None:
        """Attempt to process a single entry; retry or dead-letter on failure."""
        if self._handler is None:
            logger.error("No handler set -- moving message %s to dead-letter", entry.message.id)
            entry.last_error = "No handler configured"
            self._dead_letters.append(entry)
            return

        try:
            await self._handler(entry.message)
            logger.debug("Processed message %s", entry.message.id)
        except Exception as exc:
            entry.retries += 1
            entry.last_error = str(exc)
            logger.warning(
                "Handler failed for %s (attempt %d/%d): %s",
                entry.message.id,
                entry.retries,
                self.max_retries,
                exc,
            )
            if entry.retries >= self.max_retries:
                logger.error("Message %s moved to dead-letter after %d retries", entry.message.id, entry.retries)
                self._dead_letters.append(entry)
            else:
                delay = self.retry_delay * (2 ** (entry.retries - 1))
                await asyncio.sleep(delay)
                await self._queue.put(entry)

    # ------------------------------------------------------------------
    # introspection helpers
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        return {
            "pending": self.pending_count,
            "dead_letters": self.dead_letter_count,
            "running": self._running,
            "max_size": self.max_size,
            "max_retries": self.max_retries,
        }
