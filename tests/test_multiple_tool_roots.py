"""Regression tests for concatenated top-level tool envelopes.

A model turn carries exactly one tool envelope. Codex OAuth (Responses mode)
was observed emitting two concatenated JSON roots (`}{` boundary), which the
parser could not read as a single request. Because the payload was also not
recognised as misformatted, the Responses branch in Agent._process_chat_result
wrapped the raw tool protocol as response(text=...) and rendered it to the
user verbatim.

The contract asserted here is fail-closed: execute none, classify as
misformatted, and let the existing repair path and circuit breaker run.
"""

import json
from types import SimpleNamespace

import pytest

from helpers import extract_tools
from extensions.python._functions.agent.Agent.hist_add_warning.end import (
    _90_stop_unusable_response_loop as response_loop,
)


def _envelope(tool_name, tool_args, headline="h"):
    return json.dumps(
        {
            "thoughts": ["thinking"],
            "headline": headline,
            "tool_name": tool_name,
            "tool_args": tool_args,
        }
    )


SKILLS_ENVELOPE = _envelope(
    "skills_tool", {"action": "load", "skill_name": "a0-review-plugin"}
)
RESPONSE_ENVELOPE = _envelope("response", {"text": "done"})
CODE_ENVELOPE = _envelope("code_execution_tool", {"runtime": "terminal", "code": "ls"})


# --- single envelope still works -------------------------------------------


def test_single_valid_envelope_executes_normally():
    request = extract_tools.extract_tool_request(SKILLS_ENVELOPE)
    assert request is not None
    name, args = extract_tools.normalize_tool_request(request)
    assert name == "skills_tool"
    assert args["action"] == "load"
    assert extract_tools.has_multiple_tool_roots(SKILLS_ENVELOPE) is False
    assert extract_tools.is_misformatted_tool_request(SKILLS_ENVELOPE) is False


# --- concatenated envelopes fail closed ------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(SKILLS_ENVELOPE + RESPONSE_ENVELOPE, id="tool_then_response"),
        pytest.param(SKILLS_ENVELOPE + CODE_ENVELOPE, id="two_tool_calls"),
        pytest.param(
            SKILLS_ENVELOPE + "\n" + RESPONSE_ENVELOPE, id="separated_by_newline"
        ),
    ],
)
def test_concatenated_envelopes_execute_none_and_enter_repair(payload):
    # two roots are actually seen
    assert len(extract_tools.extract_json_root_strings(payload)) == 2
    # nothing is selected for execution
    assert extract_tools.extract_tool_request(payload) is None
    # and the turn is classified as malformed so repair runs
    assert extract_tools.has_multiple_tool_roots(payload) is True
    assert extract_tools.is_misformatted_tool_request(payload) is True


def test_concatenated_envelopes_do_not_silently_pick_the_first():
    payload = SKILLS_ENVELOPE + CODE_ENVELOPE
    request = extract_tools.extract_tool_request(payload)
    assert request is None, "first envelope must not be selected and executed"


def test_responses_mode_does_not_wrap_concatenated_protocol_as_text():
    """Guards the exact fail-open branch that caused the user-visible bug.

    agent.py wraps a message as response(text=...) only when it is neither a
    tool request nor misformatted. Concatenated envelopes must not satisfy
    that condition.
    """
    payload = SKILLS_ENVELOPE + RESPONSE_ENVELOPE
    would_wrap_as_plain_response = (
        isinstance(payload, str)
        and bool(payload.strip())
        and extract_tools.extract_tool_request(payload) is None
        and not extract_tools.is_misformatted_tool_request(payload)
    )
    assert would_wrap_as_plain_response is False


# --- no over-triggering ----------------------------------------------------


