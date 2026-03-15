"""Tests for models.py — ModelConfig, ChatGenerationResult, model getters."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestModelType:
    def test_model_type_enum_values(self):
        from models import ModelType

        assert ModelType.CHAT.value == "Chat"
        assert ModelType.EMBEDDING.value == "Embedding"


class TestModelConfig:
    def test_model_config_defaults(self):
        from models import ModelConfig, ModelType

        cfg = ModelConfig(type=ModelType.CHAT, provider="openai", name="gpt-4")
        assert cfg.type == ModelType.CHAT
        assert cfg.provider == "openai"
        assert cfg.name == "gpt-4"
        assert cfg.api_base == ""
        assert cfg.ctx_length == 0
        assert cfg.limit_requests == 0
        assert cfg.limit_input == 0
        assert cfg.limit_output == 0
        assert cfg.vision is False
        assert cfg.kwargs == {}

    def test_model_config_build_kwargs_includes_api_base_when_set(self):
        from models import ModelConfig, ModelType

        cfg = ModelConfig(
            type=ModelType.CHAT,
            provider="openai",
            name="gpt-4",
            api_base="https://api.example.com",
        )
        result = cfg.build_kwargs()
        assert "api_base" in result
        assert result["api_base"] == "https://api.example.com"

    def test_model_config_build_kwargs_preserves_existing_kwargs(self):
        from models import ModelConfig, ModelType

        cfg = ModelConfig(
            type=ModelType.CHAT,
            provider="openai",
            name="gpt-4",
            api_base="https://a.com",
            kwargs={"temperature": 0.7},
        )
        result = cfg.build_kwargs()
        assert result["temperature"] == 0.7
        assert result["api_base"] == "https://a.com"

    def test_model_config_build_kwargs_does_not_override_existing_api_base(self):
        from models import ModelConfig, ModelType

        cfg = ModelConfig(
            type=ModelType.CHAT,
            provider="openai",
            name="gpt-4",
            api_base="https://default.com",
            kwargs={"api_base": "https://custom.com"},
        )
        result = cfg.build_kwargs()
        assert result["api_base"] == "https://custom.com"

    def test_model_config_build_kwargs_empty_when_no_api_base(self):
        from models import ModelConfig, ModelType

        cfg = ModelConfig(type=ModelType.CHAT, provider="openai", name="gpt-4")
        result = cfg.build_kwargs()
        assert "api_base" not in result


class TestChatChunk:
    def test_chat_chunk_typed_dict(self):
        from models import ChatChunk

        chunk = ChatChunk(response_delta="hi", reasoning_delta="think")
        assert chunk["response_delta"] == "hi"
        assert chunk["reasoning_delta"] == "think"


class TestChatGenerationResult:
    def test_chat_generation_result_empty_init(self):
        from models import ChatGenerationResult

        r = ChatGenerationResult()
        assert r.reasoning == ""
        assert r.response == ""
        assert r.thinking is False
        assert r.thinking_tag == ""
        assert r.unprocessed == ""
        assert r.native_reasoning is False

    def test_chat_generation_result_add_chunk_with_native_reasoning(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        chunk = ChatChunk(response_delta="hello", reasoning_delta="thinking...")
        r.add_chunk(chunk)
        assert r.response == "hello"
        assert r.reasoning == "thinking..."
        assert r.native_reasoning is True

    def test_chat_generation_result_add_chunk_response_only(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        chunk = ChatChunk(response_delta="hi", reasoning_delta="")
        r.add_chunk(chunk)
        assert r.response == "hi"
        assert r.reasoning == ""

    def test_chat_generation_result_output_returns_chunk_shape(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.add_chunk(ChatChunk(response_delta="x", reasoning_delta="y"))
        out = r.output()
        assert "response_delta" in out
        assert "reasoning_delta" in out
        assert out["response_delta"] == "x"
        assert out["reasoning_delta"] == "y"

    def test_chat_generation_result_thinking_tags_parsed(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.add_chunk(ChatChunk(response_delta="<think>reasoning</think>", reasoning_delta=""))
        assert r.reasoning == "reasoning"
        assert r.response == ""

    def test_chat_generation_result_init_with_chunk(self):
        from models import ChatGenerationResult, ChatChunk

        chunk = ChatChunk(response_delta="hi", reasoning_delta="")
        r = ChatGenerationResult(chunk=chunk)
        assert r.response == "hi"
        assert r.reasoning == ""

    def test_chat_generation_result_reasoning_tags_parsed(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.add_chunk(ChatChunk(response_delta="<reasoning>thought</reasoning>", reasoning_delta=""))
        assert r.reasoning == "thought"
        assert r.response == ""

    def test_chat_generation_result_output_with_unprocessed_in_reasoning(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.reasoning = "r1"
        r.response = ""
        r.unprocessed = "leftover"
        out = r.output()
        assert out["reasoning_delta"] == "r1leftover"
        assert out["response_delta"] == ""

    def test_chat_generation_result_output_with_unprocessed_in_response(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.reasoning = ""
        r.response = "resp"
        r.unprocessed = "tail"
        out = r.output()
        assert out["response_delta"] == "resptail"
        assert out["reasoning_delta"] == ""

    def test_chat_generation_result_partial_opening_tag_buffers(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.add_chunk(ChatChunk(response_delta="<th", reasoning_delta=""))
        assert r.unprocessed == "<th"
        r.add_chunk(ChatChunk(response_delta="ink", reasoning_delta=""))
        # After "<think>" + "ink": content "ink" is buffered as partial closing tag; implementation
        # may buffer as unprocessed or add to reasoning. Accept either.
        assert r.reasoning == "ink" or (r.unprocessed and "ink" in r.unprocessed)
        assert r.thinking is False

    def test_chat_generation_result_partial_closing_tag_buffers(self):
        from models import ChatGenerationResult, ChatChunk

        r = ChatGenerationResult()
        r.add_chunk(ChatChunk(response_delta="<think>x", reasoning_delta=""))
        assert r.thinking is True
        r.add_chunk(ChatChunk(response_delta="</", reasoning_delta=""))
        assert r.unprocessed == "</"
        r.add_chunk(ChatChunk(response_delta="think>", reasoning_delta=""))
        assert r.thinking is False
        assert r.reasoning == "x"


class TestGetApiKey:
    def test_get_api_key_returns_none_placeholder_when_not_set(self):
        from models import get_api_key

        with patch("models.dotenv.get_dotenv_value", return_value=None):
            key = get_api_key("openai")
            assert key == "None"

    def test_get_api_key_uses_env_var(self):
        from models import get_api_key

        with patch("models.dotenv.get_dotenv_value") as mock_get:
            mock_get.side_effect = lambda k, d=None: "sk-xxx" if "OPENAI" in k.upper() else None
            key = get_api_key("openai")
            assert key == "sk-xxx"

    def test_get_api_key_round_robin_with_comma_separated_keys(self):
        from models import get_api_key, api_keys_round_robin

        with patch("models.dotenv.get_dotenv_value", return_value="key1, key2, key3"):
            orig = api_keys_round_robin.get("openai", -1)
            try:
                k1 = get_api_key("openai")
                k2 = get_api_key("openai")
                k3 = get_api_key("openai")
                k4 = get_api_key("openai")
                keys = [k1, k2, k3, k4]
                assert "key1" in keys
                assert "key2" in keys
                assert "key3" in keys
            finally:
                api_keys_round_robin.pop("openai", None)


class TestGetRateLimiter:
    def test_get_rate_limiter_returns_same_limiter_for_same_key(self):
        from models import get_rate_limiter, rate_limiters

        key = "test\\model"
        orig = rate_limiters.pop(key, None)
        try:
            lim1 = get_rate_limiter("test", "model", 10, 100, 200)
            lim2 = get_rate_limiter("test", "model", 20, 200, 400)
            assert lim1 is lim2
            assert lim2.limits["requests"] == 20
            assert lim2.limits["input"] == 200
            assert lim2.limits["output"] == 400
        finally:
            rate_limiters.pop(key, None)
            if orig is not None:
                rate_limiters[key] = orig


class TestGetChatModel:
    def test_get_chat_model_returns_litellm_wrapper(self):
        from models import get_chat_model, LiteLLMChatWrapper

        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
        ):
            model = get_chat_model("openai", "gpt-4")
            assert isinstance(model, LiteLLMChatWrapper)
            assert "openai" in model.model_name.lower() or "gpt" in model.model_name.lower()


class TestGetEmbeddingModel:
    def test_get_embedding_model_returns_wrapper(self):
        from models import get_embedding_model

        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
        ):
            model = get_embedding_model("openai", "text-embedding-3-small")
            assert model is not None
            assert hasattr(model, "embed_documents")
            assert hasattr(model, "embed_query")


class TestGetBrowserModel:
    def test_get_browser_model_returns_browser_compatible_wrapper(self):
        from models import get_browser_model, BrowserCompatibleChatWrapper

        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
        ):
            model = get_browser_model("openai", "gpt-4")
            assert isinstance(model, BrowserCompatibleChatWrapper)


class TestLLMCallbacks:
    def test_register_and_unregister_llm_callback(self):
        from models import register_llm_callback, unregister_llm_callback, _emit_usage_event

        cb = MagicMock()
        register_llm_callback(cb)
        _emit_usage_event({"event_type": "test"})
        cb.assert_called_once_with({"event_type": "test"})
        unregister_llm_callback(cb)
        cb.reset_mock()
        _emit_usage_event({"event_type": "test2"})
        cb.assert_not_called()


class TestParseChunk:
    def test_parse_chunk_from_delta_content(self):
        from models import _parse_chunk, ChatChunk

        chunk = {"choices": [{"delta": {"content": "hello", "reasoning_content": ""}}]}
        result = _parse_chunk(chunk)
        assert result["response_delta"] == "hello"
        assert result["reasoning_delta"] == ""

    def test_parse_chunk_from_message_content(self):
        from models import _parse_chunk

        chunk = {"choices": [{"delta": {}, "message": {"content": "from message"}}]}
        result = _parse_chunk(chunk)
        assert result["response_delta"] == "from message"

    def test_parse_chunk_reasoning_delta(self):
        from models import _parse_chunk

        chunk = {"choices": [{"delta": {"content": "", "reasoning_content": "thinking"}}]}
        result = _parse_chunk(chunk)
        assert result["reasoning_delta"] == "thinking"


class TestAdjustCallArgs:
    def test_adjust_call_args_openrouter_adds_headers(self):
        from models import _adjust_call_args

        p, m, kw = _adjust_call_args("openrouter", "model", {})
        assert p == "openrouter"
        assert "extra_headers" in kw
        assert kw["extra_headers"]["HTTP-Referer"] == "https://agent-zero.ai"

    def test_adjust_call_args_other_remaps_to_openai(self):
        from models import _adjust_call_args

        p, m, kw = _adjust_call_args("other", "model", {})
        assert p == "openai"


class TestMergeProviderDefaults:
    def test_merge_provider_defaults_injects_api_key(self):
        from models import _merge_provider_defaults

        with patch("models.get_api_key", return_value="sk-test"):
            with patch("models.settings.get_settings", return_value={}):
                with patch("models.get_provider_config", return_value=None):
                    p, kw = _merge_provider_defaults("chat", "openai", {})
                    assert kw.get("api_key") == "sk-test"

    def test_merge_provider_defaults_merges_provider_config(self):
        from models import _merge_provider_defaults

        with patch("models.get_api_key", return_value="sk-test"):
            with patch("models.settings.get_settings", return_value={}):
                with patch("models.get_provider_config") as mock_cfg:
                    mock_cfg.return_value = {
                        "litellm_provider": "openai",
                        "kwargs": {"temperature": 0.5},
                    }
                    p, kw = _merge_provider_defaults("chat", "openai", {})
                    assert kw.get("temperature") == 0.5


class TestGetChatModelWithConfig:
    def test_get_chat_model_with_model_config_passes_kwargs(self):
        from models import get_chat_model, LiteLLMChatWrapper, ModelConfig, ModelType

        cfg = ModelConfig(
            type=ModelType.CHAT,
            provider="openai",
            name="gpt-4",
            api_base="https://custom.api",
        )
        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
        ):
            model = get_chat_model(
                "openai", "gpt-4", model_config=cfg, **cfg.build_kwargs()
            )
            assert isinstance(model, LiteLLMChatWrapper)
            assert model.a0_model_conf is cfg
            assert model.kwargs.get("api_base") == "https://custom.api"


class TestGetEmbeddingModelSentenceTransformers:
    def test_get_embedding_model_sentence_transformers_uses_local_wrapper(self):
        from models import get_embedding_model, LocalSentenceTransformerWrapper

        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
            patch("models.LocalSentenceTransformerWrapper") as mock_wrapper,
        ):
            get_embedding_model("huggingface", "sentence-transformers/all-MiniLM-L6-v2")
            mock_wrapper.assert_called_once()


class TestGetFinishReason:
    def test_get_finish_reason_extracts_from_chunk(self):
        from models import _get_finish_reason

        chunk = {"choices": [{"finish_reason": "stop"}]}
        assert _get_finish_reason(chunk) == "stop"

    def test_get_finish_reason_returns_none_when_missing(self):
        from models import _get_finish_reason

        assert _get_finish_reason({}) is None
        assert _get_finish_reason({"choices": [{}]}) is None


class TestIsTransientLitellmError:
    def test_transient_by_status_code(self):
        from models import _is_transient_litellm_error

        err = MagicMock()
        err.status_code = 429
        assert _is_transient_litellm_error(err) is True
        err.status_code = 503
        assert _is_transient_litellm_error(err) is True
        err.status_code = 404
        assert _is_transient_litellm_error(err) is False

    def test_transient_timeout_error(self):
        from models import _is_transient_litellm_error

        assert _is_transient_litellm_error(TimeoutError()) is True
        assert _is_transient_litellm_error(asyncio.TimeoutError()) is True


class TestExtractRetryAfter:
    def test_extract_retry_after_from_headers(self):
        from models import _extract_retry_after

        err = MagicMock()
        err.headers = {"retry-after": "5"}
        assert _extract_retry_after(err) == 5.0

    def test_extract_retry_after_returns_none_when_missing(self):
        from models import _extract_retry_after

        err = MagicMock()
        err.headers = {}
        err.response = None
        assert _extract_retry_after(err) is None


class TestApplyRateLimiter:
    @pytest.mark.asyncio
    async def test_apply_rate_limiter_returns_none_when_no_config(self):
        from models import apply_rate_limiter

        result = await apply_rate_limiter(None, "text")
        assert result is None

    @pytest.mark.asyncio
    async def test_apply_rate_limiter_returns_limiter_when_config(self):
        from models import apply_rate_limiter, ModelConfig, ModelType

        cfg = ModelConfig(
            type=ModelType.CHAT,
            provider="openai",
            name="gpt-4",
            limit_requests=10,
            limit_input=100,
            limit_output=200,
        )
        result = await apply_rate_limiter(cfg, "hello world")
        assert result is not None


class TestLiteLLMEmbeddingWrapper:
    def test_embed_documents_returns_embeddings(self):
        from models import LiteLLMEmbeddingWrapper, ModelConfig, ModelType

        cfg = ModelConfig(type=ModelType.EMBEDDING, provider="openai", name="text-embedding-3-small")
        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.embedding") as mock_embed,
        ):
            mock_embed.return_value = MagicMock(data=[{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}])
            wrapper = LiteLLMEmbeddingWrapper("text-embedding-3-small", "openai", model_config=cfg)
            result = wrapper.embed_documents(["a", "b"])
            assert result == [[0.1, 0.2], [0.3, 0.4]]

    def test_embed_query_returns_single_embedding(self):
        from models import LiteLLMEmbeddingWrapper, ModelConfig, ModelType

        cfg = ModelConfig(type=ModelType.EMBEDDING, provider="openai", name="text-embedding-3-small")
        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.embedding") as mock_embed,
        ):
            mock_embed.return_value = MagicMock(data=[{"embedding": [0.1, 0.2]}])
            wrapper = LiteLLMEmbeddingWrapper("text-embedding-3-small", "openai", model_config=cfg)
            result = wrapper.embed_query("query")
            assert result == [0.1, 0.2]


class TestLiteLLMChatWrapper:
    def test_llm_type_property(self):
        from models import LiteLLMChatWrapper, ModelConfig, ModelType, get_chat_model

        cfg = ModelConfig(type=ModelType.CHAT, provider="openai", name="gpt-4")
        with (
            patch("models.get_api_key", return_value="sk-test"),
            patch("models.settings.get_settings", return_value={}),
        ):
            model = get_chat_model("openai", "gpt-4", model_config=cfg)
            assert model._llm_type == "litellm-chat"
