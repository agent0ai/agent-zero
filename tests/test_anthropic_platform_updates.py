"""
Tests for Anthropic Platform Updates Integration

Tests the new features added in Phase 1-6:
- Prompt caching
- Claude Opus 4.5 / Sonnet 4.5 integration
- Tool caching
- Batch API infrastructure
- Native SDK integration
- Cache metrics tracking
"""

import pytest

from models import LiteLLMChatWrapper, ModelConfig, ModelType
from python.helpers.anthropic_native import get_native_client
from python.helpers.batch_processor import BatchProcessor, BatchRequest, BatchStatus
from python.helpers.cache_metrics import CacheMetricsTracker, get_cache_tracker
from python.helpers.llm_router import LLMRouter


class TestPromptCaching:
    """Test prompt caching functionality"""

    def test_cache_control_added_to_system_message(self):
        """Verify system message gets cache_control marker"""
        config = ModelConfig(type=ModelType.CHAT, provider="anthropic", name="claude-opus-4-5-20251101")
        wrapper = LiteLLMChatWrapper(model="claude-opus-4-5-20251101", provider="anthropic", model_config=config)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]

        cached_messages, _ = wrapper._add_cache_control(messages, True, None)

        assert "cache_control" in cached_messages[0]
        assert cached_messages[0]["cache_control"]["type"] == "ephemeral"

    def test_cache_control_added_to_last_user_message(self):
        """Verify last user message gets cache_control marker"""
        config = ModelConfig(type=ModelType.CHAT, provider="anthropic", name="claude-opus-4-5-20251101")
        wrapper = LiteLLMChatWrapper(model="claude-opus-4-5-20251101", provider="anthropic", model_config=config)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]

        cached_messages, _ = wrapper._add_cache_control(messages, True, None)

        # Last user message should have cache control
        assert "cache_control" in cached_messages[3]
        assert cached_messages[3]["cache_control"]["type"] == "ephemeral"

    def test_cache_control_added_to_tools(self):
        """Verify tools get cache_control marker"""
        config = ModelConfig(type=ModelType.CHAT, provider="anthropic", name="claude-opus-4-5-20251101")
        wrapper = LiteLLMChatWrapper(model="claude-opus-4-5-20251101", provider="anthropic", model_config=config)

        messages = [{"role": "user", "content": "Hello!"}]
        tools = [{"name": "tool1", "description": "First tool"}, {"name": "tool2", "description": "Second tool"}]

        _, cached_tools = wrapper._add_cache_control(messages, True, tools)

        # Last tool should have cache control
        assert "cache_control" in cached_tools[1]
        assert cached_tools[1]["cache_control"]["type"] == "ephemeral"

    def test_cache_control_disabled_for_non_anthropic(self):
        """Verify cache control not added for non-Anthropic providers"""
        config = ModelConfig(type=ModelType.CHAT, provider="openai", name="gpt-4o")
        wrapper = LiteLLMChatWrapper(model="gpt-4o", provider="openai", model_config=config)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]

        cached_messages, _ = wrapper._add_cache_control(messages, True, None)

        # Should not have cache control for non-Anthropic
        assert "cache_control" not in cached_messages[0]
        assert "cache_control" not in cached_messages[1]


class TestCacheMetrics:
    """Test cache metrics tracking"""

    def test_track_usage_with_cache_hit(self):
        """Test tracking usage with cache hit"""
        tracker = CacheMetricsTracker()

        metrics = tracker.track_usage(
            model="claude-opus-4-5-20251101",
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
            cache_read_input_tokens=800,  # Cache hit
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        )

        assert metrics.cache_hit is True
        assert metrics.cache_read_input_tokens == 800
        assert metrics.cost_savings > 0

    def test_track_usage_with_cache_creation(self):
        """Test tracking usage with cache creation"""
        tracker = CacheMetricsTracker()

        metrics = tracker.track_usage(
            model="claude-opus-4-5-20251101",
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
            cache_creation_input_tokens=500,  # Writing to cache
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        )

        assert metrics.cache_hit is False
        assert metrics.cache_creation_input_tokens == 500

    def test_get_cache_stats(self):
        """Test retrieving cache statistics"""
        tracker = CacheMetricsTracker()

        # Track some usage
        tracker.track_usage(
            model="claude-opus-4-5-20251101",
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
            cache_read_input_tokens=800,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        )

        stats = tracker.get_cache_stats(hours=24)

        assert stats["total_calls"] > 0
        assert stats["cache_hits"] > 0
        assert stats["cache_hit_rate"] > 0


