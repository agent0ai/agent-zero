"""Honcho Integration Helper for Agent Zero.

Provides a clean, secure interface between Agent Zero and the Honcho
conversational-memory platform (https://honcho.dev).

SDK requirement: ``honcho-ai >= 2.0, < 3.0``
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import AgentContext

log = logging.getLogger("honcho")

# ── Constants ─────────────────────────────────────────────────
DEFAULT_WORKSPACE_ID: str = "agent-zero"
DEFAULT_USER_ID: str = "user"
CONTEXT_CACHE_TTL: int = 120  # seconds
MAX_MESSAGE_LENGTH: int = 10_000  # chars sent to Honcho
LOG_CONTENT_PREVIEW: int = 80  # max chars shown in logs

# Retry settings
_RETRY_ATTEMPTS: int = 3
_RETRY_BASE_DELAY: float = 0.5  # seconds, doubles each attempt

# ── Module-level caches ───────────────────────────────────────
_context_cache: Dict[str, tuple] = {}
_client_cache: Dict[str, Any] = {}

# ── SDK availability ──────────────────────────────────────────
HONCHO_AVAILABLE: bool = False
Honcho: Any = None

try:
    from honcho import Honcho as _Honcho  # type: ignore[import-untyped]

    Honcho = _Honcho
    HONCHO_AVAILABLE = True
    log.debug("Honcho SDK imported successfully")
except ImportError:
    log.debug("Honcho SDK not installed — integration disabled")


# ── Helpers ───────────────────────────────────────────────────
def _truncate(text: str, limit: int = LOG_CONTENT_PREVIEW) -> str:
    """Return a truncated preview of *text* safe for logging."""
    if len(text) <= limit:
        return text
    return text[:limit] + "…[truncated]"


def _retry(fn: Callable) -> Callable:
    """Decorator: retry a function with exponential back-off on exception."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_exc: Optional[Exception] = None
        delay = _RETRY_BASE_DELAY
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < _RETRY_ATTEMPTS:
                    log.debug(
                        "Retry %d/%d for %s after %.1fs — %s",
                        attempt,
                        _RETRY_ATTEMPTS,
                        fn.__name__,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
                    delay *= 2
        log.error("%s failed after %d attempts: %s", fn.__name__, _RETRY_ATTEMPTS, last_exc)
        raise last_exc  # type: ignore[misc]

    return wrapper


def _validate_role(role: str) -> str:
    """Validate and normalise a message role string."""
    role = role.strip().lower()
    if role not in ("user", "assistant"):
        raise ValueError(f"Invalid message role: {role!r}. Must be ‘user’ or ‘assistant’.")
    return role


def _validate_content(content: str, *, field: str = "content") -> str:
    """Validate that *content* is a non-empty string."""
    if not isinstance(content, str):
        raise TypeError(f"{field} must be a string, got {type(content).__name__}")
    content = content.strip()
    if not content:
        raise ValueError(f"{field} must not be empty")
    return content


# ── Config helpers ────────────────────────────────────────────
def get_api_key(context: Optional[AgentContext] = None) -> Optional[str]:
    """Retrieve ``HONCHO_API_KEY`` from Agent Zero’s secrets manager.

    The key is **never** written to logs.
    """
    try:
        from python.helpers.secrets import get_secrets_manager

        secrets_mgr = get_secrets_manager(context)
        secrets = secrets_mgr.load_secrets()
        value = secrets.get("HONCHO_API_KEY", "").strip()
        return value or None
    except Exception:
        log.debug("Unable to load HONCHO_API_KEY from secrets manager")
        return None


def get_config_value(
    key: str,
    default: str,
    context: Optional[AgentContext] = None,
) -> str:
    """Read a configuration value from secrets, falling back to *default*."""
    if not key or not isinstance(key, str):
        return default
    try:
        from python.helpers.secrets import get_secrets_manager

        secrets_mgr = get_secrets_manager(context)
        secrets = secrets_mgr.load_secrets()
        return secrets.get(key.upper(), "").strip() or default
    except Exception:
        return default


def is_configured(context: Optional[AgentContext] = None) -> bool:
    """Return ``True`` when the Honcho SDK is available **and** an API key is set."""
    return HONCHO_AVAILABLE and bool(get_api_key(context))


# ── Client management ─────────────────────────────────────────
def get_client(context: Optional[AgentContext] = None) -> Any:
    """Return a cached :class:`Honcho` client for the current workspace.

    Returns ``None`` when the SDK is unavailable or misconfigured.
    """
    if not HONCHO_AVAILABLE or Honcho is None:
        return None

    api_key = get_api_key(context)
    if not api_key:
        return None

    workspace_id = get_config_value(
        "HONCHO_WORKSPACE_ID", DEFAULT_WORKSPACE_ID, context,
    )

    if workspace_id in _client_cache:
        return _client_cache[workspace_id]

    try:
        client = Honcho(api_key=api_key, workspace_id=workspace_id)
        _client_cache[workspace_id] = client
        log.info("Created Honcho client for workspace: %s", workspace_id)
        return client
    except Exception:
        log.error("Failed to create Honcho client for workspace: %s", workspace_id)
        return None


# ── Session / user helpers ────────────────────────────────────
def get_session_id(context: AgentContext) -> str:
    """Derive a deterministic Honcho session ID from the A0 chat context."""
    if hasattr(context, "id") and context.id:
        return f"chat-{context.id}"
    return f"session-{id(context)}"


def get_user_id(context: Optional[AgentContext] = None) -> str:
    """Return the configured Honcho user identifier."""
    return get_config_value("HONCHO_USER_ID", DEFAULT_USER_ID, context)


# ── Lazy initialisation ───────────────────────────────────────
def ensure_initialized(context: AgentContext) -> bool:
    """Lazily initialise the Honcho session for *context*.

    Returns ``True`` on success, ``False`` otherwise.
    """
    if hasattr(context, "_honcho") and context._honcho.get("enabled"):
        return True

    if not is_configured(context):
        return False

    client = get_client(context)
    if not client:
        return False

    if not hasattr(context, "_honcho"):
        context._honcho = {}  # type: ignore[attr-defined]

    session_id = get_session_id(context)
    try:
        session = client.session(session_id)
        user_peer = client.peer(get_user_id(context))
        agent_peer = client.peer("agent-zero")
        try:
            session.add_peers([user_peer, agent_peer])
        except Exception:
            pass  # peers may already exist

        context._honcho["enabled"] = True
        context._honcho["session_id"] = session_id
        log.info("Initialised Honcho session: %s", session_id)
        return True
    except Exception as exc:
        log.error("Honcho session init failed for %s: %s", session_id, exc)
        context._honcho["enabled"] = False
        return False


# ── Message sync ──────────────────────────────────────────────
@_retry
def _push_message(client: Any, session_id: str, peer: Any, content: str) -> None:
    """Push a single message to Honcho (retried internally)."""
    session = client.session(session_id)
    msg = peer.message(content[:MAX_MESSAGE_LENGTH])
    session.add_messages([msg])


def sync_message(context: AgentContext, role: str, content: str) -> bool:
    """Validate and push a message to Honcho.

    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        role = _validate_role(role)
        content = _validate_content(content)
    except (ValueError, TypeError) as exc:
        log.warning("sync_message validation failed: %s", exc)
        return False

    if not ensure_initialized(context):
        return False

    client = get_client(context)
    if not client:
        return False

    try:
        session_id = get_session_id(context)
        user_id = get_user_id(context)
        peer = client.peer(user_id if role == "user" else "agent-zero")
        _push_message(client, session_id, peer, content)
        log.debug(
            "Synced %s message (%d chars) to %s: %s",
            role,
            len(content),
            session_id,
            _truncate(content),
        )
        return True
    except Exception as exc:
        log.error("sync_message failed: %s", exc)
        return False


# ── User context retrieval ────────────────────────────────────
def get_user_context(
    context: AgentContext,
    max_tokens: int = 500,
) -> Optional[str]:
    """Fetch summarised user context from Honcho (cached).

    Results are cached for :data:`CONTEXT_CACHE_TTL` seconds.
    """
    if not isinstance(max_tokens, int) or max_tokens < 1:
        max_tokens = 500

    if not ensure_initialized(context):
        return None

    session_id = get_session_id(context)

    # Check cache
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
        result: Optional[str] = None
        if hasattr(ctx, "summary") and ctx.summary:
            result = ctx.summary
        elif hasattr(ctx, "peer_representation") and ctx.peer_representation:
            result = ctx.peer_representation
        _context_cache[session_id] = (time.time(), result)
        return result
    except Exception as exc:
        log.error("get_user_context failed for %s: %s", session_id, exc)
        return None


# ── Cache management ──────────────────────────────────────────
def clear_context_cache(session_id: Optional[str] = None) -> None:
    """Invalidate the context cache for one or all sessions."""
    global _context_cache
    if session_id:
        _context_cache.pop(session_id, None)
    else:
        _context_cache = {}
