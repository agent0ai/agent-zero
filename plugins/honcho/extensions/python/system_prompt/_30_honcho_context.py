"""Honcho Context Injection Extension.

Injects persistent user context from Honcho into the agent’s system
prompt.  Uses lazy initialisation — no restart required when secrets
are added after startup.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from python.helpers.extension import Extension

if TYPE_CHECKING:
    from agent import AgentContext

log = logging.getLogger("honcho")

# ── Load helper via importlib (no sys.path mutation) ──────────
_HELPER_PATH = str(
    Path(__file__).resolve().parents[3] / "helpers" / "honcho_helper.py"
)

_helper_module = None


def _get_helper():
    """Lazily load and cache honcho_helper without mutating sys.path."""
    global _helper_module
    if _helper_module is not None:
        return _helper_module
    spec = importlib.util.spec_from_file_location("honcho_helper", _HELPER_PATH)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        log.debug("Failed to load honcho_helper: %s", exc)
        return None
    _helper_module = mod
    return mod


_CONTEXT_TEMPLATE = """

# Honcho User Context
- Persistent memory about the user from previous conversations.
- Use this information to personalise responses.

<honcho_context>
{context}
</honcho_context>
"""


class HonchoContext(Extension):
    """Append Honcho user context to the system prompt."""

    async def execute(self, **kwargs) -> str:
        """Return a system-prompt fragment with Honcho context, or empty string."""
        context: AgentContext = self.agent.context

        try:
            helper = _get_helper()
            if helper is None:
                return ""

            user_context = helper.get_user_context(context, max_tokens=500)

            if user_context and user_context.strip():
                return _CONTEXT_TEMPLATE.format(context=user_context.strip())
        except Exception as exc:
            log.warning("Honcho context injection error (non-fatal): %s", exc)

        return ""
