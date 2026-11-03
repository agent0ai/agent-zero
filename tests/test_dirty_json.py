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


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ('{"version": 1.2.3}', {"version": "1.2.3"}),
        (
            '{"tool_name":"x","tool_args":{"date": 2024-01-01, "n": 2}}',
            {"tool_name": "x", "tool_args": {"date": "2024-01-01", "n": 2}},
        ),
        ('{"phone": +1-555-0100}', {"phone": "+1-555-0100"}),
        ('{"sign": -, "ok": true}', {"sign": "-", "ok": True}),
        ("[1.2.3, 4]", ["1.2.3", 4]),
    ],
)
def test_number_like_bare_value_is_kept_as_text(payload, expected) -> None:
    parser = DirtyJson()

    assert parser.parse(payload) == expected
    assert parser.completed is True


def test_numbers_still_parse_as_numbers() -> None:
    parsed = DirtyJson.parse_string('{"i": -12, "f": 1.5e3, "p": +7}')

    assert parsed == {"i": -12, "f": 1500.0, "p": 7}
