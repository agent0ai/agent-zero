from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.extract_tools import normalize_tool_request
from helpers import parallel_tools


def test_normalize_tool_request_accepts_canonical_keys() -> None:
    assert normalize_tool_request({"tool_name": "response", "tool_args": {"text": "ok"}}) == (
        "response",
        {"text": "ok"},
    )


def test_normalize_tool_request_accepts_fallback_keys() -> None:
    assert normalize_tool_request({"tool": "response", "args": {"text": "ok"}}) == (
        "response",
        {"text": "ok"},
    )


def test_normalize_tool_request_uses_fallback_when_canonical_name_is_empty() -> None:
    assert normalize_tool_request(
        {"tool_name": "", "tool": "response", "args": {"text": "ok"}}
    ) == ("response", {"text": "ok"})


def test_normalize_tool_request_uses_fallback_when_canonical_args_are_invalid() -> None:
    assert normalize_tool_request(
        {"tool_name": "response", "tool_args": None, "args": {"text": "ok"}}
    ) == ("response", {"text": "ok"})


def test_normalize_tool_request_translates_method_suffix_to_action() -> None:
    assert normalize_tool_request(
        {"tool_name": "text_editor:read", "tool_args": {"path": "README.md"}}
    ) == ("text_editor", {"path": "README.md", "action": "read"})


def test_normalize_tool_request_translates_method_arg_to_action() -> None:
    assert normalize_tool_request(
        {"tool_name": "scheduler", "tool_args": {"method": "list_tasks"}}
    ) == ("scheduler", {"method": "list_tasks", "action": "list_tasks"})


def test_normalize_tool_request_preserves_explicit_action_over_method() -> None:
    assert normalize_tool_request(
        {
            "tool_name": "scheduler:delete_task",
            "tool_args": {"method": "list_tasks", "action": "show_task"},
        }
    ) == (
        "scheduler",
        {"method": "list_tasks", "action": "show_task"},
    )


def test_normalize_tool_request_rejects_missing_args() -> None:
    with pytest.raises(ValueError, match="tool_args"):
        normalize_tool_request({"tool_name": "response"})


def test_normalize_parallel_tool_calls_accepts_full_agent_reply_shape() -> None:
    calls = parallel_tools.normalize_parallel_tool_calls(
        [
            {
                "thoughts": ["This is independent and ready to run."],
                "headline": "Search Python release notes",
                "tool_name": "search_engine",
                "tool_args": {"query": "latest Python version changelog"},
            }
        ]
    )

    assert calls[0].tool_name == "search_engine"
    assert calls[0].tool_args == {"query": "latest Python version changelog"}


def test_parallel_prompt_encourages_mixed_independent_batches() -> None:
    prompt = (PROJECT_ROOT / "prompts" / "agent.system.tool.parallel.md").read_text(
        encoding="utf-8"
    )

    assert "same `tool_name` and `tool_args` shape as a top-level reply" in prompt
    assert "planning fields like `thoughts` or `headline` are ignored" in prompt
    assert "even when they use different tools" in prompt
    assert "Do not split by tool type" in prompt
    assert "Never include `document_query`" in prompt
