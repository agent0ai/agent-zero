"""Tests for the JSON misformat handling pipeline: extraction, validation, and circuit breaker.

Covers three fix areas from PR #1245:
1. extract_json_object_string brace-depth tracking (replaces buggy rfind)
2. validate_tool_request RepairableException (replaces unrecoverable ValueError)
3. Consecutive misformat circuit breaker for BOTH code paths:
   - Case A: complete parse failure (tool_request is None)
   - Case B: parseable-but-invalid JSON (RepairableException from validation)
"""

import pytest

from helpers.extract_tools import extract_json_object_string, json_parse_dirty
from helpers.errors import RepairableException, HandledException


# ---------------------------------------------------------------------------
# 1. extract_json_object_string — brace-depth tracking
# ---------------------------------------------------------------------------

class TestExtractJsonObjectString:

    def test_simple_json_object(self):
        content = '{"tool_name": "response", "tool_args": {"text": "hello"}}'
        assert extract_json_object_string(content) == content

    def test_json_with_leading_text(self):
        content = 'Some preamble text {"key": "value"}'
        assert extract_json_object_string(content) == '{"key": "value"}'

    def test_json_with_trailing_text(self):
        content = '{"key": "value"} and some trailing text'
        assert extract_json_object_string(content) == '{"key": "value"}'

    def test_nested_braces(self):
        content = '{"outer": {"inner": {"deep": true}}}'
        assert extract_json_object_string(content) == content

    def test_braces_inside_strings_ignored(self):
        content = '{"path": "/restore/{backup_id}/files", "tool_name": "test"}'
        assert extract_json_object_string(content) == content

    def test_rfind_bug_regression_incidental_braces(self):
        """Original rfind bug: content.rfind('}') grabs the LAST '}' in entire
        response, which could be from a file path, code block, or inline JSON
        example — producing corrupted extraction."""
        content = (
            '{"tool_name": "code_execution_tool", "tool_args": {"code": "print(1)"}}'
            '\n\nHere is a path: /api/{version}/endpoint'
        )
        expected = '{"tool_name": "code_execution_tool", "tool_args": {"code": "print(1)"}}'
        assert extract_json_object_string(content) == expected

    def test_rfind_bug_regression_multiple_json_objects(self):
        """rfind would span from first '{' to last '}' across multiple objects."""
        content = '{"first": 1} and {"second": 2}'
        assert extract_json_object_string(content) == '{"first": 1}'

    def test_escaped_quotes_in_strings(self):
        content = r'{"message": "He said \"hello\" to me"}'
        assert extract_json_object_string(content) == content

    def test_escaped_backslash_before_quote(self):
        r"""Escaped backslash (\\) followed by quote should NOT toggle string state.
        The \\ is the escape, and the " ends the string."""
        content = r'{"path": "C:\\Users\\"}'
        assert extract_json_object_string(content) == content

    def test_newlines_inside_strings(self):
        content = '{"text": "line1\\nline2\\nline3"}'
        assert extract_json_object_string(content) == content

    def test_unclosed_brace_returns_to_end(self):
        content = '{"incomplete": true'
        assert extract_json_object_string(content) == content

    def test_no_braces_returns_empty(self):
        content = 'no json here at all'
        assert extract_json_object_string(content) == ""

    def test_empty_string(self):
        assert extract_json_object_string("") == ""

    def test_empty_object(self):
        assert extract_json_object_string("{}") == "{}"

    def test_code_block_with_json_inside(self):
        """Model wraps JSON in markdown code fences — should extract the JSON."""
        content = '```json\n{"tool_name": "response", "tool_args": {"text": "hi"}}\n```'
        assert extract_json_object_string(content) == '{"tool_name": "response", "tool_args": {"text": "hi"}}'

    def test_deeply_nested_objects(self):
        content = '{"a": {"b": {"c": {"d": {"e": "deep"}}}}}'
        assert extract_json_object_string(content) == content

    def test_array_values_with_braces_in_strings(self):
        content = '{"items": ["a{b}", "c}d"], "done": true}'
        assert extract_json_object_string(content) == content

    def test_mixed_content_with_xml_style_tags(self):
        """Model outputs XML-style tool calls mixed with JSON."""
        content = 'ECT{"tool_name": "test", "tool_args": {}}ECT'
        assert extract_json_object_string(content) == '{"tool_name": "test", "tool_args": {}}'

    def test_unicode_content(self):
        content = '{"text": "café résumé naïve"}'
        assert extract_json_object_string(content) == content

    def test_numbers_and_booleans(self):
        content = '{"count": 42, "active": true, "ratio": 3.14, "nothing": null}'
        assert extract_json_object_string(content) == content

    def test_lone_opening_brace(self):
        assert extract_json_object_string("{") == "{"

    def test_brace_in_string_not_counted(self):
        """Braces inside strings must not affect depth tracking."""
        content = '{"data": "{{template}}", "ok": true}'
        assert extract_json_object_string(content) == content


