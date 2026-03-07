"""Gateway: queue-based message routing for all channel adapters.

Replaces synchronous routing with async queue processing backed by
``MessageQueue`` (retry + dead-letter) and ``MessageStore`` (audit).

Backward-compatible helpers ``route_message`` and ``route_message_sync``
are provided for callers that still expect a direct-call interface.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable  # noqa: TCH003
from typing import Any

from python.helpers.channel_bridge import NormalizedMessage  # noqa: TCH001
from python.helpers.channel_factory import ChannelFactory
from python.helpers.message_queue import MessageQueue
from python.helpers.message_store import MessageStore

logger = logging.getLogger(__name__)

# Module-level singletons -- initialised lazily via ``init()``.
_queue: MessageQueue | None = None
_store: MessageStore | None = None

# User-supplied callback that actually processes a NormalizedMessage and
# returns a response string.  Set via ``set_processor()``.
_processor: Callable[[NormalizedMessage], Awaitable[str]] | None = None


# ------------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------------


def init(
    *,
    max_queue_size: int = 1000,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    db_path: str | None = None,
) -> None:
    """Initialise the gateway queue and message store.

    Safe to call multiple times -- subsequent calls are no-ops.
    """
    global _queue, _store

    if _queue is None:
        _queue = MessageQueue(
            max_size=max_queue_size,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        _queue.set_handler(_handle_message)

    if _store is None:
        _store = MessageStore(db_path=db_path)


def set_processor(
    processor: Callable[[NormalizedMessage], Awaitable[str]],
) -> None:
    """Register the application-level message processor.

    The *processor* receives a ``NormalizedMessage`` and must return the
    response string.  It is invoked inside the queue worker loop.
    """
    global _processor
    _processor = processor


# ------------------------------------------------------------------
# Queue lifecycle
# ------------------------------------------------------------------


async def start() -> None:
    """Start the queue worker.  Call ``init()`` first."""
    _ensure_init()
    assert _queue is not None
    await _queue.start()
    logger.info("Gateway queue started")


async def stop() -> None:
    """Gracefully stop the queue worker."""
    if _queue is not None:
        await _queue.stop()
        logger.info("Gateway queue stopped")


# ------------------------------------------------------------------
# Routing (preferred async path)
# ------------------------------------------------------------------


async def route_message(message: NormalizedMessage) -> None:
    """Enqueue a NormalizedMessage for async processing.

    This is the primary entry point for all adapters.
    """
    _ensure_init()
    assert _queue is not None
    await _queue.enqueue(message)


def route_message_sync(message: NormalizedMessage) -> None:
    """Fire-and-forget helper for synchronous callers.

    Creates or reuses an event loop to enqueue the message.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(route_message(message))
    except RuntimeError:
        asyncio.run(route_message(message))


# ------------------------------------------------------------------
# Direct processing (backward-compat / webhook shortcut)
# ------------------------------------------------------------------


async def process_now(message: NormalizedMessage) -> str:
    """Process a message immediately (bypass the queue).

    Useful for webhook handlers that must return the response in the
    same HTTP request.  The message is still persisted in the store.
    """
    _ensure_init()
    return await _handle_message(message)


# ------------------------------------------------------------------
# Introspection
# ------------------------------------------------------------------


def stats() -> dict[str, Any]:
    """Return queue + store statistics."""
    result: dict[str, Any] = {"initialised": _queue is not None}
    if _queue is not None:
        result.update(_queue.stats())
    return result


def get_store() -> MessageStore | None:
    """Return the active ``MessageStore`` instance (or ``None``)."""
    return _store


# ------------------------------------------------------------------
# Internals
# ------------------------------------------------------------------


async def _handle_message(message: NormalizedMessage) -> str:
    """Core handler invoked by the queue worker (or ``process_now``)."""
    assert _store is not None

    if _processor is None:
        err = "No processor registered -- call gateway.set_processor() first"
        logger.error(err)
        _store.store(message, response=f"[ERROR] {err}")
        raise RuntimeError(err)

    try:
        response = await _processor(message)
    except Exception as exc:
        logger.error("Processor failed for message %s: %s", message.id, exc)
        _store.store(message, response=f"[ERROR] {exc}")
        raise

    _store.store(message, response=response)
    logger.debug("Message %s processed and stored", message.id)

    # Attempt to send the response back through the originating adapter.
    adapter_cls = ChannelFactory.get_adapter_class(message.channel)
    if adapter_cls is not None and message.sender_id:
        try:
            adapter = ChannelFactory.create(message.channel)
            await adapter.send(message.sender_id, response)
        except Exception as exc:
            logger.warning(
                "Failed to send response for %s via %s: %s",
                message.id,
                message.channel,
                exc,
            )

    return response


def _ensure_init() -> None:
    if _queue is None or _store is None:
        init()
