import os
import random
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_client = None
_client_initialized = False


def get_langfuse_config() -> dict[str, Any]:
    """Get Langfuse configuration with settings UI > env var > default precedence."""
    from python.helpers.settings import get_settings

    settings = get_settings()
    public_key = settings.get("langfuse_public_key") or os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = settings.get("langfuse_secret_key") or os.getenv("LANGFUSE_SECRET_KEY", "")
    host = settings.get("langfuse_host") or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    enabled = settings.get("langfuse_enabled", False)
    sample_rate = float(settings.get("langfuse_sample_rate", 1.0))

    # Auto-enable if keys are set via env vars but toggle is off
    if not enabled and public_key and secret_key:
        enabled = True

    return {
        "enabled": enabled,
        "public_key": public_key,
        "secret_key": secret_key,
        "host": host,
        "sample_rate": sample_rate,
    }


def get_langfuse_client():
    """Get or create the Langfuse client singleton. Returns None if disabled or not configured."""
    global _client, _client_initialized

    config = get_langfuse_config()

    if not config["enabled"] or not config["public_key"] or not config["secret_key"]:
        _client = None
        _client_initialized = False
        return None

    # Return cached client if already initialized
    if _client_initialized and _client is not None:
        return _client

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=config["public_key"],
            secret_key=config["secret_key"],
            host=config["host"],
        )
        _client_initialized = True
        logger.info("Langfuse client initialized successfully")
        return _client
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse client: {e}")
        _client = None
        _client_initialized = False
        return None


def reset_client():
    """Reset the client singleton (call when settings change)."""
    global _client, _client_initialized
    if _client:
        try:
            _client.flush()
        except Exception:
            pass
    _client = None
    _client_initialized = False


def should_sample() -> bool:
    """Check if this interaction should be sampled based on sample_rate."""
    config = get_langfuse_config()
    rate = config.get("sample_rate", 1.0)
    if rate >= 1.0:
        return True
    if rate <= 0.0:
        return False
    return random.random() < rate