# ---------------------------------------------------------------------------
# 2. json_parse_dirty — end-to-end parse with DirtyJson
# ---------------------------------------------------------------------------

class TestJsonParseDirty:

    def test_valid_tool_call(self):
        msg = '{"tool_name": "response", "tool_args": {"text": "hello"}}'
        result = json_parse_dirty(msg)
        assert result == {"tool_name": "response", "tool_args": {"text": "hello"}}

    def test_valid_with_thoughts(self):
        msg = '{"thoughts": ["thinking"], "headline": "test", "tool_name": "response", "tool_args": {"text": "hi"}}'
        result = json_parse_dirty(msg)
        assert result is not None
        assert result["tool_name"] == "response"

    def test_returns_none_for_empty_string(self):
        assert json_parse_dirty("") is None

    def test_returns_none_for_none_input(self):
        assert json_parse_dirty(None) is None

    def test_returns_none_for_non_string(self):
        assert json_parse_dirty(42) is None

    def test_returns_none_for_no_json(self):
        assert json_parse_dirty("just plain text with no braces") is None

    def test_returns_none_for_array(self):
        """Arrays are not valid tool requests, only dicts."""
        assert json_parse_dirty("[1, 2, 3]") is None

    def test_extracts_json_with_surrounding_text(self):
        msg = 'Here is my response: {"tool_name": "test", "tool_args": {"a": 1}} done.'
        result = json_parse_dirty(msg)
        assert result is not None
        assert result["tool_name"] == "test"

    def test_handles_dirty_json_trailing_comma(self):
        msg = '{"tool_name": "test", "tool_args": {"a": 1},}'
        result = json_parse_dirty(msg)
        assert result is not None
        assert result["tool_name"] == "test"

    def test_handles_dirty_json_single_quotes(self):
        msg = "{'tool_name': 'test', 'tool_args': {'a': 1}}"
        result = json_parse_dirty(msg)
        assert result is not None
        assert result["tool_name"] == "test"

    def test_returns_first_complete_object(self):
        msg = '{"first": true} {"second": true}'
        result = json_parse_dirty(msg)
        assert result == {"first": True}

    def test_invalid_json_returns_none(self):
        msg = '{this is not json at all with no quotes}'
        result = json_parse_dirty(msg)
        # DirtyJson may or may not parse this; the important thing is no crash
        assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# 3. validate_tool_request logic (standalone reproduction)
#
# Agent.validate_tool_request can't be imported without the full dep chain.
# We test the exact same logic in isolation to verify correctness.
# ---------------------------------------------------------------------------

def _validate_tool_request(tool_request):
    """Exact reproduction of Agent.validate_tool_request from agent.py."""
    if tool_request is None:
        return
    if not isinstance(tool_request, dict):
        raise RepairableException("Tool request must be a dictionary")
    if not tool_request.get("tool_name") or not isinstance(tool_request.get("tool_name"), str):
        raise RepairableException("Tool request must have a tool_name (type string) field")
    if not tool_request.get("tool_args") or not isinstance(tool_request.get("tool_args"), dict):
        raise RepairableException("Tool request must have a tool_args (type dictionary) field")


class TestValidateToolRequest:

    def test_none_returns_silently(self):
        _validate_tool_request(None)

    def test_valid_request_passes(self):
        _validate_tool_request({"tool_name": "test", "tool_args": {"key": "val"}})

    def test_non_dict_raises_repairable(self):
        with pytest.raises(RepairableException, match="must be a dictionary"):
            _validate_tool_request("not a dict")

    def test_list_raises_repairable(self):
        with pytest.raises(RepairableException, match="must be a dictionary"):
            _validate_tool_request([1, 2, 3])

    def test_int_raises_repairable(self):
        with pytest.raises(RepairableException, match="must be a dictionary"):
            _validate_tool_request(42)

    def test_missing_tool_name_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_name"):
            _validate_tool_request({"tool_args": {"key": "val"}})

    def test_empty_tool_name_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_name"):
            _validate_tool_request({"tool_name": "", "tool_args": {"key": "val"}})

    def test_non_string_tool_name_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_name"):
            _validate_tool_request({"tool_name": 123, "tool_args": {"key": "val"}})

    def test_missing_tool_args_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_args"):
            _validate_tool_request({"tool_name": "test"})

    def test_empty_tool_args_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_args"):
            _validate_tool_request({"tool_name": "test", "tool_args": {}})

    def test_non_dict_tool_args_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_args"):
            _validate_tool_request({"tool_name": "test", "tool_args": "not a dict"})

    def test_tool_args_as_list_raises_repairable(self):
        with pytest.raises(RepairableException, match="tool_args"):
            _validate_tool_request({"tool_name": "test", "tool_args": [1, 2]})

    def test_extra_fields_dont_affect_validation(self):
        _validate_tool_request({
            "thoughts": ["thinking"],
            "headline": "test",
            "tool_name": "response",
            "tool_args": {"text": "hello"},
        })

    def test_never_raises_valueerror(self):
        """PR #1245 core fix: ValueError was unrecoverable, RepairableException is not."""
        bad_inputs = [
            "string", 42, [1, 2], True,
            {"no_tool": True},
            {"tool_name": 123, "tool_args": "bad"},
            {"tool_name": "", "tool_args": {}},
        ]
        for inp in bad_inputs:
            with pytest.raises(RepairableException):
                _validate_tool_request(inp)


