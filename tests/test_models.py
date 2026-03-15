"""Tests for models.py — ModelConfig, ChatGenerationResult, model getters."""

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
