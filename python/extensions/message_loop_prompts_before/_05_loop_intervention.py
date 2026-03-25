"""
Loop Intervention Extension

Injects an intervention prompt when a loop is detected, instructing the agent
to stop and ask the user for guidance instead of continuing the loop.
"""

from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import settings
from python.extensions.message_loop_start._15_loop_detection import (
    get_loop_failures,
    reset_loop_failures,
)

# Key for tracking if intervention was injected
DATA_NAME_INTERVENTION_ACTIVE = "loop_intervention_active"


class LoopIntervention(Extension):
    """
    Checks for loop conditions and injects an intervention prompt.

    When the loop failure count exceeds the threshold, this extension
    injects a prompt that tells the agent to stop and ask the user for help.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Get configuration
        set_dict = settings.get_settings()
        enabled = set_dict.get("loop_detection_enabled", True)
        threshold = set_dict.get("loop_detection_threshold", 3)

        if not enabled:
            return

        # Get current failure count
        failures = get_loop_failures(self.agent)

        # Check if we need to inject intervention
        if failures >= threshold:
            # Inject intervention prompt as persistent extra
            # This will be included in the system prompt for this iteration
            intervention_msg = self.agent.parse_prompt(
                "fw.msg_loop_detected.md",
                failure_count=failures,
            )

            # Add to persistent extras so it stays in the prompt
            loop_data.extras_persistent["loop_intervention"] = intervention_msg

            # Mark that intervention is active
            self.agent.set_data(DATA_NAME_INTERVENTION_ACTIVE, True)

            # Log the intervention
            self.agent.context.log.log(
                type="warning",
                heading="Loop detected - injecting user intervention prompt "
                        f"(failures: {failures})",
            )

            # Reset failure counter after intervention
            # to give agent a fresh start
            reset_loop_failures(self.agent)
