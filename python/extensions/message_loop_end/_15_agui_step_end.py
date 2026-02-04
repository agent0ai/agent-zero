"""AG-UI step end extension.

Emits STEP_FINISHED and STATE_DELTA events at the end of each message loop iteration.
"""

from python.helpers.extension import Extension


class AguiStepEnd(Extension):
    """Emit AG-UI step finished and state delta events."""

    async def execute(self, **kwargs):
        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        step_id = run_data.current_step_id
        if not step_id:
            return

        try:
            # Import AG-UI event types
            try:
                from ag_ui.core import StepFinishedEvent, StateDeltaEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Emit STATE_DELTA with updated step count (SDK expects delta as list of operations)
            # Using JSON Patch format: [{"op": "replace", "path": "/step_count", "value": N}]
            delta_ops = [
                {"op": "replace", "path": "/step_count", "value": run_data.step_counter}
            ]

            if agui_available:
                state_delta_event = StateDeltaEvent(
                    type=EventType.STATE_DELTA,
                    delta=delta_ops,
                )
            else:
                state_delta_event = {
                    "type": "STATE_DELTA",
                    "delta": delta_ops,
                }
            await queue.put(state_delta_event)

            # Update run_data state
            run_data.state["step_count"] = run_data.step_counter

            # Emit STEP_FINISHED (SDK uses stepName, not step_id)
            step_name = f"loop-{run_data.step_counter}"
            if agui_available:
                step_event = StepFinishedEvent(
                    type=EventType.STEP_FINISHED,
                    step_name=step_name,
                )
            else:
                step_event = {
                    "type": "STEP_FINISHED",
                    "stepName": step_name,
                }
            await queue.put(step_event)

            # Clear current step ID
            run_data.current_step_id = None

            # Note: LoopData is a class with attributes, not a dict
            # The run_agent method in agui_server.py handles completion detection
            # via the agent_task and queue timeout mechanism

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Step end error: {e}")
