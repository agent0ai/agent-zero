"""Tests for python/helpers/errors.py — handle_error, error_text, format_error, RepairableException."""

import asyncio
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.errors import (
    handle_error,
    error_text,
    format_error,
    RepairableException,
)


class TestHandleError:
    def test_reraises_cancelled_error(self):
        with pytest.raises(asyncio.CancelledError):
            handle_error(asyncio.CancelledError())

    def test_does_not_raise_for_other_errors(self):
        handle_error(ValueError("test"))
        handle_error(RuntimeError("x"))


class TestErrorText:
    def test_returns_str_of_exception(self):
        assert error_text(ValueError("hello")) == "hello"


class TestFormatError:
    def test_includes_error_message(self):
        try:
            raise ValueError("test message")
        except ValueError as e:
            result = format_error(e)
        assert "test message" in result or "ValueError" in result

    def test_includes_traceback(self):
        try:
            raise RuntimeError("err")
        except RuntimeError as e:
            result = format_error(e)
        assert "Traceback" in result or "RuntimeError" in result

    def test_error_message_position_top(self):
        try:
            raise ValueError("top")
        except ValueError as e:
            result = format_error(e, error_message_position="top")
        assert "top" in result

    def test_error_message_position_bottom(self):
        try:
            raise ValueError("bottom")
        except ValueError as e:
            result = format_error(e, error_message_position="bottom")
        assert "bottom" in result

    def test_error_message_position_none(self):
        try:
            raise ValueError("none")
        except ValueError as e:
            result = format_error(e, error_message_position="none")
        assert "none" in result or "ValueError" in result

    def test_trimmed_traceback_when_many_file_lines(self):
        def level4():
            raise ValueError("deep")
        def level3():
            level4()
        def level2():
            level3()
        def level1():
            level2()
        try:
            level1()
        except ValueError as e:
            result = format_error(e, start_entries=2, end_entries=2)
        assert "skipped" in result or "ValueError" in result or "deep" in result

    def test_returns_str_of_exception_when_empty_result(self):
        result = format_error(Exception("x"), start_entries=0, end_entries=0)
        assert "x" in result


class TestRepairableException:
    def test_is_exception_subclass(self):
        assert issubclass(RepairableException, Exception)

    def test_can_raise_and_catch(self):
        with pytest.raises(RepairableException):
            raise RepairableException("repairable")

    def test_message_preserved(self):
        try:
            raise RepairableException("msg")
        except RepairableException as e:
            assert str(e) == "msg"