def test_literal_brace_boundary_inside_string_stays_valid():
    payload = _envelope("response", {"text": "literal }{ boundary"}, headline="a }{ b")
    assert "}{" in payload
    assert extract_tools.has_multiple_tool_roots(payload) is False
    assert extract_tools.is_misformatted_tool_request(payload) is False
    request = extract_tools.extract_tool_request(payload)
    assert request is not None
    assert extract_tools.normalize_tool_request(request)[0] == "response"


def test_nested_braces_stay_valid():
    payload = _envelope(
        "code_execution_tool",
        {"runtime": "python", "code": "d = {'a': {'b': 1}}", "nested": {"x": {"y": 2}}},
    )
    assert extract_tools.has_multiple_tool_roots(payload) is False
    assert extract_tools.extract_tool_request(payload) is not None


def test_multiple_roots_without_any_tool_request_are_not_flagged():
    payload = '{"a": 1}{"b": 2}'
    assert len(extract_tools.extract_json_root_strings(payload)) == 2
    assert extract_tools.has_multiple_tool_roots(payload) is False


# --- unchanged existing behaviour ------------------------------------------


def test_prose_with_ordinary_json_unchanged():
    payload = 'Here is the config: {"retries": 3}'
    assert extract_tools.extract_tool_request(payload) is None
    assert extract_tools.has_multiple_tool_roots(payload) is False
    assert extract_tools.is_misformatted_tool_request(payload) is False


def test_plain_prose_unchanged():
    payload = "No JSON here at all."
    assert extract_tools.extract_tool_request(payload) is None
    assert extract_tools.is_misformatted_tool_request(payload) is False


def test_fenced_tool_json_still_misformatted():
    payload = "```json\n" + SKILLS_ENVELOPE + "\n```"
    assert extract_tools.extract_tool_request(payload) is None
    assert extract_tools.is_misformatted_tool_request(payload) is True


def test_truncated_json_safe_and_unchanged():
    payload = SKILLS_ENVELOPE[:-20]
    assert extract_tools.extract_json_root_strings(payload) == []
    assert extract_tools.extract_tool_request(payload) is None
    assert extract_tools.has_multiple_tool_roots(payload) is False


def test_empty_and_non_string_inputs_safe():
    for payload in ("", None, 123, []):
        assert extract_tools.has_multiple_tool_roots(payload) is False


# --- circuit breaker counts the repaired turns -----------------------------


class FakeLog:
    def __init__(self):
        self.entries = []

    def log(self, **entry):
        self.entries.append(entry)


def _agent():
    prompts = {
        "fw.msg_misformat.md": "misformatted",
        "fw.msg_repeat.md": "repeated",
    }

    def read_prompt(name, **kwargs):
        if name == "fw.msg_unusable_response_limit.md":
            return f"stopped at {kwargs['limit']}"
        return prompts[name]

    return SimpleNamespace(
        loop_data=SimpleNamespace(iteration=0, params_persistent={}),
        context=SimpleNamespace(log=FakeLog()),
        read_prompt=read_prompt,
    )


def _run(extension, agent, message):
    data = {"args": (agent, message), "kwargs": {}, "exception": None}
    extension.execute(data=data)
    return data


def test_repeated_concatenated_turns_trip_existing_circuit_breaker(monkeypatch):
    """The concatenated payload routes to the generic misformat warning, so the
    existing breaker must count it without any new prompt being introduced."""
    payload = SKILLS_ENVELOPE + RESPONSE_ENVELOPE
    assert extract_tools.is_misformatted_tool_request(payload) is True

    monkeypatch.setattr(
        response_loop,
        "get_settings",
        lambda: {"max_consecutive_unusable_responses": 2},
    )
    agent = _agent()
    extension = response_loop.StopUnusableResponseLoop(agent=agent)

    warning = agent.read_prompt("fw.msg_misformat.md")

    assert _run(extension, agent, warning)["exception"] is None

    agent.loop_data.iteration = 1
    data = _run(extension, agent, warning)
    assert data["exception"] is not None
    assert "stopped at 2" in str(data["exception"])
