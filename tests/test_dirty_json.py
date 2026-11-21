from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.dirty_json import DirtyJson
from helpers.extract_tools import extract_tool_request, json_parse_dirty


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            '{"tool_name":"x","tool_args":{}}',
            {"tool_name": "x", "tool_args": {}},
        ),
        ("[1, 2, 3]", [1, 2, 3]),
    ],
)
def test_completed_true_when_root_is_explicitly_closed(payload, expected) -> None:
    parser = DirtyJson()

    assert parser.parse(payload) == expected
    assert parser.completed is True


def test_completed_false_when_root_hits_eof_before_closing() -> None:
    parser = DirtyJson()

    assert parser.parse('{"tool_name":"x","tool_args":{}') == {
        "tool_name": "x",
        "tool_args": {},
    }
    assert parser.completed is False


def test_completed_remains_true_after_trailing_content() -> None:
    parser = DirtyJson()

    assert parser.feed('{"tool_name":"x","tool_args":{}}') == {
        "tool_name": "x",
        "tool_args": {},
    }
    assert parser.completed is True

    assert parser.feed(" trailing noise") == {
        "tool_name": "x",
        "tool_args": {},
    }

    assert parser.completed is True


def test_value_keeps_unescaped_markdown_quotes_until_structural_delimiter() -> None:
    payload = (
        "{\n"
        '    "tool_name": "response",\n'
        '    "tool_args": {\n'
        '        "text": "The rule:\\n\\n> *"'
        'Create a child AGENTS.md when a folder becomes a boundary."'
        '*\\n\\nAdding `css/AGENTS.md` that says *"'
        'this folder contains CSS"'
        '* is duplication."\n'
        "    }\n"
        "}"
    )

    parsed = DirtyJson.parse_string(payload)

    assert parsed["tool_args"] == {
        "text": (
            "The rule:\n\n"
            '> *"Create a child AGENTS.md when a folder becomes a boundary."*\n\n'
            'Adding `css/AGENTS.md` that says *"this folder contains CSS"* is duplication.'
        )
    }


def test_value_keeps_unescaped_quotes_on_single_line() -> None:
    parsed = DirtyJson.parse_string(
        '{"text":"He said "hello" before closing","ok":true}'
    )

    assert parsed == {"text": 'He said "hello" before closing', "ok": True}


def test_value_can_still_end_before_quoted_key_when_comma_is_missing() -> None:
    parsed = DirtyJson.parse_string('{"first":"one" "second":"two"}')

    assert parsed == {"first": "one", "second": "two"}


@pytest.mark.parametrize(
    "pair",
    [
        pytest.param("\\ud83c\\udf78", id="lower"),
        pytest.param("\\uD83C\\uDF78", id="upper"),
        pytest.param("\\ud800\\udc00", id="first-supplementary"),
        pytest.param("\\udbff\\udfff", id="last-supplementary"),
    ],
)
@pytest.mark.parametrize(
    "template",
    ["{} cheers", "cheers {} cheers", "cheers {}"],
    ids=["start", "middle", "end"],
)
def test_escaped_surrogate_pair_decodes_like_json_loads(pair, template) -> None:
    payload = '{"text": "' + template.format(pair) + '"}'

    parsed = DirtyJson.parse_string(payload)

    assert parsed == json.loads(payload)
    parsed["text"].encode("utf-8")  # must not raise "surrogates not allowed"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param('{"text": "a\\ud83cb"}', "a\ufffdb", id="lone-high"),
        pytest.param('{"text": "a\\udf78b"}', "a\ufffdb", id="lone-low"),
        pytest.param(
            '{"text": "a\\ud83c\\u0041b"}', "a\ufffdAb", id="high-then-bmp-escape"
        ),
        pytest.param(
            '{"text": "a\\ud83c\\ud83c\\udf78"}',
            "a\ufffd\U0001f378",
            id="high-then-pair",
        ),
        pytest.param(
            '{"text": "\\ud83c\\udf\uff17\uff18"}',
            "\ufffd\ufffd",
            id="high-then-fullwidth-digits",
        ),
        pytest.param('{"text": "a\\ud83c', "a\ufffd", id="unterminated-high"),
    ],
)
def test_unpaired_escaped_surrogate_becomes_replacement_character(
    payload, expected
) -> None:
    # json.loads keeps lone surrogates, but they cannot be encoded as UTF-8.
    assert DirtyJson.parse_string(payload) == {"text": expected}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param('{"text": "caf\\u00e9 \\u2713"}', "caf\u00e9 \u2713", id="bmp"),
        pytest.param('{"text": "a\\uZZZZb"}', "a\\uZZZZb", id="invalid-hex"),
    ],
)
def test_bmp_and_invalid_unicode_escapes_are_unchanged(payload, expected) -> None:
    assert DirtyJson.parse_string(payload) == {"text": expected}


@pytest.mark.parametrize(
    "parse",
    [extract_tool_request, json_parse_dirty],
    ids=["extract_tool_request", "json_parse_dirty"],
)
def test_tool_envelope_with_escaped_emoji_parses_like_json_loads(parse) -> None:
    envelope = json.dumps(
        {
            "thoughts": ["Print a cocktail emoji."],
            "headline": "Printing an emoji",
            "tool_name": "code_execution_tool",
            "tool_args": {
                "runtime": "python",
                "session": 0,
                "reset": False,
                "code": "print('\U0001f378')",
            },
        }
    )
    # json.dumps escapes the emoji as a UTF-16 surrogate pair.
    assert "\\ud83c\\udf78" in envelope

    parsed = parse(envelope)

    assert parsed == json.loads(envelope)
    parsed["tool_args"]["code"].encode("utf-8")  # must not raise
