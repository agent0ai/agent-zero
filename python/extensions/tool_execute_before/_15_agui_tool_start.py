"""AG-UI tool start extension.

Emits TOOL_CALL_START and TOOL_CALL_ARGS events when a tool execution begins.
"""

import json
import uuid
from python.helpers.extension import Extension


class AguiToolStart(Extension):
    """Emit AG-UI tool call start events before tool execution."""

    async def execute(self, **kwargs):
        # Get tool info from kwargs
        tool = kwargs.get("tool")
        tool_name = kwargs.get("tool_name", "")
        tool_args = kwargs.get("tool_args", {})

        if not tool_name:
            return

        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        try:
            # Generate tool call ID
            tool_call_id = f"tc-{uuid.uuid4().hex[:8]}"

            # Store for use in tool_execute_after
            run_data.current_tool_call_id = tool_call_id

            # Import AG-UI event types
            try:
                from ag_ui.core import ToolCallStartEvent, ToolCallArgsEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Emit TOOL_CALL_START
            if agui_available:
                start_event = ToolCallStartEvent(
                    type=EventType.TOOL_CALL_START,
                    tool_call_id=tool_call_id,
                    tool_call_name=tool_name,
                )
            else:
                start_event = {
                    "type": "TOOL_CALL_START",
                    "toolCallId": tool_call_id,
                    "toolCallName": tool_name,
                }
            await queue.put(start_event)

            # Emit TOOL_CALL_ARGS with the arguments
            if tool_args:
                args_json = json.dumps(tool_args)
                if agui_available:
                    args_event = ToolCallArgsEvent(
                        type=EventType.TOOL_CALL_ARGS,
                        tool_call_id=tool_call_id,
                        delta=args_json,
                    )
                else:
                    args_event = {
                        "type": "TOOL_CALL_ARGS",
                        "toolCallId": tool_call_id,
                        "delta": args_json,
                    }
                await queue.put(args_event)

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Tool start error: {e}")
