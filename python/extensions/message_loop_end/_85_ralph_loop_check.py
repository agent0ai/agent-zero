"""
Ralph Loop Check Extension

Checks after each message loop if a Ralph loop should continue.
If active, injects the continuation prompt for the next iteration.
"""

from agent import LoopData
from python.helpers.extension import Extension


class RalphLoopCheck(Extension):
    """
    Extension to manage Ralph loop continuations.

    After each message loop iteration, checks if there's an active
    Ralph loop for this agent and determines whether to:
    1. Complete the loop (completion promise detected)
    2. Stop the loop (max iterations reached)
    3. Continue to next iteration (inject prompt)
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            from instruments.custom.ralph_loop.ralph_manager import RalphLoopManager
            from python.helpers import files

            # Initialize manager
            db_path = files.get_abs_path(
                "./instruments/custom/ralph_loop/data/ralph_loop.db"
            )
            manager = RalphLoopManager(db_path)

            # Get agent ID
            agent_id = str(self.agent.number) if self.agent else None
            if not agent_id:
                return

            # Check for active Ralph loop
            active_loop = manager.get_active_loop(agent_id)
            if not active_loop:
                return  # No active loop, nothing to do

            # Get the last response from this iteration
            last_response = loop_data.last_response or ""

            # Check if loop should complete
            is_complete, reason = manager.check_completion(
                active_loop['loop_id'],
                last_response
            )

            if is_complete:
                # Log completion
                self.agent.context.log.log(
                    type="info",
                    content=f"🔄 Ralph Loop: {reason}",
                    heading=f"Loop #{active_loop['loop_id']} Complete"
                )
                return

            # Loop should continue - advance iteration
            iteration_result = manager.advance_iteration(
                loop_id=active_loop['loop_id'],
                output_summary=last_response[:500] if last_response else None
            )

            # Generate and inject the continuation prompt
            continuation_prompt = manager.generate_iteration_prompt(
                active_loop['loop_id']
            )

            if continuation_prompt:
                # Add to extras for next iteration
                loop_data.extras_persistent["ralph_loop"] = continuation_prompt

                # Log continuation
                self.agent.context.log.log(
                    type="info",
                    content=f"Iteration {iteration_result['iteration']}/{iteration_result['max_iterations'] or '∞'}",
                    heading="🔄 Ralph Loop Continuing"
                )

        except ImportError:
            # Ralph loop module not available
            pass
        except Exception as e:
            # Log but don't break the main loop
            if self.agent and self.agent.context:
                self.agent.context.log.log(
                    type="error",
                    content=f"Ralph loop check error: {e!s}"
                )
