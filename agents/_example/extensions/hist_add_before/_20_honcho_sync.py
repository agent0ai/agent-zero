"""Honcho Message Sync Extension.

Automatically syncs every user and assistant message to
Honcho when it is appended to the conversation history.
"""

import logging
import sys
import os

from agent import AgentContext
from python.helpers.extension import Extension

logger = logging.getLogger("honcho")

_ext_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ext_dir not in sys.path:
    sys.path.insert(0, _ext_dir)

try:
    import honcho_helper
except ImportError:
    honcho_helper = None  # type: ignore[assignment]


class HonchoSync(Extension):
    """Sync each history entry to Honcho."""

    async def execute(self, **kwargs):
        if honcho_helper is None:
            return

        context: AgentContext = self.agent.context
        content_data = kwargs.get("content_data", {})
        ai = kwargs.get("ai", False)

        # Extract text from the (possibly nested) content payload.
        raw = content_data
        while isinstance(raw, dict):
            extracted = raw.get("content") or raw.get("text") or raw.get("message")
            if extracted is None:
                raw = str(raw)
                break
            raw = extracted

        content = raw if isinstance(raw, str) else str(raw) if raw else ""
        if not content.strip():
            return

        role = "assistant" if ai else "user"

        try:
            honcho_helper.sync_message(context, role, content)
        except Exception as e:
            logger.warning("[Honcho] Sync error (non-fatal): %s", e)
