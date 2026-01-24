"""
Prompt Caching Configuration Module for Agent Zero

This module provides feature flags and configuration for Anthropic prompt caching.
Caching is ENABLED by default for cost optimization.

Environment Variables:
    A0_ENABLE_PROMPT_CACHING: Set to 'false' to disable prompt caching (default: true)
    A0_CACHE_SCOPE: Caching scope level (default: standard)
        - minimal: Only cache tool documentation (safest)
        - standard: Cache tool docs + system prompt base
        - aggressive: Cache all static content including examples

Minimum Token Requirements (from Anthropic docs):
    - Claude Opus 4.5: 4,096 tokens
    - Claude Opus 4.1, 4, Sonnet 4.5, 4, 3.7: 1,024 tokens
    - Claude Haiku 4.5: 4,096 tokens
    - Claude Haiku 3.5, 3: 2,048 tokens

Usage:
    from python.helpers.caching_config import CACHING_CONFIG, get_min_tokens_for_model
    
    if CACHING_CONFIG.enabled:
        min_tokens = get_min_tokens_for_model(model_name)
        # Apply cache_control to content if content >= min_tokens
"""

import os
import re
from dataclasses import dataclass
from typing import Literal


# Model-specific minimum token requirements for caching
# Source: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
MODEL_MIN_TOKENS = {
    # Claude Opus models
    'opus-4.5': 4096,
    'opus-4-5': 4096,
    'opus-4.1': 1024,
    'opus-4-1': 1024,
    'opus-4': 1024,
    'opus-3': 1024,  # deprecated
    
    # Claude Sonnet models
    'sonnet-4.5': 1024,
    'sonnet-4-5': 1024,
    'sonnet-4': 1024,
    'sonnet-3.7': 1024,  # deprecated
    'sonnet-3-7': 1024,
    
    # Claude Haiku models - IMPORTANT: Haiku 4.5 requires 4096!
    'haiku-4.5': 4096,
    'haiku-4-5': 4096,
    'haiku-3.5': 2048,  # deprecated
    'haiku-3-5': 2048,
    'haiku-3': 2048,
}

# Default minimum tokens (conservative fallback)
DEFAULT_MIN_TOKENS = 4096


def get_min_tokens_for_model(model_name: str) -> int:
    """
    Get the minimum token requirement for caching based on model name.
    
    Args:
        model_name: The model name (e.g., 'claude-haiku-4-5-20251001', 'anthropic/claude-3-haiku')
    
    Returns:
        Minimum tokens required for caching (4096, 2048, or 1024 depending on model)
    """
    if not model_name:
        return DEFAULT_MIN_TOKENS
    
    model_lower = model_name.lower()
    
    # Check for specific model patterns
    for pattern, min_tokens in MODEL_MIN_TOKENS.items():
        if pattern in model_lower:
            return min_tokens
    
    # Fallback patterns for generic model names
    if 'haiku' in model_lower:
        # Check for version numbers
        if '4.5' in model_lower or '4-5' in model_lower or '45' in model_lower:
            return 4096  # Haiku 4.5
        elif '3.5' in model_lower or '3-5' in model_lower or '35' in model_lower:
            return 2048  # Haiku 3.5
        elif '3' in model_lower:
            return 2048  # Haiku 3
        else:
            return 4096  # Default to highest for unknown Haiku versions
    
    if 'opus' in model_lower:
        if '4.5' in model_lower or '4-5' in model_lower or '45' in model_lower:
            return 4096  # Opus 4.5
        else:
            return 1024  # Other Opus versions
    
    if 'sonnet' in model_lower:
        return 1024  # All Sonnet versions use 1024
    
    # Default to conservative value for unknown models
    return DEFAULT_MIN_TOKENS


@dataclass
class CachingConfig:
    """Configuration for prompt caching features."""
    
    enabled: bool
    scope: Literal['minimal', 'standard', 'aggressive']
    
    @classmethod
    def from_env(cls) -> 'CachingConfig':
        """Load configuration from environment variables."""
        enabled = os.getenv('A0_ENABLE_PROMPT_CACHING', 'true').lower() == 'true'
        scope = os.getenv('A0_CACHE_SCOPE', 'standard')
        
        # Validate scope
        valid_scopes = ('minimal', 'standard', 'aggressive')
        if scope not in valid_scopes:
            scope = 'standard'
        
        return cls(
            enabled=enabled,
            scope=scope  # type: ignore
        )
    
    def should_cache_tools(self) -> bool:
        """Whether to cache tool documentation."""
        return self.enabled and self.scope in ('minimal', 'standard', 'aggressive')
    
    def should_cache_system_prompt(self) -> bool:
        """Whether to cache the base system prompt."""
        return self.enabled and self.scope in ('standard', 'aggressive')
    
    def should_cache_examples(self) -> bool:
        """Whether to cache example content."""
        return self.enabled and self.scope == 'aggressive'


# Global configuration instance - loaded once at import time
CACHING_CONFIG = CachingConfig.from_env()


def get_caching_status(model_name: str = None) -> dict:
    """Get current caching configuration status for debugging."""
    status = {
        'enabled': CACHING_CONFIG.enabled,
        'scope': CACHING_CONFIG.scope,
        'cache_tools': CACHING_CONFIG.should_cache_tools(),
        'cache_system_prompt': CACHING_CONFIG.should_cache_system_prompt(),
        'cache_examples': CACHING_CONFIG.should_cache_examples(),
        'default_min_tokens': DEFAULT_MIN_TOKENS,
        'env_vars': {
            'A0_ENABLE_PROMPT_CACHING': os.getenv('A0_ENABLE_PROMPT_CACHING', 'not set'),
            'A0_CACHE_SCOPE': os.getenv('A0_CACHE_SCOPE', 'not set')
        }
    }
    
    if model_name:
        status['model_name'] = model_name
        status['min_tokens_for_model'] = get_min_tokens_for_model(model_name)
    
    return status


if __name__ == '__main__':
    import json
    print("Caching Configuration Status:")
    print(json.dumps(get_caching_status(), indent=2))
    
    print("\nModel-specific minimum tokens:")
    test_models = [
        'claude-haiku-4-5-20251001',
        'anthropic/claude-3-haiku-20240307',
        'claude-3-5-haiku-20241022',
        'claude-sonnet-4-5',
        'claude-opus-4-5',
        'anthropic/claude-3-opus',
    ]
    for model in test_models:
        print(f"  {model}: {get_min_tokens_for_model(model)} tokens")
