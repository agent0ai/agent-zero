"""
Tests for _cap_max_tokens_for_context: verifies that max_tokens is capped
correctly based on estimated input size, and that base64 images don't
inflate the estimate.
"""
import base64
from unittest.mock import patch, MagicMock

import pytest

# We call _cap_max_tokens_for_context directly, so import it.
# It lives at module level in models.py — use importlib to avoid
# heavy Agent Zero init.
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_cap_fn():
    """Extract _cap_max_tokens_for_context without importing the full module."""
    import ast
    source = (PROJECT_ROOT / "models.py").read_text()
    tree = ast.parse(source)
    ns = {"__builtins__": __builtins__}
    exec("import litellm", ns)
    exec("from python.helpers.tokens import approximate_tokens", ns)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_cap_max_tokens_for_context":
            code = ast.get_source_segment(source, node)
            exec(compile(code, "<extract>", "exec"), ns)
            return ns["_cap_max_tokens_for_context"]
    raise ValueError("_cap_max_tokens_for_context not found")


_cap = _get_cap_fn()

FAKE_MODEL = "anthropic/claude-sonnet-4-6"


def _fake_model_info(**overrides):
    base = {"max_input_tokens": 200_000, "max_tokens": 200_000, "max_output_tokens": 64_000}
    base.update(overrides)
    return base


def _make_text_msgs(count: int, chars_per_msg: int = 500) -> list:
    """Create a list of simple text messages."""
    text = "a " * (chars_per_msg // 2)
    msgs = []
    for i in range(count):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append({"role": role, "content": text})
    return msgs


def _make_image_msg() -> dict:
    """Create a message with a base64-encoded image (~100KB)."""
    fake_image_bytes = b"\x89PNG" + b"\x00" * 100_000
    b64 = base64.b64encode(fake_image_bytes).decode()
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": "What is in this image?"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }


class TestCapMaxTokensBasic:
    """Basic behavior: cap only when needed."""

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    @patch("litellm.token_counter", return_value=50_000)
    def test_no_cap_when_plenty_of_headroom(self, mock_counter, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(10))
        assert kwargs["max_tokens"] == 64_000

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    @patch("litellm.token_counter", return_value=180_000)
    def test_caps_when_headroom_is_tight(self, mock_counter, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(10))
        assert kwargs["max_tokens"] == 20_000  # 200k - 180k

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    @patch("litellm.token_counter", return_value=199_500)
    def test_floor_at_1024(self, mock_counter, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(10))
        assert kwargs["max_tokens"] == 1024

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    @patch("litellm.token_counter", return_value=250_000)
    def test_negative_headroom_floors_at_1024(self, mock_counter, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(10))
        assert kwargs["max_tokens"] == 1024

    def test_no_max_tokens_in_kwargs_is_noop(self):
        kwargs = {"temperature": 0.7}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(5))
        assert "max_tokens" not in kwargs


class TestCapMaxTokensWithImages:
    """Verify that base64 images don't inflate token estimate."""

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    def test_image_msg_does_not_destroy_headroom(self, mock_info):
        """With litellm.token_counter, a 100KB image should NOT count as
        hundreds of thousands of tokens like str()+tiktoken would."""
        msgs = _make_text_msgs(20) + [_make_image_msg()]
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, msgs)
        # Should NOT be capped to 1024 — litellm counts images properly
        assert kwargs["max_tokens"] > 1024, (
            f"max_tokens was capped to {kwargs['max_tokens']}, "
            f"image likely inflated token estimate"
        )

    @patch("litellm.get_model_info", return_value=_fake_model_info())
    def test_multiple_images_still_reasonable(self, mock_info):
        """Even with several images, estimate should stay reasonable."""
        msgs = _make_text_msgs(10) + [_make_image_msg() for _ in range(5)]
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, msgs)
        assert kwargs["max_tokens"] > 1024


class TestCapMaxTokensEdgeCases:
    @patch("litellm.get_model_info", side_effect=Exception("unknown model"))
    def test_exception_is_swallowed(self, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap("unknown/model", kwargs, _make_text_msgs(5))
        assert kwargs["max_tokens"] == 64_000  # unchanged

    @patch("litellm.get_model_info", return_value={"max_input_tokens": 0})
    def test_zero_ctx_window_is_noop(self, mock_info):
        kwargs = {"max_tokens": 64_000}
        _cap(FAKE_MODEL, kwargs, _make_text_msgs(5))
        assert kwargs["max_tokens"] == 64_000
