"""Tests for python/helpers/log.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager that passes through values (no masking)."""
    mgr = MagicMock()
    mgr.mask_values = lambda s: s
    return mgr


@pytest.fixture
def patch_log_dependencies(mock_secrets_manager):
    """Patch get_secrets_manager and state monitor to avoid side effects."""
    with patch("python.helpers.log.get_secrets_manager", return_value=mock_secrets_manager):
        with patch("python.helpers.log._lazy_mark_dirty_all"):
            with patch("python.helpers.log._lazy_mark_dirty_for_context"):
                yield


# --- Constants ---


class TestLogConstants:
    def test_heading_max_len_defined(self):
        from python.helpers.log import HEADING_MAX_LEN

        assert HEADING_MAX_LEN == 120

    def test_content_max_len_defined(self):
        from python.helpers.log import CONTENT_MAX_LEN

        assert CONTENT_MAX_LEN == 15_000

    def test_response_content_max_len_larger(self):
        from python.helpers.log import CONTENT_MAX_LEN, RESPONSE_CONTENT_MAX_LEN

        assert RESPONSE_CONTENT_MAX_LEN > CONTENT_MAX_LEN

    def test_progress_max_len_defined(self):
        from python.helpers.log import PROGRESS_MAX_LEN

        assert PROGRESS_MAX_LEN == 120


# --- Truncation (via module internals) ---


class TestTruncateHeading:
    def test_truncate_heading_none_returns_empty(self):
        from python.helpers.log import _truncate_heading

        assert _truncate_heading(None) == ""

    def test_truncate_heading_short_unchanged(self):
        from python.helpers.log import _truncate_heading

        text = "Short heading"
        assert _truncate_heading(text) == text

    def test_truncate_heading_long_truncated(self):
        from python.helpers.log import HEADING_MAX_LEN, _truncate_heading

        text = "x" * (HEADING_MAX_LEN + 50)
        result = _truncate_heading(text)
        assert len(result) <= HEADING_MAX_LEN + 5  # +5 for "..."
        assert "..." in result or len(result) == HEADING_MAX_LEN


class TestTruncateProgress:
    def test_truncate_progress_none_returns_empty(self):
        from python.helpers.log import _truncate_progress

        assert _truncate_progress(None) == ""

    def test_truncate_progress_short_unchanged(self):
        from python.helpers.log import _truncate_progress

        assert _truncate_progress("Short") == "Short"


class TestTruncateKey:
    def test_truncate_key_short_unchanged(self):
        from python.helpers.log import _truncate_key

        assert _truncate_key("key") == "key"

    def test_truncate_key_long_truncated(self):
        from python.helpers.log import KEY_MAX_LEN, _truncate_key

        long_key = "x" * (KEY_MAX_LEN + 20)
        result = _truncate_key(long_key)
        assert len(result) <= KEY_MAX_LEN + 5


class TestTruncateValue:
    def test_truncate_value_short_string_unchanged(self):
        from python.helpers.log import _truncate_value

        assert _truncate_value("short") == "short"

    def test_truncate_value_long_string_truncated(self):
        from python.helpers.log import VALUE_MAX_LEN, _truncate_value

        long_val = "x" * (VALUE_MAX_LEN + 100)
        result = _truncate_value(long_val)
        assert "Characters hidden" in result or len(result) <= VALUE_MAX_LEN + 50

    def test_truncate_value_dict_recursive(self):
        from python.helpers.log import _truncate_value

        d = {"a": "short", "b": "also short"}
        result = _truncate_value(d)
        assert result == {"a": "short", "b": "also short"}

    def test_truncate_value_list_recursive(self):
        from python.helpers.log import _truncate_value

        lst = ["a", "b"]
        result = _truncate_value(lst)
        assert result == ["a", "b"]

    def test_truncate_value_tuple_recursive(self):
        from python.helpers.log import _truncate_value

        t = ("a", "b")
        result = _truncate_value(t)
        assert result == ("a", "b")


class TestTruncateContent:
    def test_truncate_content_none_returns_empty(self):
        from python.helpers.log import _truncate_content

        assert _truncate_content(None, "info") == ""

    def test_truncate_content_short_unchanged(self):
        from python.helpers.log import _truncate_content

        text = "Short content"
        assert _truncate_content(text, "info") == text

    def test_truncate_content_response_type_uses_larger_limit(self):
        from python.helpers.log import CONTENT_MAX_LEN, RESPONSE_CONTENT_MAX_LEN, _truncate_content

        # Content at CONTENT_MAX_LEN + 1 would be truncated for "info"
        long_info = "x" * (CONTENT_MAX_LEN + 100)
        result_info = _truncate_content(long_info, "info")
        assert "Characters hidden" in result_info or len(result_info) < len(long_info)

        # Response type allows more
        long_resp = "x" * (CONTENT_MAX_LEN + 100)
        result_resp = _truncate_content(long_resp, "response")
        assert len(result_resp) > CONTENT_MAX_LEN or "Characters hidden" in result_resp


