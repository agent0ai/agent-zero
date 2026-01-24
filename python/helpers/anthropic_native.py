"""
Native Anthropic SDK Integration

Provides direct access to Anthropic's SDK for advanced features like:
- Prompt caching with explicit cache_control
- Batch API support
- Extended thinking with effort parameter
- Tool search and defer loading
- Programmatic Tool Calling (PTC)

This complements LiteLLM for cases where native SDK features are needed.
"""

import os
from typing import Any, Optional

try:
    from anthropic import Anthropic, AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    AsyncAnthropic = None


class AnthropicNativeClient:
    """
    Native Anthropic client wrapper for advanced features.

    Usage:
        ```python
        client = AnthropicNativeClient()
        if client.is_available():
            response = await client.create_message(
                model="claude-opus-4-5-20251101",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1024,
                cache_control=True,  # Enable prompt caching
                effort="medium",     # Control token usage
            )
        ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize native Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("API_KEY_ANTHROPIC")
        self._client = None
        self._async_client = None

        if ANTHROPIC_AVAILABLE and self.api_key:
            self._client = Anthropic(api_key=self.api_key)
            self._async_client = AsyncAnthropic(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if native Anthropic SDK is available and configured"""
        return ANTHROPIC_AVAILABLE and self._client is not None

    async def create_message(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 1.0,
        cache_control: bool = True,
        effort: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Create a message using native Anthropic SDK.

        Args:
            model: Model name (e.g., "claude-opus-4-5-20251101")
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            system: System prompt
            tools: Tool definitions for function calling
            temperature: Sampling temperature
            cache_control: Enable prompt caching
            effort: Effort level (low, medium, high) for token usage control
            **kwargs: Additional parameters

        Returns:
            Response dictionary with usage metadata including cache metrics
        """
        if not self.is_available():
            raise RuntimeError("Native Anthropic SDK not available")

        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        # Add system prompt if provided
        if system:
            params["system"] = system

        # Add tools if provided
        if tools:
            params["tools"] = tools

        # Add effort parameter if supported
        if effort and effort in ["low", "medium", "high"]:
            params["metadata"] = params.get("metadata", {})
            params["metadata"]["effort"] = effort

        # Cache control is automatically handled by Anthropic SDK
        # when messages have cache_control markers

        # Call API
        response = await self._async_client.messages.create(**params)

        # Extract response data
        result = {
            "id": response.id,
            "model": response.model,
            "role": response.role,
            "content": [
                {
                    "type": block.type,
                    "text": block.text if hasattr(block, "text") else None,
                }
                for block in response.content
            ],
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            },
        }

        return result

    async def create_batch(
        self,
        requests: list[dict],
    ) -> dict:
        """
        Create a batch job using native Anthropic Batch API.

        Args:
            requests: List of request dictionaries

        Returns:
            Batch metadata including batch_id
        """
        if not self.is_available():
            raise RuntimeError("Native Anthropic SDK not available")

        # Create batch
        batch = await self._async_client.messages.batches.create(
            requests=requests,
        )

        return {
            "id": batch.id,
            "type": batch.type,
            "processing_status": batch.processing_status,
            "request_counts": {
                "processing": batch.request_counts.processing,
                "succeeded": batch.request_counts.succeeded,
                "errored": batch.request_counts.errored,
                "canceled": batch.request_counts.canceled,
                "expired": batch.request_counts.expired,
            },
            "created_at": batch.created_at,
            "expires_at": batch.expires_at,
        }

    async def retrieve_batch(self, batch_id: str) -> dict:
        """Retrieve batch status"""
        if not self.is_available():
            raise RuntimeError("Native Anthropic SDK not available")

        batch = await self._async_client.messages.batches.retrieve(batch_id)

        return {
            "id": batch.id,
            "type": batch.type,
            "processing_status": batch.processing_status,
            "request_counts": {
                "processing": batch.request_counts.processing,
                "succeeded": batch.request_counts.succeeded,
                "errored": batch.request_counts.errored,
                "canceled": batch.request_counts.canceled,
                "expired": batch.request_counts.expired,
            },
            "ended_at": batch.ended_at,
            "results_url": batch.results_url if hasattr(batch, "results_url") else None,
        }

    async def list_batches(self, limit: int = 20) -> list[dict]:
        """List recent batches"""
        if not self.is_available():
            raise RuntimeError("Native Anthropic SDK not available")

        batches = await self._async_client.messages.batches.list(limit=limit)

        return [
            {
                "id": batch.id,
                "type": batch.type,
                "processing_status": batch.processing_status,
                "created_at": batch.created_at,
            }
            for batch in batches.data
        ]


# Global instance
_native_client: Optional[AnthropicNativeClient] = None


def get_native_client() -> AnthropicNativeClient:
    """Get or create global native Anthropic client"""
    global _native_client
    if _native_client is None:
        _native_client = AnthropicNativeClient()
    return _native_client


def is_native_sdk_enabled() -> bool:
    """Check if native SDK is enabled via environment variable"""
    return os.getenv("USE_NATIVE_ANTHROPIC_SDK", "false").lower() == "true"
