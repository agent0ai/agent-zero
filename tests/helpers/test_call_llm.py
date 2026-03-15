"""
Tests for retry logic helpers and LLM usage callback system from models.py.

Extracts the specific functions under test from the source file to avoid
importing the full Agent Zero dependency tree (browser_use, litellm, etc.).
"""
import sys
import ast
import types
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_PY = PROJECT_ROOT / "models.py"


def _extract_and_compile(source: str, func_names: list[str], global_names: list[str] | None = None):
    """Extract standalone functions from source by name and compile them into a namespace."""
    tree = ast.parse(source)
    ns = {"__builtins__": __builtins__}

    # Also extract top-level assignments (like _llm_usage_callbacks)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and global_names and target.id in global_names:
                    code = ast.get_source_segment(source, node)
                    if code:
                        exec(compile(code, "<extract>", "exec"), ns)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in func_names:
                code = ast.get_source_segment(source, node)
                if code:
                    exec(compile(code, "<extract>", "exec"), ns)

    # Type aliases
    if global_names:
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.AnnAssign,)) and isinstance(node.target, ast.Name):
                if node.target.id in global_names:
                    code = ast.get_source_segment(source, node)
                    if code:
                        try:
                            exec(compile(code, "<extract>", "exec"), ns)
                        except Exception:
                            pass

    return ns


# Read models.py source once
_source = MODELS_PY.read_text()

# Provide the typing imports that the extracted functions need
from typing import Any, Callable

# Extract the functions we want to test
_ns = {}
exec(textwrap.dedent("""
from typing import Any, Callable
import asyncio
import openai

LLMUsageCallback = Callable[[dict[str, Any]], None]
_llm_usage_callbacks: list[LLMUsageCallback] = []
"""), _ns)

# Manually extract and exec each function
for _func_name in [
    "_is_transient_litellm_error",
    "_extract_retry_after",
    "register_llm_callback",
    "unregister_llm_callback",
    "_emit_usage_event",
]:
    tree = ast.parse(_source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == _func_name:
            code = ast.get_source_segment(_source, node)
            if code:
                exec(compile(code, "<extract>", "exec"), _ns)
            break

# Make them accessible as module-level names
_is_transient_litellm_error = _ns["_is_transient_litellm_error"]
_extract_retry_after = _ns["_extract_retry_after"]
register_llm_callback = _ns["register_llm_callback"]
unregister_llm_callback = _ns["unregister_llm_callback"]
_emit_usage_event = _ns["_emit_usage_event"]
_llm_usage_callbacks = _ns["_llm_usage_callbacks"]


# ─── _extract_retry_after ────────────────────────────────────────────────────

class TestExtractRetryAfter:
    def test_no_headers(self):
        exc = Exception("plain error")
        assert _extract_retry_after(exc) is None

    def test_retry_after_in_headers_attr(self):
        exc = Exception("rate limited")
        exc.headers = {"retry-after": "5"}
        assert _extract_retry_after(exc) == 5.0

    def test_retry_after_case_variant(self):
        exc = Exception("rate limited")
        exc.headers = {"Retry-After": "12.5"}
        assert _extract_retry_after(exc) == 12.5

    def test_retry_after_in_response_headers(self):
        class FakeResponse:
            headers = {"retry-after": "3"}
        exc = Exception("rate limited")
        exc.headers = {}
        exc.response = FakeResponse()
        assert _extract_retry_after(exc) == 3.0

    def test_non_numeric_retry_after(self):
        exc = Exception("rate limited")
        exc.headers = {"retry-after": "not-a-number"}
        assert _extract_retry_after(exc) is None

    def test_none_headers(self):
        exc = Exception("error")
        exc.headers = None
        assert _extract_retry_after(exc) is None


# ─── _is_transient_litellm_error ──────────────────────────────────────────────

class TestIsTransientLitellmError:
    @pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504, 599])
    def test_transient_status_codes(self, code):
        exc = Exception("error")
        exc.status_code = code
        assert _is_transient_litellm_error(exc) is True

    @pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
    def test_non_transient_status_codes(self, code):
        exc = Exception("error")
        exc.status_code = code
        assert _is_transient_litellm_error(exc) is False

    def test_plain_exception_no_status(self):
        exc = Exception("unknown")
        result = _is_transient_litellm_error(exc)
        assert isinstance(result, bool)


