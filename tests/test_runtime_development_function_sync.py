from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import helpers.runtime as runtime


async def _double(value: int) -> int:
    return value * 2


async def _boom() -> None:
    raise ValueError("boom from delegated call")


@pytest.fixture(autouse=True)
def _local_transport(monkeypatch):
    """Pin the underlying transport so the sync wrapper is tested offline and deterministically."""

    async def fake_call(func, *args, **kwargs):
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    monkeypatch.setattr(runtime, "call_development_function", fake_call)


def test_call_development_function_sync_returns_result():
    assert runtime.call_development_function_sync(_double, 21) == 42


def test_call_development_function_sync_propagates_original_error():
    # A failed delegated call must surface its own error, not queue.Empty.
    with pytest.raises(ValueError, match="boom from delegated call"):
        runtime.call_development_function_sync(_boom)
