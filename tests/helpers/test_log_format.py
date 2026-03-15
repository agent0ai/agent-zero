"""Tests for python/helpers/log_format.py."""

import logging
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestFormatPrefix:
    def test_default_values(self):
        from python.helpers.log_format import format_prefix

        result = format_prefix()
        assert "INFO" in result
        assert "[a0]" in result
        assert "T" in result  # RFC 3339 timestamp
        assert "Z" in result  # UTC

    def test_custom_level_and_component(self):
        from python.helpers.log_format import format_prefix

        result = format_prefix(level="ERROR", component="a0.addon")
        assert "ERROR" in result
        assert "[a0.addon]" in result


class TestStructuredFormatter:
    def test_format_record(self):
        from python.helpers.log_format import StructuredFormatter

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="a0.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "a0.test" in result
        assert "test message" in result
        assert "INFO" in result
        assert "T" in result and "Z" in result

    def test_format_record_with_exception(self):
        from python.helpers.log_format import StructuredFormatter

        formatter = StructuredFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="a0.test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="failed",
            args=(),
            exc_info=exc_info,
        )
        result = formatter.format(record)
        assert "failed" in result
        assert "ValueError" in result
        assert "test error" in result


class TestConfigureLogging:
    def test_clears_handlers_and_adds_structured(self):
        from python.helpers.log_format import configure_logging

        configure_logging(root_level=logging.DEBUG)
        root = logging.getLogger()
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        from python.helpers.log_format import StructuredFormatter

        assert isinstance(handler.formatter, StructuredFormatter)

    def test_uvicorn_loggers_configured(self):
        from python.helpers.log_format import configure_logging

        configure_logging(root_level=logging.WARNING)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            lg = logging.getLogger(name)
            assert lg.propagate is False
            assert len(lg.handlers) >= 1
