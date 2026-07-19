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
