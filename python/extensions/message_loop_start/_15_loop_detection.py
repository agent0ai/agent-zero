"""
Loop Detection Extension

Tracks iteration patterns to detect when the agent is stuck in a loop.
A loop is detected when the same action/result signature repeats consecutively.
"""

from python.helpers.extension import Extension
from agent import Agent, LoopData
from python.helpers import settings

# Data keys for storing loop detection state
DATA_NAME_HISTORY = "loop_detection_history"
DATA_NAME_FAILURES = "loop_detection_failures"
DATA_NAME_LAST_MISFORMAT = "loop_detection_last_misformat"

# Default configuration (can be overridden in settings)
DEFAULT_HISTORY_SIZE = 5
DEFAULT_FAILURE_THRESHOLD = 3


class LoopDetection(Extension):
    """
    Detects when the agent is stuck in a loop by tracking action signatures.

    A loop is detected when:
    1. The same response signature repeats consecutively
    2. Misformat errors occur repeatedly
    3. The agent fails to make progress across iterations
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Get configuration from settings
        set_dict = settings.get_settings()
        history_size = set_dict.get(
            "loop_detection_history_size", DEFAULT_HISTORY_SIZE
        )
        failure_threshold = set_dict.get(
            "loop_detection_threshold", DEFAULT_FAILURE_THRESHOLD
        )
        enabled = set_dict.get("loop_detection_enabled", True)

        if not enabled:
            return

        # Get current state
        history = self.agent.get_data(DATA_NAME_HISTORY) or []
        failures = self.agent.get_data(DATA_NAME_FAILURES) or 0
        last_misformat = self.agent.get_data(DATA_NAME_LAST_MISFORMAT) or False

        # Create signature from current iteration state
        signature = self._create_signature(loop_data, last_misformat)

        # Detect loop: same signature repeated consecutively
        if len(history) >= 2:
            # Check if the last few signatures are the same (loop detected)
            recent = history[-2:]
            if all(s == signature for s in recent):
                failures += 1
            else:
                # Different signature - reset if we had progress
                if not last_misformat:
                    failures = max(0, failures - 1)

        # Store updated state
        history.append(signature)
        # Keep only last N entries
        history = history[-history_size:]
        self.agent.set_data(DATA_NAME_HISTORY, history)
        self.agent.set_data(DATA_NAME_FAILURES, failures)

        # Reset misformat flag for next iteration
        self.agent.set_data(DATA_NAME_LAST_MISFORMAT, False)

        # Log if approaching threshold
        if failures > 0 and failures < failure_threshold:
            self.agent.context.log.log(
                type="info",
                heading="Loop detection: "
                        f"{failures}/{failure_threshold} consecutive patterns",
            )

    def _create_signature(self, loop_data: LoopData, was_misformat: bool) -> str:
        """
        Create a hashable signature of the current iteration state.

        This signature is used to detect repeated patterns across iterations.
        """
        parts = []

        # Track misformat state
        if was_misformat:
            parts.append("MISFORMAT")

        # Track last response (truncated to avoid noise from minor variations)
        if loop_data.last_response:
            # Use first 100 chars hash to catch similar responses
            response_preview = loop_data.last_response[:100].strip()
            parts.append(f"RESP:{hash(response_preview)}")

        # Track tool name if available
        if loop_data.current_tool:
            tool_name = loop_data.current_tool.__class__.__name__
            parts.append(f"TOOL:{tool_name}")

        # If no parts, use iteration number to track "no action" state
        if not parts:
            parts.append("NO_ACTION")

        return "|".join(parts)


def get_loop_failures(agent: Agent) -> int:
    """Get the current loop failure count for an agent."""
    return agent.get_data(DATA_NAME_FAILURES) or 0


def reset_loop_failures(agent: Agent) -> None:
    """Reset the loop failure counter for an agent."""
    agent.set_data(DATA_NAME_FAILURES, 0)


def set_misformat_flag(agent: Agent) -> None:
    """Set the misformat flag to indicate the last iteration had a misformat."""
    agent.set_data(DATA_NAME_LAST_MISFORMAT, True)
