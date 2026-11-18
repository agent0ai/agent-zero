from pathlib import Path

import pytest

from helpers import messages


class PromptReader:
    """Supply the repository's real truncation prompt without starting an agent."""

    def read_prompt(self, name, **kwargs):
        assert name == "fw.msg_truncated.md"
        template = (Path(__file__).parents[1] / "prompts" / name).read_text(encoding="utf-8")
        return template.replace("{{length}}", str(kwargs["length"]))


@pytest.mark.parametrize("threshold", [1, 10, 39, 40, 41, 42, 43, 44, 50, 100, 999])
def test_truncate_text_respects_positive_budget_with_real_prompt(threshold):
    text = "abcdefghij" * 100
    agent = PromptReader()
    marker = agent.read_prompt("fw.msg_truncated.md", length=len(text) - threshold)

    result = messages.truncate_text(agent, text, threshold)

    assert len(result) == threshold
    if len(marker) >= threshold:
        assert result == marker[:threshold]
    else:
        remaining = threshold - len(marker)
        prefix = remaining // 2
        suffix = remaining - prefix
        assert result == text[:prefix] + marker + text[-suffix:]


@pytest.mark.parametrize("threshold", [0, 10, 11, 100])
def test_truncate_text_preserves_disabled_or_unnecessary_truncation(threshold):
    assert messages.truncate_text(PromptReader(), "abcdefghij", threshold) == "abcdefghij"


@pytest.mark.parametrize("data", ["x" * 100, {"body": "x" * 100}, ["x" * 100]], ids=["string", "dict", "list"])
def test_recursive_truncation_respects_small_leaf_budget(data):
    result = messages.truncate_dict_by_ratio(PromptReader(), data, 80, 10)
    if isinstance(result, dict):
        leaf = result["body"]
    elif isinstance(result, list):
        leaf = result[0]
    else:
        leaf = result
    assert len(leaf) == 10


@pytest.mark.parametrize("text", ["🙂世界好" * 100, "abcdefghij" * 100], ids=["unicode", "ascii"])
@pytest.mark.parametrize("marker", ["", "...", "截断提示" * 30], ids=["empty", "ellipsis", "long"])
@pytest.mark.parametrize("threshold", [1, 2, 3, 4, 40, 120, 121, 200])
def test_truncation_marker_boundaries_and_unicode(text, marker, threshold):
    class CustomPromptReader:
        def read_prompt(self, name, **kwargs):
            return marker

    result = messages.truncate_text(CustomPromptReader(), text, threshold)
    assert len(result) == threshold
    if len(marker) >= threshold:
        assert result == marker[:threshold]
    else:
        remaining = threshold - len(marker)
        start = remaining // 2
        end = remaining - start
        assert result == text[:start] + marker + text[-end:]
