"""Tests for python/helpers/security.py — safe_filename, forbidden chars, Windows reserved names."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.security import (
    safe_filename,
    FORBIDDEN_CHARS_RE,
    WINDOWS_RESERVED,
    FILENAME_MAX_LENGTH,
)


class TestForbiddenChars:
    def test_forbidden_chars_rejects_slash(self):
        assert FORBIDDEN_CHARS_RE.search("path/to/file") is not None

    def test_forbidden_chars_rejects_null(self):
        assert FORBIDDEN_CHARS_RE.search("file\x00name") is not None

    def test_forbidden_chars_rejects_windows_chars(self):
        assert FORBIDDEN_CHARS_RE.search("file<name>") is not None
        assert FORBIDDEN_CHARS_RE.search("file:name") is not None
        assert FORBIDDEN_CHARS_RE.search('file"name') is not None
        assert FORBIDDEN_CHARS_RE.search("file|name") is not None
        assert FORBIDDEN_CHARS_RE.search("file?name") is not None
        assert FORBIDDEN_CHARS_RE.search("file*name") is not None

    def test_forbidden_chars_allows_safe_chars(self):
        assert FORBIDDEN_CHARS_RE.search("valid_file-123.txt") is None


class TestWindowsReserved:
    def test_con_in_reserved(self):
        assert "CON" in WINDOWS_RESERVED

    def test_com1_in_reserved(self):
        assert "COM1" in WINDOWS_RESERVED

    def test_lpt1_in_reserved(self):
        assert "LPT1" in WINDOWS_RESERVED


class TestSafeFilename:
    def test_safe_filename_replaces_forbidden_chars(self):
        assert safe_filename("file/name.txt") == "file_name.txt"
        assert safe_filename("file:name.txt") == "file_name.txt"

    def test_safe_filename_strips_leading_trailing_spaces(self):
        assert safe_filename("  file.txt  ") == "file.txt"

    def test_safe_filename_strips_trailing_dots(self):
        assert safe_filename("file...") == "file"

    def test_safe_filename_normalizes_unicode(self):
        result = safe_filename("café.txt")
        assert result is not None
        assert "é" in result or "_" in result

    def test_safe_filename_handles_windows_reserved(self):
        result = safe_filename("CON.txt")
        assert result is not None
        assert result != "CON.txt"
        assert "CON" in result

    def test_safe_filename_truncates_long_names(self):
        long_name = "a" * 300 + ".txt"
        result = safe_filename(long_name)
        assert result is not None
        assert len(result) <= FILENAME_MAX_LENGTH

    def test_safe_filename_returns_none_for_empty(self):
        assert safe_filename("") is None
        assert safe_filename("   ") is None
        assert safe_filename("...") is None

    def test_safe_filename_preserves_valid_names(self):
        assert safe_filename("document.pdf") == "document.pdf"
        assert safe_filename("my_file-123.txt") == "my_file-123.txt"
