from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.dirty_json import DirtyJson


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


def test_unicode_escape_surrogate_pair_is_combined() -> None:
    # \\ud83c\\udf78 is the JSON escape form of U+1F378; json.loads combines
    # the pair and DirtyJson must match, otherwise the parsed string carries two
    # lone UTF-16 surrogates and crashes at the first .encode("utf-8") downstream
    # (tool execution, log writes).
    payload = '{"text": "START\\ud83c\\udf78END"}'

    parsed = DirtyJson.parse_string(payload)

    assert parsed == {"text": "START\U0001f378END"}
    parsed["text"].encode("utf-8")  # must not raise


def test_unicode_escape_lone_surrogate_becomes_replacement_char() -> None:
    high = DirtyJson.parse_string('{"text": "x\\ud83cy"}')
    low = DirtyJson.parse_string('{"text": "x\\udf78y"}')

    assert high == {"text": "x\ufffdy"}
    assert low == {"text": "x\ufffdy"}
    high["text"].encode("utf-8")  # must not raise
    low["text"].encode("utf-8")  # must not raise


def test_unicode_escape_bmp_characters_unchanged() -> None:
    parsed = DirtyJson.parse_string('{"text": "caf\\u00e9 \\u2713"}')

    assert parsed == {"text": "caf\u00e9 \u2713"}


def test_unicode_escape_high_surrogate_followed_by_non_escape_text() -> None:
    parsed = DirtyJson.parse_string('{"text": "a\\ud83cbcd"}')

    assert parsed == {"text": "a\ufffdbcd"}
