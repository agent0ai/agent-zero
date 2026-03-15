"""Tests for python/helpers/print_catch.py."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestCapturePrintsAsync:
    @pytest.mark.asyncio
    async def test_captures_stdout(self):
        from python.helpers.print_catch import capture_prints_async

        async def print_hello():
            print("hello", end="")
            return "done"

        task, get_output = capture_prints_async(print_hello)
        result = await task
        assert result == "done"
        assert get_output() == "hello"

    @pytest.mark.asyncio
    async def test_captures_multiple_prints(self):
        from python.helpers.print_catch import capture_prints_async

        async def print_multi():
            print("a", end="")
            print("b", end="")
            return None

        task, get_output = capture_prints_async(print_multi)
        await task
        assert get_output() == "ab"

    @pytest.mark.asyncio
    async def test_restores_stdout_on_exception(self):
        from python.helpers.print_catch import capture_prints_async

        original_stdout = sys.stdout

        async def raise_error():
            print("before")
            raise ValueError("oops")

        task, get_output = capture_prints_async(raise_error)
        with pytest.raises(ValueError):
            await task
        assert sys.stdout is original_stdout

    @pytest.mark.asyncio
    async def test_get_output_returns_current_value(self):
        from python.helpers.print_catch import capture_prints_async

        async def print_incremental():
            print("1", end="")
            return "ok"

        task, get_output = capture_prints_async(print_incremental)
        # Before await, output may be empty or partial
        await task
        assert get_output() == "1"

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        from python.helpers.print_catch import capture_prints_async

        async def add(a, b):
            print(f"{a}+{b}", end="")
            return a + b

        task, get_output = capture_prints_async(add, 2, 3)
        result = await task
        assert result == 5
        assert get_output() == "2+3"
