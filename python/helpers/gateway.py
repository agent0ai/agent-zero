"""Multi-channel messaging gateway.

Central registry and message router that connects external messaging
platforms to AgentContext via pluggable channel adapters.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from python.helpers.print_style import PrintStyle

if TYPE_CHECKING:
    from python.helpers.channel_bridge import (
        ChannelBridge,
        ChannelClient,
        NormalizedMessage,
    )

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


class RateLimiter:
    """Token-bucket rate limiter per sender."""

    def __init__(
        self,
        max_requests: int = 20,
        window_seconds: float = 60.0,
    ):
        self._max = max_requests
        self._window = window_seconds
        self._lock = threading.Lock()
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        """Return True if the request is within rate limits."""
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            # Evict expired timestamps
            cutoff = now - self._window
            self._buckets[key] = [t for t in bucket if t > cutoff]
            if len(self._buckets[key]) >= self._max:
                return False
            self._buckets[key].append(now)
            return True


# ---------------------------------------------------------------------------
# Channel registry entry
# ---------------------------------------------------------------------------


class _ChannelEntry:
    __slots__ = ("bridge", "client", "last_activity", "message_count", "error")

    def __init__(self, bridge: ChannelBridge, client: ChannelClient):
        self.bridge = bridge
        self.client = client
        self.last_activity: float | None = None
        self.message_count: int = 0
        self.error: str | None = None


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------


class Gateway:
    """Manages channel adapters and routes messages to/from agents."""

    _instance: Gateway | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._channels: dict[str, _ChannelEntry] = {}
        self._rate_limiter = RateLimiter()

    # -- Singleton -----------------------------------------------------------

    @classmethod
    def get(cls) -> Gateway:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Gateway()
        return cls._instance

    # -- Channel registration ------------------------------------------------

    def register_channel(
        self,
        name: str,
        bridge: ChannelBridge,
        client: ChannelClient,
    ) -> None:
        """Register a channel adapter pair."""
        self._channels[name] = _ChannelEntry(bridge, client)
        PrintStyle(font_color="cyan", padding=True).print(
            f"[Gateway] Channel registered: {name} " f"(configured={bridge.is_configured()})"
        )

    def get_channel(self, name: str) -> tuple[ChannelBridge, ChannelClient] | None:
        entry = self._channels.get(name)
        if entry is None:
            return None
        return entry.bridge, entry.client

    def channel_names(self) -> list[str]:
        return list(self._channels.keys())

    # -- Message routing -----------------------------------------------------

    async def receive_message(
        self,
        msg: NormalizedMessage,
        use_context_fn: Any = None,
    ) -> dict[str, Any]:
        """Process an inbound message from any channel.

        Parameters
        ----------
        msg : NormalizedMessage
            Validated, platform-agnostic message.
        use_context_fn : callable, optional
            ``ApiHandler.use_context`` (or equivalent) — resolves an
            ``AgentContext`` by ID.

        Returns
        -------
        dict  with keys ``status``, ``response`` (if synchronous),
        ``context`` (context ID).
        """
        # --- Validation -----------------------------------------------------
        errors = msg.validate()
        if errors:
            return {"status": "error", "errors": errors}

        entry = self._channels.get(msg.channel)
        if entry is None:
            return {"status": "error", "errors": [f"unknown channel: {msg.channel}"]}

        bridge = entry.bridge
        client = entry.client

        # --- Rate limit -----------------------------------------------------
        rate_key = f"{msg.channel}:{msg.sender_id}"
        if not self._rate_limiter.allow(rate_key):
            PrintStyle(font_color="yellow", padding=True).print(f"[Gateway] Rate limited: {rate_key}")
            return {"status": "rate_limited"}

        # --- Deduplication ---------------------------------------------------
        update_id = msg.metadata.get("update_id")
        if update_id is not None:
            if bridge.should_ignore_update(msg.conversation_id, update_id):
                return {"status": "duplicate"}

        # --- Command handling -----------------------------------------------
        stripped = msg.text.strip().lower()
        if stripped in {"/new", "/reset"}:
            bridge.clear_context_for_conversation(msg.conversation_id)
            try:
                await client.send_message(
                    msg.conversation_id,
                    "Context reset. Start a new thread.",
                )
            except Exception as exc:
                PrintStyle.error(f"[Gateway] Reset reply failed: {exc}")
            return {"status": "reset"}

        # --- Context resolution ---------------------------------------------
        ctxid = bridge.get_context_for_conversation(msg.conversation_id)
        if not ctxid:
            ctxid = f"{msg.channel}-{uuid.uuid4().hex}"
        bridge.set_context_for_conversation(msg.conversation_id, ctxid)

        # --- Logging --------------------------------------------------------
        PrintStyle(font_color="white", padding=True).print(
            f"[Gateway:{msg.channel}] {msg.conversation_id}: {msg.text[:120]}"
        )

        # --- Agent communication --------------------------------------------
        if use_context_fn is None:
            return {
                "status": "error",
                "errors": ["no context resolver provided"],
            }

        from agent import AgentContext, UserMessage
        from python.helpers import extension

        context: AgentContext = use_context_fn(ctxid)

        # Extension hook
        ext_data: dict[str, Any] = {
            "message": msg.text,
            "attachment_paths": msg.attachments,
        }
        await extension.call_extensions("user_message_ui", agent=context.get_agent(), data=ext_data)
        processed_text: str = ext_data.get("message", msg.text)

        task = context.communicate(UserMessage(processed_text, msg.attachments))
        result = await task.result()  # type: ignore[union-attr]

        # --- Send response back to platform ---------------------------------
        try:
            await client.send_message(msg.conversation_id, result)
        except Exception as exc:
            PrintStyle.error(f"[Gateway] Reply failed ({msg.channel}): {exc}")
            entry.error = str(exc)

        # --- Book-keeping ---------------------------------------------------
        entry.last_activity = time.time()
        entry.message_count += 1
        entry.error = None

        return {
            "status": "ok",
            "context": ctxid,
            "response": result,
        }

    # -- Status / health -----------------------------------------------------

    def get_all_status(self) -> list[dict[str, Any]]:
        """Return status for every registered channel."""
        result: list[dict[str, Any]] = []
        for name, entry in self._channels.items():
            st = entry.bridge.get_status()
            st.last_activity = entry.last_activity
            st.message_count = entry.message_count
            if entry.error:
                st.error = entry.error
            result.append(
                {
                    "channel": st.channel,
                    "connected": st.connected,
                    "enabled": st.enabled,
                    "error": st.error,
                    "last_activity": st.last_activity,
                    "message_count": st.message_count,
                }
            )
        return result

    def get_channel_status(self, name: str) -> dict[str, Any] | None:
        entry = self._channels.get(name)
        if entry is None:
            return None
        st = entry.bridge.get_status()
        st.last_activity = entry.last_activity
        st.message_count = entry.message_count
        if entry.error:
            st.error = entry.error
        return {
            "channel": st.channel,
            "connected": st.connected,
            "enabled": st.enabled,
            "error": st.error,
            "last_activity": st.last_activity,
            "message_count": st.message_count,
        }
