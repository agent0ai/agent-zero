"""Honcho Context Injection Extension.

Injects persistent user context retrieved from Honcho into the
agent's system prompt so the LLM can personalise responses.
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


class HonchoContext(Extension):
    """Append Honcho user context to the system prompt."""

    async def execute(self, **kwargs):
        context: AgentContext = self.agent.context

        try:
            import honcho_helper

            user_context = honcho_helper.get_user_context(context, max_tokens=500)

            if user_context and user_context.strip():
                return (
                    "\n\n# Honcho User Context\n"
                    "- Persistent memory about the user from previous conversations.\n"
                    "- Use this to personalise responses.\n\n"
                    "<honcho_context>\n"
                    f"{user_context}\n"
                    "</honcho_context>\n"
                )
        except ImportError:
            pass
        except Exception as e:
            logger.warning("[Honcho] Context retrieval error (non-fatal): %s", e)

        return ""
