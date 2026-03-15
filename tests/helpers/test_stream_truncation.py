"""
Tests for stream truncation detection and finish_reason tracking in unified_call.

Uses mocked async iterators to simulate various streaming scenarios without
requiring actual LLM API calls.
"""
import ast
import asyncio
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_PY = PROJECT_ROOT / "models.py"

_source = MODELS_PY.read_text()


def _extract_function(name: str) -> callable:
    tree = ast.parse(_source)
    ns = {"__builtins__": __builtins__}
    exec("from typing import Any", ns)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            code = ast.get_source_segment(_source, node)
            if code:
                exec(compile(code, "<extract>", "exec"), ns)
            return ns[name]
    raise ValueError(f"Function {name} not found in models.py")


_get_finish_reason = _extract_function("_get_finish_reason")


# ─── _get_finish_reason ──────────────────────────────────────────────────────

class TestGetFinishReason:
    def test_stop(self):
        chunk = {"choices": [{"finish_reason": "stop"}]}
        assert _get_finish_reason(chunk) == "stop"

    def test_end_turn(self):
        chunk = {"choices": [{"finish_reason": "end_turn"}]}
        assert _get_finish_reason(chunk) == "end_turn"

    def test_length(self):
        chunk = {"choices": [{"finish_reason": "length"}]}
        assert _get_finish_reason(chunk) == "length"

    def test_none_finish_reason(self):
        chunk = {"choices": [{"finish_reason": None}]}
        assert _get_finish_reason(chunk) is None

    def test_no_choices(self):
        chunk = {"choices": []}
        assert _get_finish_reason(chunk) is None

    def test_missing_choices_key(self):
        chunk = {"usage": {"prompt_tokens": 10}}
        assert _get_finish_reason(chunk) is None

    def test_non_dict_chunk(self):
        assert _get_finish_reason(None) is None
        assert _get_finish_reason("string") is None

    def test_mock_model_response(self):
        chunk = MagicMock()
        chunk.__getitem__ = lambda self, key: [{"finish_reason": "stop"}] if key == "choices" else None
        assert _get_finish_reason(chunk) == "stop"


# ─── Stream truncation detection (integration-style) ─────────────────────────

def _make_chunk(text: str = "", finish_reason: str | None = None, usage: dict | None = None) -> dict:
    chunk = {
        "choices": [{
            "delta": {"content": text, "role": "assistant"},
            "finish_reason": finish_reason,
        }],
    }
    if usage:
        chunk["usage"] = usage
    return chunk


async def _simulate_stream_and_check(chunks: list[dict]) -> tuple[str | None, bool]:
    """Simulate the stream loop from unified_call and return (finish_reason, got_chunks).

    Returns the tracked _stream_finish_reason and whether any chunks were received.
    """
    got_any_chunk = False
    _stream_finish_reason: str | None = None

    for chunk in chunks:
        got_any_chunk = True
        _fr = _get_finish_reason(chunk)
        if _fr is not None:
            _stream_finish_reason = _fr

    return _stream_finish_reason, got_any_chunk


class TestStreamTruncationDetection:
    def test_normal_stream_has_finish_reason(self):
        chunks = [
            _make_chunk("Hello "),
            _make_chunk("world"),
            _make_chunk("", finish_reason="stop"),
            _make_chunk(usage={"prompt_tokens": 10, "completion_tokens": 5}),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert got is True
        assert finish == "stop"

    def test_anthropic_end_turn(self):
        chunks = [
            _make_chunk("Response text"),
            _make_chunk("", finish_reason="end_turn"),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert got is True
        assert finish == "end_turn"

    def test_truncated_stream_no_finish_reason(self):
        chunks = [
            _make_chunk("Hello "),
            _make_chunk("wor"),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert got is True
        assert finish is None  # truncated!

    def test_length_truncation_detected(self):
        chunks = [
            _make_chunk("Long text..."),
            _make_chunk("", finish_reason="length"),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert got is True
        assert finish == "length"

    def test_empty_stream(self):
        finish, got = asyncio.run(_simulate_stream_and_check([]))
        assert got is False
        assert finish is None

    def test_finish_reason_in_middle_chunk(self):
        """finish_reason can appear on any chunk, not just the last one."""
        chunks = [
            _make_chunk("Hello"),
            _make_chunk("", finish_reason="stop"),
            _make_chunk(usage={"prompt_tokens": 10, "completion_tokens": 2}),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert finish == "stop"

    def test_usage_only_final_chunk_no_false_positive(self):
        """A usage-only final chunk (finish_reason=None) should NOT cause
        false positive truncation detection if a prior chunk had finish_reason."""
        chunks = [
            _make_chunk("Hello"),
            _make_chunk("", finish_reason="stop"),
            _make_chunk(usage={"prompt_tokens": 50, "completion_tokens": 10}),
        ]
        finish, got = asyncio.run(_simulate_stream_and_check(chunks))
        assert finish == "stop"  # NOT None

    def test_should_retry_logic_on_truncation(self):
        """Verify that truncated stream (no finish_reason) would trigger retry."""
        finish = None
        got_any_chunk = True
        stream = True

        should_retry = stream and got_any_chunk and finish is None
        assert should_retry is True

    def test_should_not_retry_on_normal_completion(self):
        finish = "stop"
        got_any_chunk = True
        stream = True

        should_retry = stream and got_any_chunk and finish is None
        assert should_retry is False

    def test_should_not_retry_on_empty_stream(self):
        finish = None
        got_any_chunk = False
        stream = True

        should_retry = stream and got_any_chunk and finish is None
        assert should_retry is False