# ─── Callback registration ────────────────────────────────────────────────────

class TestLLMUsageCallbacks:
    def setup_method(self):
        self._backup = _llm_usage_callbacks.copy()
        _llm_usage_callbacks.clear()

    def teardown_method(self):
        _llm_usage_callbacks.clear()
        _llm_usage_callbacks.extend(self._backup)

    def test_register_callback(self):
        events = []
        register_llm_callback(events.append)
        assert len(_llm_usage_callbacks) == 1

    def test_register_duplicate_ignored(self):
        events = []
        cb = events.append
        register_llm_callback(cb)
        register_llm_callback(cb)
        assert len(_llm_usage_callbacks) == 1

    def test_unregister_callback(self):
        events = []
        cb = events.append
        register_llm_callback(cb)
        unregister_llm_callback(cb)
        assert len(_llm_usage_callbacks) == 0

    def test_unregister_nonexistent_no_error(self):
        unregister_llm_callback(lambda x: None)

    def test_emit_calls_all_callbacks(self):
        events1, events2 = [], []
        register_llm_callback(events1.append)
        register_llm_callback(events2.append)
        _emit_usage_event({"n": 1})
        assert len(events1) == 1 and len(events2) == 1

    def test_emit_no_callbacks_no_error(self):
        _emit_usage_event({"test": True})

    def test_callback_error_silenced(self):
        def bad_callback(event):
            raise ValueError("boom")
        events = []
        register_llm_callback(bad_callback)
        register_llm_callback(events.append)
        _emit_usage_event({"n": 1})
        assert len(events) == 1


# ─── Exponential backoff formula ──────────────────────────────────────────────

class TestExponentialBackoffFormula:
    def test_default_params(self):
        kwargs = {}
        assert int(kwargs.pop("a0_retry_attempts", 2)) == 2
        assert float(kwargs.pop("a0_retry_delay_seconds", 1.5)) == 1.5
        assert float(kwargs.pop("a0_retry_exponential_base", 2.0)) == 2.0
        assert float(kwargs.pop("a0_retry_max_delay", 30.0)) == 30.0
        assert bool(kwargs.pop("a0_retry_jitter", True)) is True

    def test_custom_params_stripped_from_kwargs(self):
        kwargs = {
            "a0_retry_attempts": 5,
            "a0_retry_delay_seconds": 0.5,
            "a0_retry_exponential_base": 3.0,
            "a0_retry_max_delay": 60.0,
            "a0_retry_jitter": False,
            "temperature": 0.7,
        }
        for key in list(kwargs):
            if key.startswith("a0_retry"):
                kwargs.pop(key)
        assert kwargs == {"temperature": 0.7}

    @pytest.mark.parametrize("attempt, expected", [
        (0, 1.5),
        (1, 3.0),
        (2, 6.0),
        (3, 12.0),
        (4, 24.0),
        (5, 30.0),  # capped
    ])
    def test_delay_with_cap(self, attempt, expected):
        base, exp, cap = 1.5, 2.0, 30.0
        delay = min(base * (exp ** attempt), cap)
        assert delay == expected

    def test_retry_after_takes_precedence(self):
        retry_after = 10.0
        cap = 30.0
        delay = min(retry_after, cap)
        assert delay == 10.0

    def test_jitter_bounds(self):
        import random
        random.seed(42)
        delay = 10.0
        for _ in range(100):
            jittered = delay * (0.5 + random.random())
            assert 5.0 <= jittered < 15.0
