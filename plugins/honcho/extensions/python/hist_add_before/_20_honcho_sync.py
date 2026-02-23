"""Honcho Message Sync Extension.

Pushes each user/assistant message to Honcho when it is added to the
Agent Zero conversation history.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

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


def _extract_content(content_data: Any) -> str:
    """Recursively extract a plain-text string from *content_data*."""
    raw = content_data
    depth = 0
    while isinstance(raw, dict) and depth < 10:
        extracted = raw.get("content") or raw.get("text") or raw.get("message")
        if extracted is None:
            return str(raw)
        raw = extracted
        depth += 1
    return raw if isinstance(raw, str) else str(raw) if raw else ""


class HonchoSync(Extension):
    """Sync each history message to Honcho."""

    async def execute(self, **kwargs) -> None:
        """Push the incoming message to Honcho."""
        context: AgentContext = self.agent.context

        content_data = kwargs.get("content_data", {})
        ai: bool = kwargs.get("ai", False)
        content = _extract_content(content_data).strip()

        if not content:
            return

        role = "assistant" if ai else "user"

        helper = _get_helper()
        if helper is None:
            return

        try:
            success = helper.sync_message(context, role, content)
            if success:
                log.debug("Synced %s message (%d chars)", role, len(content))
            else:
                log.debug("sync_message returned False for %s", role)
        except Exception as exc:
            log.warning("Honcho sync error (non-fatal): %s", exc)
