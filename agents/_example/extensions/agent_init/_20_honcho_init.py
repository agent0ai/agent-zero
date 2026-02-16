"""Honcho Initialization Extension.

Initializes the Honcho conversational memory client when the
agent context starts.  Activation is lazy — if the API key is
not configured the extension silently does nothing.
"""

import logging
import sys
import os

from agent import AgentContext
from python.helpers.extension import Extension

logger = logging.getLogger("honcho")

# Ensure the parent extensions directory is importable so that
# ``honcho_helper`` can be resolved as a top-level module.
_ext_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ext_dir not in sys.path:
    sys.path.insert(0, _ext_dir)


class HonchoInit(Extension):
    """Bootstrap Honcho integration on agent start."""

    async def execute(self, **kwargs):
        context: AgentContext = self.agent.context

        try:
            import honcho_helper

            if not honcho_helper.is_configured(context):
                return  # Not configured — skip silently

            client = honcho_helper.get_client(context)
            if client:
                session_id = honcho_helper.get_session_id(context)
                logger.info("[Honcho] Integration enabled for session: %s", session_id)

                if not hasattr(context, "_honcho"):
                    context._honcho = {}
                context._honcho["enabled"] = True
                context._honcho["session_id"] = session_id
        except ImportError:
            logger.debug("[Honcho] SDK not available — skipping init")
        except Exception as e:
            logger.warning("[Honcho] Init error (non-fatal): %s", e)
