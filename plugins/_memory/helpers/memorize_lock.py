"""Shared lock serializing memory post-processing utility jobs.

_50_memorize_fragments and _51_memorize_solutions both run heavyweight
utility-model requests asynchronously on the shared background event loop.
Running them concurrently means two long-held, non-streaming provider
requests at once, which providers may truncate or rate-limit. The lock is
created lazily inside the loop that first uses it and recreated when the
running loop changes, because an asyncio.Lock is bound to the loop it was
first used on: if the background loop is terminated and recreated (see
EventLoopThread.terminate), a stale lock would either raise "bound to a
different event loop" or hang forever if it was left locked.
"""

import asyncio

_lock: asyncio.Lock | None = None
_lock_loop: asyncio.AbstractEventLoop | None = None


def get_memorize_lock() -> asyncio.Lock:
    global _lock, _lock_loop
    try:
        loop: asyncio.AbstractEventLoop | None = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if _lock is None or loop is not _lock_loop:
        _lock = asyncio.Lock()
        _lock_loop = loop
    return _lock


def format_utility_error(exc: Exception) -> str:
    """Provider-aware error text: status code first when the API supplied one."""
    from helpers import errors

    err = errors.format_error(exc)
    status = getattr(exc, "status_code", None)
    if status is not None:
        return f"Provider status {status}: {err}"
    return err