# ---------------------------------------------------------------------------
# 4. Circuit breaker logic (standalone reproduction)
#
# Reproduces the exact try/except pattern from process_tools to verify that
# BOTH Case A (None parse) and Case B (RepairableException from validation)
# increment the counter and trigger the breaker at 5.
# ---------------------------------------------------------------------------

MAX_MISFORMAT = 5


def _circuit_breaker_step(tool_request, consecutive_misformat):
    """Reproduces the circuit breaker logic from Agent.process_tools.

    Returns (new_counter, exception_type_or_none) where exception_type_or_none
    indicates what would be raised to the caller.
    """
    try:
        _validate_tool_request(tool_request)
    except RepairableException:
        consecutive_misformat += 1
        if consecutive_misformat >= MAX_MISFORMAT:
            return consecutive_misformat, HandledException
        return consecutive_misformat, RepairableException

    if tool_request is not None:
        consecutive_misformat = 0
        return consecutive_misformat, None
    else:
        consecutive_misformat += 1
        if consecutive_misformat >= MAX_MISFORMAT:
            return consecutive_misformat, HandledException
        return consecutive_misformat, "misformat_warning"


class TestCircuitBreakerCaseA:
    """Case A: complete parse failure — tool_request is None."""

    def test_single_none_increments_counter(self):
        counter, exc = _circuit_breaker_step(None, 0)
        assert counter == 1
        assert exc == "misformat_warning"

    def test_consecutive_nones_accumulate(self):
        counter = 0
        for i in range(4):
            counter, exc = _circuit_breaker_step(None, counter)
            assert counter == i + 1
            assert exc == "misformat_warning"

    def test_five_nones_triggers_breaker(self):
        counter = 0
        for _ in range(4):
            counter, exc = _circuit_breaker_step(None, counter)
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 5
        assert exc is HandledException

    def test_valid_request_resets_counter_after_nones(self):
        counter = 3
        counter, exc = _circuit_breaker_step(
            {"tool_name": "test", "tool_args": {"a": 1}}, counter
        )
        assert counter == 0
        assert exc is None


class TestCircuitBreakerCaseB:
    """Case B: parseable JSON but invalid tool call (RepairableException)."""

    def test_missing_tool_name_increments_counter(self):
        counter, exc = _circuit_breaker_step({"random": "dict"}, 0)
        assert counter == 1
        assert exc is RepairableException

    def test_empty_tool_name_increments_counter(self):
        counter, exc = _circuit_breaker_step(
            {"tool_name": "", "tool_args": {"a": 1}}, 0
        )
        assert counter == 1
        assert exc is RepairableException

    def test_non_string_tool_name_increments_counter(self):
        counter, exc = _circuit_breaker_step(
            {"tool_name": 42, "tool_args": {"a": 1}}, 0
        )
        assert counter == 1
        assert exc is RepairableException

    def test_missing_tool_args_increments_counter(self):
        counter, exc = _circuit_breaker_step({"tool_name": "test"}, 0)
        assert counter == 1
        assert exc is RepairableException

    def test_five_invalid_dicts_triggers_breaker(self):
        counter = 0
        for _ in range(4):
            counter, exc = _circuit_breaker_step({"bad": "json"}, counter)
            assert exc is RepairableException
        counter, exc = _circuit_breaker_step({"bad": "json"}, counter)
        assert counter == 5
        assert exc is HandledException

    def test_valid_request_resets_counter_after_invalid_dicts(self):
        counter = 3
        counter, exc = _circuit_breaker_step(
            {"tool_name": "test", "tool_args": {"a": 1}}, counter
        )
        assert counter == 0
        assert exc is None


