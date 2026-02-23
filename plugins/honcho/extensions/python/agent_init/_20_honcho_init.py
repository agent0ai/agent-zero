"""Honcho Initialization Extension.

Activates the Honcho conversational-memory integration when an agent
context starts.  If the SDK is missing or unconfigured the extension
is silently skipped.
"""

from __future__ import annotations

import importlib.util
import logging
import os
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


def _load_helper():
    """Import honcho_helper without mutating sys.path."""
    spec = importlib.util.spec_from_file_location("honcho_helper", _HELPER_PATH)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class HonchoInit(Extension):
    """One-time Honcho integration bootstrap per agent context."""

    async def execute(self, **kwargs) -> None:
        """Initialise Honcho for the current agent context."""
        context: AgentContext = self.agent.context

        try:
            helper = _load_helper()
            if helper is None:
                log.debug("honcho_helper.py not found at %s", _HELPER_PATH)
                return

            if not helper.is_configured(context):
                return  # SDK missing or API key not set — skip

            client = helper.get_client(context)
            if client:
                session_id = helper.get_session_id(context)
                log.info("Honcho integration enabled (session: %s)", session_id)

                if not hasattr(context, "_honcho"):
                    context._honcho = {}
                context._honcho["enabled"] = True
                context._honcho["session_id"] = session_id
        except ImportError as exc:
            log.debug("Honcho helper unavailable: %s", exc)
        except Exception as exc:
            log.warning("Honcho init error (non-fatal): %s", exc)