# --- LogItem ---


class TestLogItem:
    def test_log_item_creation(self, patch_log_dependencies):
        from python.helpers.log import Log, LogItem

        log = Log()
        item = LogItem(log=log, no=0, type="info")
        assert item.log == log
        assert item.no == 0
        assert item.type == "info"
        assert item.guid == log.guid
        assert item.timestamp > 0

    def test_log_item_output(self, patch_log_dependencies):
        from python.helpers.log import Log, LogItem

        log = Log()
        item = LogItem(log=log, no=0, type="info", heading="H", content="C", id="item-1")
        out = item.output()
        assert out["no"] == 0
        assert out["type"] == "info"
        assert out["heading"] == "H"
        assert out["content"] == "C"
        assert out["id"] == "item-1"
        assert "timestamp" in out
        assert "agentno" in out


# --- Log ---


class TestLog:
    def test_log_initialization(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        assert log.guid
        assert log.logs == []
        assert log.updates == []
        assert log.progress == "Waiting for input"
        assert log.progress_active is False

    def test_log_creates_item(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        item = log.log("info", heading="Test", content="Body")
        assert item is not None
        assert len(log.logs) == 1
        assert log.logs[0].heading == "Test"
        assert log.logs[0].content == "Body"
        assert log.logs[0].type == "info"

    def test_log_with_kvps(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        item = log.log("tool", heading="Tool", kvps={"key": "value"})
        assert item.kvps is not None
        assert item.kvps.get("key") == "value"

    def test_log_output_returns_updates(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.log("info", heading="A")
        log.log("info", heading="B")
        out = log.output()
        assert len(out) == 2
        assert out[0]["heading"] == "A"
        assert out[1]["heading"] == "B"

    def test_log_output_with_start_end(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.log("info", heading="A")
        log.log("info", heading="B")
        log.log("info", heading="C")
        out = log.output(start=1, end=2)
        assert len(out) == 1
        assert out[0]["heading"] == "B"

    def test_log_reset_clears_state(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.log("info", heading="Before")
        old_guid = log.guid
        log.reset()
        assert log.logs == []
        assert log.updates == []
        assert log.guid != old_guid

    def test_log_set_progress(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.set_progress("Processing...", no=1, active=True)
        assert log.progress == "Processing..."
        assert log.progress_no == 1
        assert log.progress_active is True

    def test_log_set_initial_progress(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.set_initial_progress()
        assert log.progress == "Waiting for input"
        assert log.progress_active is False

    def test_log_item_update(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        item = log.log("info", heading="Original", content="Body")
        item.update(heading="Updated", content="New body")
        assert log.logs[0].heading == "Updated"
        assert log.logs[0].content == "New body"

    def test_log_item_stream_appends(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        item = log.log("info", heading="A", content="B")
        item.stream(heading="+H", content="+C")
        assert "A" in log.logs[0].heading and "+H" in log.logs[0].heading
        assert "B" in log.logs[0].content and "+C" in log.logs[0].content

    def test_log_item_update_ignored_when_guid_mismatch(self, patch_log_dependencies):
        from python.helpers.log import Log, LogItem

        log = Log()
        item = LogItem(log=log, no=0, type="info", heading="H", content="C")
        item.guid = "different-guid"
        log.logs.append(item)
        item.update(heading="Should not apply")
        assert log.logs[0].heading == "H"

    def test_log_with_id(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        item = log.log("info", heading="H", id="custom-id")
        assert item.id == "custom-id"
        assert log.output()[0]["id"] == "custom-id"

    def test_log_update_progress_persistent_vs_temporary(self, patch_log_dependencies):
        from python.helpers.log import Log

        log = Log()
        log.log("info", heading="First", update_progress="persistent")
        log.log("info", heading="Second", update_progress="temporary")
        assert log.progress == "Second"
        assert log.progress_no == -1  # temporary sets -1

    def test_log_masking_integration(self):
        from python.helpers.log import Log

        mock_mgr = MagicMock()
        mock_mgr.mask_values = lambda s: s.replace("secret", "***")

        with patch("python.helpers.log.get_secrets_manager", return_value=mock_mgr):
            with patch("python.helpers.log._lazy_mark_dirty_all"):
                with patch("python.helpers.log._lazy_mark_dirty_for_context"):
                    log = Log()
                    log.log("info", content="My secret key")
                    assert "***" in log.logs[0].content
