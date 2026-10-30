"""Token caps use the real tokenizer, including uneven density and Unicode."""

from typing import Literal

import pytest

from helpers import tokens


@pytest.mark.parametrize("direction", ["start", "end"])
@pytest.mark.parametrize("budget", [10, 200, 1000])
@pytest.mark.parametrize(
    "sparse", [" " * 10000, "documentation " * 1000], ids=["spaces", "prose"]
)
def test_trim_mixed_density_stays_within_budget(
    direction: Literal["start", "end"], budget: int, sparse: str
) -> None:
    dense = "😀" * 1000
    text = dense + sparse if direction == "start" else sparse + dense

    result = tokens.trim_to_tokens(text, budget, direction)

    assert tokens.count_tokens(result) <= budget
    assert result.endswith("...") if direction == "start" else result.startswith("...")
    retained = result[:-3] if direction == "start" else result[3:]
    assert retained
    assert (
        text.startswith(retained) if direction == "start" else text.endswith(retained)
    )
    assert "\ufffd" not in result


@pytest.mark.parametrize("direction", ["start", "end"])
@pytest.mark.parametrize("budget", [1, 2, 3, 9, 40])
@pytest.mark.parametrize("marker", ["", "...", "…", " [omitted] "])
def test_trim_counts_marker_and_preserves_codepoints(
    direction: Literal["start", "end"], budget: int, marker: str
) -> None:
    text = "😀中文 e\u0301 <|endoftext|> " * 40

    result = tokens.trim_to_tokens(text, budget, direction, ellipsis=marker)

    assert tokens.count_tokens(result) <= budget
    assert "\ufffd" not in result
    if result:
        assert (
            result.endswith(marker)
            if direction == "start"
            else result.startswith(marker)
        )
        retained = (
            (result[: -len(marker)] if direction == "start" else result[len(marker) :])
            if marker
            else result
        )
        assert (
            text.startswith(retained)
            if direction == "start"
            else text.endswith(retained)
        )


@pytest.mark.parametrize("direction", ["start", "end"])
@pytest.mark.parametrize("budget", [0, -1])
def test_trim_nonpositive_budget_is_empty(
    direction: Literal["start", "end"], budget: int
) -> None:
    assert tokens.trim_to_tokens("some text", budget, direction) == ""


@pytest.mark.parametrize("direction", ["start", "end"])
def test_trim_marker_that_cannot_fit_is_empty(
    direction: Literal["start", "end"],
) -> None:
    assert tokens.trim_to_tokens("word " * 100, 2, direction, "omitted " * 20) == ""


@pytest.mark.parametrize("direction", ["start", "end"])
@pytest.mark.parametrize("text", ["", "hello", "😀中文", "<|endoftext|>"])
def test_trim_preserves_text_already_within_budget(
    direction: Literal["start", "end"], text: str
) -> None:
    for budget in (tokens.count_tokens(text), tokens.count_tokens(text) + 10):
        assert tokens.trim_to_tokens(text, budget, direction) == text


@pytest.mark.parametrize("direction", ["start", "end"])
def test_trim_preserves_existing_safe_heuristic_result(
    direction: Literal["start", "end"],
) -> None:
    text = "ordinary words " * 100
    budget = 30
    chars = int(len(text) * (budget / tokens.count_tokens(text)) * tokens.TRIM_BUFFER)
    expected = text[:chars] + "..." if direction == "start" else "..." + text[-chars:]
    assert tokens.count_tokens(expected) <= budget

    assert tokens.trim_to_tokens(text, budget, direction) == expected
