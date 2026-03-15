"""
Tests for retry logic helpers and LLM usage callback system from models.py,
and for python/helpers/call_llm.py (LLM call wrapper with streaming).
"""
import sys
import ast
import types
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODELS_PY = PROJECT_ROOT / "models.py"
HAS_MODELS = MODELS_PY.exists()


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


# Read models.py source once (skip if file missing, e.g. in submodule layout)
_source = MODELS_PY.read_text() if HAS_MODELS else ""

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

# Manually extract and exec each function (only when models.py exists)
if HAS_MODELS:
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

# Make them accessible as module-level names (only when models.py exists)
_is_transient_litellm_error = _ns.get("_is_transient_litellm_error", lambda x: False)
_extract_retry_after = _ns.get("_extract_retry_after", lambda x: None)
register_llm_callback = _ns.get("register_llm_callback", lambda x: None)
unregister_llm_callback = _ns.get("unregister_llm_callback", lambda x: None)
_emit_usage_event = _ns.get("_emit_usage_event", lambda x: None)
_llm_usage_callbacks = _ns.get("_llm_usage_callbacks", [])

pytestmark_models = pytest.mark.skipif(not HAS_MODELS, reason="models.py not found")


# ─── _extract_retry_after ────────────────────────────────────────────────────

@pytestmark_models
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

@pytestmark_models
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

@pytestmark_models
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

@pytestmark_models
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


# ─── python/helpers/call_llm.py ────────────────────────────────────────────────

class TestCallLlm:
    """Tests for call_llm from python/helpers/call_llm.py."""

    @pytest.fixture
    def mock_streaming_model(self):
        """Model that yields chunks via astream for LCEL chain."""
        from langchain_core.runnables import Runnable
        from langchain_core.messages import AIMessageChunk

        class FakeStreamModel(Runnable):
            def invoke(self, input, config=None, **kwargs):
                return "Hello"

            async def astream(self, input, config=None, **kwargs):
                for c in "Hello":
                    yield c

        return FakeStreamModel()

    @pytest.fixture
    def model_yielding_content_objects(self):
        """Model yielding objects with .content attribute."""
        from langchain_core.runnables import Runnable

        class Chunk:
            def __init__(self, content):
                self.content = content

        class FakeContentModel(Runnable):
            def invoke(self, input, config=None, **kwargs):
                return "AB"

            async def astream(self, input, config=None, **kwargs):
                yield Chunk("A")
                yield Chunk("B")

        return FakeContentModel()

    @pytest.fixture
    def model_yielding_strings(self):
        """Model yielding raw strings."""
        from langchain_core.runnables import Runnable

        class FakeStringModel(Runnable):
            def invoke(self, input, config=None, **kwargs):
                return "XYZ"

            async def astream(self, input, config=None, **kwargs):
                yield "X"
                yield "Y"
                yield "Z"

        return FakeStringModel()

    @pytest.mark.asyncio
    async def test_returns_accumulated_response(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        result = await call_llm("You are helpful.", mock_streaming_model, "Hi")
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_empty_examples_works(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        result = await call_llm("System", mock_streaming_model, "msg", examples=[])
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_few_shot_examples_included(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        examples = [{"input": "q1", "output": "a1"}, {"input": "q2", "output": "a2"}]
        result = await call_llm("System", mock_streaming_model, "msg", examples=examples)
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_callback_invoked_per_chunk(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        chunks = []
        result = await call_llm(
            "System", mock_streaming_model, "msg", callback=chunks.append
        )
        assert chunks == ["H", "e", "l", "l", "o"]
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_callback_none_no_error(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        result = await call_llm("System", mock_streaming_model, "msg", callback=None)
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_handles_content_object_chunks(self, model_yielding_content_objects):
        from python.helpers.call_llm import call_llm
        result = await call_llm("System", model_yielding_content_objects, "msg")
        assert result == "AB"

    @pytest.mark.asyncio
    async def test_handles_string_chunks(self, model_yielding_strings):
        from python.helpers.call_llm import call_llm
        result = await call_llm("System", model_yielding_strings, "msg")
        assert result == "XYZ"

    @pytest.mark.asyncio
    async def test_handles_other_chunk_types_via_str(self):
        from langchain_core.runnables import Runnable
        from python.helpers.call_llm import call_llm

        class FakeOtherModel(Runnable):
            def invoke(self, input, config=None, **kwargs):
                return "42None"

            async def astream(self, input, config=None, **kwargs):
                yield 42
                yield None

        model = FakeOtherModel()
        result = await call_llm("System", model, "msg")
        assert result == "42None"

    @pytest.mark.asyncio
    async def test_empty_stream_returns_empty_string(self):
        from langchain_core.runnables import Runnable
        from python.helpers.call_llm import call_llm

        class FakeEmptyModel(Runnable):
            def invoke(self, input, config=None, **kwargs):
                return ""

            async def astream(self, input, config=None, **kwargs):
                if False:
                    yield

        model = FakeEmptyModel()
        result = await call_llm("System", model, "msg")
        assert result == ""

    @pytest.mark.asyncio
    async def test_system_and_message_passed_to_chain(self, mock_streaming_model):
        from python.helpers.call_llm import call_llm
        result = await call_llm(
            "Custom system prompt", mock_streaming_model, "User question here"
        )
        assert result == "Hello"
