"""Shared lock serializing memory post-processing utility jobs.

_50_memorize_fragments and _51_memorize_solutions both run heavyweight
utility-model requests asynchronously on the shared background event loop.
Running them concurrently means two long-held, non-streaming provider
requests at once, which providers may truncate or rate-limit. The lock is
created lazily inside the loop that first uses it.
"""

import asyncio

_lock: asyncio.Lock | None = None


def get_memorize_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


def format_utility_error(exc: Exception) -> str:
    """Provider-aware error text: status code first when the API supplied one."""
    from helpers import errors

    err = errors.format_error(exc)
    status = getattr(exc, "status_code", None)
    if status is not None:
        return f"Provider status {status}: {err}"
    return err