class TestBatchProcessor:
    """Test batch API infrastructure"""

    @pytest.mark.asyncio
    async def test_create_batch(self):
        """Test creating a batch job"""
        processor = BatchProcessor()

        requests = [
            BatchRequest(
                custom_id=f"test_{i}",
                model="claude-opus-4-5-20251101",
                messages=[{"role": "user", "content": f"Test {i}"}],
            )
            for i in range(5)
        ]

        batch_id = await processor.create_batch(requests)

        assert batch_id is not None
        assert batch_id.startswith("batch_")

    @pytest.mark.asyncio
    async def test_get_batch(self):
        """Test retrieving a batch job"""
        processor = BatchProcessor()

        requests = [
            BatchRequest(
                custom_id="test_1", model="claude-opus-4-5-20251101", messages=[{"role": "user", "content": "Test"}]
            )
        ]

        batch_id = await processor.create_batch(requests)
        batch = processor.db.get_batch(batch_id)

        assert batch is not None
        assert batch.batch_id == batch_id
        assert batch.status == BatchStatus.PENDING
        assert batch.request_count == 1

    @pytest.mark.asyncio
    async def test_batch_validation(self):
        """Test batch validation"""
        processor = BatchProcessor()

        # Empty batch should fail
        with pytest.raises(ValueError):
            await processor.create_batch([])

        # Too many requests should fail
        large_batch = [
            BatchRequest(
                custom_id=f"test_{i}", model="claude-opus-4-5-20251101", messages=[{"role": "user", "content": "Test"}]
            )
            for i in range(10001)
        ]

        with pytest.raises(ValueError):
            await processor.create_batch(large_batch)


class TestLLMRouter:
    """Test LLM router with new models"""

    def test_opus_4_5_in_catalog(self):
        """Test that Opus 4.5 is in the model catalog"""
        router = LLMRouter()

        assert "anthropic/claude-opus-4-5-20251101" in router.MODEL_CATALOG
        opus_config = router.MODEL_CATALOG["anthropic/claude-opus-4-5-20251101"]

        assert opus_config["display_name"] == "Claude Opus 4.5"
        assert opus_config["context_length"] == 200000
        assert opus_config["max_output_tokens"] == 64000
        assert opus_config["supports_caching"] is True
        assert opus_config["supports_ptc"] is True
        assert opus_config["supports_batch"] is True
        assert "effort_levels" in opus_config

    def test_sonnet_4_5_in_catalog(self):
        """Test that Sonnet 4.5 is in the model catalog"""
        router = LLMRouter()

        assert "anthropic/claude-sonnet-4-5-20250929" in router.MODEL_CATALOG
        sonnet_config = router.MODEL_CATALOG["anthropic/claude-sonnet-4-5-20250929"]

        assert sonnet_config["display_name"] == "Claude Sonnet 4.5"
        assert sonnet_config["context_length"] == 200000
        assert sonnet_config["supports_caching"] is True
        assert sonnet_config["supports_ptc"] is True

    def test_cache_configuration(self):
        """Test cache configuration in models"""
        router = LLMRouter()

        for key, config in router.MODEL_CATALOG.items():
            if key.startswith("anthropic/"):
                assert "supports_caching" in config
                if config.get("supports_caching"):
                    assert "cache_ttl_seconds" in config


class TestNativeSDK:
    """Test native Anthropic SDK integration"""

    def test_native_client_initialization(self):
        """Test native client can be initialized"""
        client = get_native_client()
        assert client is not None

    def test_native_client_availability(self):
        """Test native client availability check"""
        client = get_native_client()
        # Will be False without API key in test environment
        available = client.is_available()
        assert isinstance(available, bool)


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_global_cache_tracker(self):
        """Test global cache tracker instance"""
        tracker1 = get_cache_tracker()
        tracker2 = get_cache_tracker()

        assert tracker1 is tracker2  # Should be same instance

    @pytest.mark.asyncio
    async def test_end_to_end_cache_tracking(self):
        """Test end-to-end cache tracking workflow"""
        # Get tracker
        tracker = get_cache_tracker()

        # Track usage
        metrics = tracker.track_usage(
            model="claude-opus-4-5-20251101",
            provider="anthropic",
            input_tokens=5000,
            output_tokens=2000,
            cache_creation_input_tokens=2000,
            cache_read_input_tokens=3000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        )

        # Verify metrics
        assert metrics.cache_hit is True
        assert metrics.cost_savings > 0

        # Get stats
        stats = tracker.get_cache_stats(hours=1)
        assert stats["total_calls"] > 0