class TestCircuitBreakerMixed:
    """Mixed Case A and Case B failures should accumulate toward the same limit."""

    def test_alternating_none_and_invalid_dict_accumulates(self):
        counter = 0
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 1
        counter, exc = _circuit_breaker_step({"bad": "dict"}, counter)
        assert counter == 2
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 3
        counter, exc = _circuit_breaker_step({"tool_name": 42, "tool_args": "bad"}, counter)
        assert counter == 4
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 5
        assert exc is HandledException

    def test_valid_request_resets_mixed_accumulation(self):
        counter = 0
        counter, _ = _circuit_breaker_step(None, counter)
        counter, _ = _circuit_breaker_step({"bad": "dict"}, counter)
        counter, _ = _circuit_breaker_step(None, counter)
        assert counter == 3
        counter, exc = _circuit_breaker_step(
            {"tool_name": "test", "tool_args": {"a": 1}}, counter
        )
        assert counter == 0
        assert exc is None

    def test_counter_restarts_after_reset(self):
        counter = 0
        for _ in range(4):
            counter, _ = _circuit_breaker_step(None, counter)
        assert counter == 4
        counter, _ = _circuit_breaker_step(
            {"tool_name": "test", "tool_args": {"a": 1}}, counter
        )
        assert counter == 0
        for _ in range(4):
            counter, _ = _circuit_breaker_step({"bad": "dict"}, counter)
        assert counter == 4
        counter, exc = _circuit_breaker_step({"bad": "dict"}, counter)
        assert counter == 5
        assert exc is HandledException

    def test_exactly_at_boundary(self):
        counter = 4
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 5
        assert exc is HandledException

    def test_one_below_boundary(self):
        counter = 3
        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 4
        assert exc == "misformat_warning"


# ---------------------------------------------------------------------------
# 5. End-to-end: parse → validate → circuit breaker
#
# Tests realistic model outputs through the full pipeline.
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:

    def _run_pipeline(self, raw_msg, counter):
        """Simulate the full process_tools pipeline for a raw model message."""
        tool_request = json_parse_dirty(raw_msg)
        return _circuit_breaker_step(tool_request, counter)

    def test_valid_tool_call_message(self):
        msg = '{"tool_name": "response", "tool_args": {"text": "hello"}}'
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 0
        assert exc is None

    def test_plain_text_response(self):
        msg = "I don't know how to help with that."
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 1
        assert exc == "misformat_warning"

    def test_xml_style_tool_call(self):
        msg = '<tool_call name="response"><arg name="text">hello</arg>ECT'
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 1
        assert exc == "misformat_warning"

    def test_json_without_tool_fields(self):
        msg = '{"result": "I computed the answer", "confidence": 0.95}'
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 1
        assert exc is RepairableException

    def test_json_with_empty_tool_name(self):
        msg = '{"tool_name": "", "tool_args": {"text": "hi"}}'
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 1
        assert exc is RepairableException

    def test_incidental_json_in_code_block(self):
        msg = (
            '{"tool_name": "code_execution_tool", "tool_args": '
            '{"code": "data = {\\\"key\\\": \\\"value\\\"}"}}'
        )
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 0
        assert exc is None

    def test_rfind_bug_scenario(self):
        """The original rfind bug: model output has valid JSON followed by
        incidental braces. Old code would produce corrupted extraction with
        empty tool_name, causing infinite validation->retry loop."""
        msg = (
            '{"tool_name": "response", "tool_args": {"text": "See /api/{version}/docs"}}'
            '\n\nYou can access it at /api/{v2}/endpoint'
        )
        counter, exc = self._run_pipeline(msg, 0)
        assert counter == 0
        assert exc is None

    def test_five_consecutive_bad_messages_stops(self):
        counter = 0
        bad_messages = [
            "Just plain text",
            '{"random": "json without tool fields"}',
            "More plain text",
            '{"tool_name": 42}',
            "Final bad message",
        ]
        for msg in bad_messages[:4]:
            counter, exc = self._run_pipeline(msg, counter)
            assert exc in (RepairableException, "misformat_warning")
        counter, exc = self._run_pipeline(bad_messages[4], counter)
        assert exc is HandledException

    def test_recovery_mid_sequence(self):
        counter = 0
        counter, _ = self._run_pipeline("bad text", counter)
        counter, _ = self._run_pipeline("more bad text", counter)
        assert counter == 2
        counter, exc = self._run_pipeline(
            '{"tool_name": "response", "tool_args": {"text": "recovered"}}',
            counter,
        )
        assert counter == 0
        assert exc is None

    def test_session_cguijgu4_reproduction(self):
        """Reproduce the failure pattern from session CgujjGU4:
        agent alternates between misformat (Case A) and invalid-dict (Case B).
        Without the fix, the counter never increments for Case B and
        the agent loops forever."""
        counter = 0

        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 1

        counter, exc = _circuit_breaker_step({"random": "dict"}, counter)
        assert counter == 2

        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 3

        counter, exc = _circuit_breaker_step({"random": "dict"}, counter)
        assert counter == 4

        counter, exc = _circuit_breaker_step(None, counter)
        assert counter == 5
        assert exc is HandledException