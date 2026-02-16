"""Honcho Integration Helper for Agent Zero.

Provides client management, message synchronization, and context
retrieval for the Honcho conversational memory platform.

See: https://docs.honcho.dev
SDK: https://github.com/plastic-labs/honcho-python
"""

import logging
import time
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import AgentContext

logger = logging.getLogger("honcho")

# --- SDK availability check ---
try:
    from honcho import Honcho
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False
    logger.debug("Honcho SDK not installed. Run: pip install honcho-ai")

# --- Defaults ---
DEFAULT_WORKSPACE_ID = "agent-zero"
DEFAULT_USER_ID = "user"
DEFAULT_AGENT_PEER = "agent-zero"
CONTEXT_CACHE_TTL = 120  # seconds

# --- Caches ---
_client_cache: Dict[str, Any] = {}
_context_cache: Dict[str, tuple] = {}


def _get_secret(key: str, context: Optional["AgentContext"] = None, default: str = "") -> str:
    """Retrieve a secret value from Agent Zero's secrets manager."""
    try:
        from python.helpers.secrets import get_secrets_manager
        secrets_mgr = get_secrets_manager(context)
        secrets = secrets_mgr.load_secrets()
        return secrets.get(key, "").strip() or default
    except Exception as e:
        logger.debug("Could not load secret %s: %s", key, e)
        return default


def is_configured(context: Optional["AgentContext"] = None) -> bool:
    """Check whether Honcho SDK is available and API key is set."""
    if not HONCHO_AVAILABLE:
        return False
    return bool(_get_secret("HONCHO_API_KEY", context))


def get_client(context: Optional["AgentContext"] = None) -> Optional[Any]:
    """Return a cached Honcho client instance (or create one)."""
    if not HONCHO_AVAILABLE:
        return None
    api_key = _get_secret("HONCHO_API_KEY", context)
    if not api_key:
        return None

    workspace_id = _get_secret("HONCHO_WORKSPACE_ID", context, DEFAULT_WORKSPACE_ID)
    if workspace_id in _client_cache:
        return _client_cache[workspace_id]

    try:
        client = Honcho(api_key=api_key, workspace_id=workspace_id)
        _client_cache[workspace_id] = client
        logger.info("Created Honcho client for workspace: %s", workspace_id)
        return client
    except Exception as e:
        logger.error("Failed to create Honcho client: %s", e)
        return None


def get_session_id(context: "AgentContext") -> str:
    """Derive a Honcho session ID from the A0 chat context."""
    if hasattr(context, "id") and context.id:
        return f"chat-{context.id}"
    return f"session-{id(context)}"


def get_user_id(context: Optional["AgentContext"] = None) -> str:
    """Return the configured Honcho user identifier."""
    return _get_secret("HONCHO_USER_ID", context, DEFAULT_USER_ID)


def ensure_initialized(context: "AgentContext") -> bool:
    """Lazily initialize Honcho session for the given context.

    Returns True if Honcho is ready to use, False otherwise.
    """
    if hasattr(context, "_honcho") and context._honcho.get("enabled"):
        return True
    if not is_configured(context):
        return False

    client = get_client(context)
    if not client:
        return False

    if not hasattr(context, "_honcho"):
        context._honcho = {}

    session_id = get_session_id(context)
    try:
        session = client.session(session_id)
        user_peer = client.peer(get_user_id(context))
        agent_peer = client.peer(DEFAULT_AGENT_PEER)
        try:
            session.add_peers([user_peer, agent_peer])
        except Exception:
            pass  # Peers may already be added

        context._honcho["enabled"] = True
        context._honcho["session_id"] = session_id
        logger.info("Honcho session initialized: %s", session_id)
        return True
    except Exception as e:
        logger.error("Honcho init failed: %s", e, exc_info=True)
        context._honcho["enabled"] = False
        return False


def sync_message(context: "AgentContext", role: str, content: str) -> bool:
    """Sync a single message to Honcho.

    Args:
        context: The Agent Zero context.
        role: Either ``"user"`` or ``"assistant"``.
        content: The message text (truncated to 10 000 chars).

    Returns:
        True on success, False otherwise.
    """
    if not ensure_initialized(context):
        return False

    client = get_client(context)
    if not client:
        return False

    try:
        session = client.session(get_session_id(context))
        peer_id = get_user_id(context) if role == "user" else DEFAULT_AGENT_PEER
        peer = client.peer(peer_id)
        msg = peer.message(content[:10_000])
        session.add_messages([msg])
        logger.debug("Synced %s message (%d chars)", role, len(content))
        return True
    except Exception as e:
        logger.error("Message sync failed: %s", e, exc_info=True)
        return False


def get_user_context(context: "AgentContext", max_tokens: int = 500) -> Optional[str]:
    """Fetch persistent user context from Honcho.

    Results are cached for ``CONTEXT_CACHE_TTL`` seconds.
    """
    if not ensure_initialized(context):
        return None

    session_id = get_session_id(context)
    if session_id in _context_cache:
        cached_time, cached_ctx = _context_cache[session_id]
        if time.time() - cached_time < CONTEXT_CACHE_TTL:
            return cached_ctx

    client = get_client(context)
    if not client:
        return None

    try:
        session = client.session(session_id)
        ctx = session.context()
        result = None
        if hasattr(ctx, "summary") and ctx.summary:
            result = ctx.summary
        elif hasattr(ctx, "peer_representation") and ctx.peer_representation:
            result = ctx.peer_representation
        _context_cache[session_id] = (time.time(), result)
        return result
    except Exception as e:
        logger.error("Context retrieval failed: %s", e)
        return None


def clear_context_cache(session_id: Optional[str] = None) -> None:
    """Invalidate the context cache."""
    global _context_cache
    if session_id:
        _context_cache.pop(session_id, None)
    else:
        _context_cache = {}
