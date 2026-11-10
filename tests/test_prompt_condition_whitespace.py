from pathlib import Path

import pytest

from helpers import files

WHITESPACE = [" ", "  ", "\t", "\n", "\r\n", "\v", "\f", "\u00a0"]


@pytest.mark.parametrize("separator", WHITESPACE)
@pytest.mark.parametrize("outer", [False, True])
@pytest.mark.parametrize("inner", [False, True])
def test_nested_conditions_accept_the_same_whitespace_as_top_level(
    separator: str, outer: bool, inner: bool
) -> None:
    prompt = "before{{if outer}}A{{if" + separator + "inner}}B{{endif}}C{{endif}}after"
    expected = "before" + ("A" + ("B" if inner else "") + "C" if outer else "")

    assert files.evaluate_text_conditions(prompt, outer=outer, inner=inner) == (
        expected + "after"
    )


@pytest.mark.parametrize("separator", WHITESPACE)
@pytest.mark.parametrize("enabled", [False, True])
def test_top_level_whitespace_remains_supported(separator: str, enabled: bool) -> None:
    prompt = "before{{if" + separator + "enabled}}body{{endif}}after"

    assert files.evaluate_text_conditions(prompt, enabled=enabled) == (
        "before" + ("body" if enabled else "") + "after"
    )


@pytest.mark.parametrize("outer", [False, True])
@pytest.mark.parametrize("middle", [False, True])
@pytest.mark.parametrize("inner", [False, True])
def test_mixed_whitespace_tracks_all_nested_levels_and_following_blocks(
    outer: bool, middle: bool, inner: bool
) -> None:
    prompt = (
        "before{{if outer}}A{{ if\tmiddle }}B"
        "{{if\ninner}}C{{ endif }}D{{endif}}E{{endif}}"
        "{{if sibling}}F{{endif}}after"
    )
    expected = "before"
    if outer:
        expected += "A"
        if middle:
            expected += "B" + ("C" if inner else "") + "D"
        expected += "E"

    assert (
        files.evaluate_text_conditions(
            prompt, outer=outer, middle=middle, inner=inner, sibling=True
        )
        == expected + "Fafter"
    )


@pytest.mark.parametrize("outer", [False, True])
@pytest.mark.parametrize("inner", [False, True])
def test_read_prompt_file_applies_conditions_before_expanding_includes(
    tmp_path: Path, outer: bool, inner: bool
) -> None:
    (tmp_path / "main.md").write_text(
        "before{{if outer}}A{{if\tinner}}"
        '{{include "details.md"}}{{endif}}C{{endif}}after',
        encoding="utf-8",
    )
    (tmp_path / "details.md").write_text("details: {{value}}", encoding="utf-8")

    result = files.read_prompt_file(
        "main.md", [str(tmp_path)], outer=outer, inner=inner, value="expanded"
    )

    expected = "before"
    if outer:
        expected += "A" + ("details: expanded" if inner else "") + "C"
    assert result == expected + "after"


@pytest.mark.parametrize("separator", WHITESPACE)
def test_false_outer_condition_does_not_evaluate_unknown_nested_expression(
    separator: str,
) -> None:
    prompt = (
        "before{{if outer}}A{{if"
        + separator
        + "missing_name}}B{{endif}}C{{endif}}after"
    )

    assert files.evaluate_text_conditions(prompt, outer=False) == "beforeafter"


@pytest.mark.parametrize(
    "prompt",
    [
        "before{{if enabled}}unterminated",
        "before{{if enabled}}A{{if\tinner}}B{{endif}}after",
        "before{{if missing_name}}body{{endif}}after",
        "before{{if enabled +}}body{{endif}}after",
        "no conditional markers",
    ],
)
def test_unterminated_or_unevaluable_conditions_remain_unchanged(prompt: str) -> None:
    assert files.evaluate_text_conditions(prompt, enabled=True, inner=True) == prompt
