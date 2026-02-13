"""AG-UI tool end extension.

Emits TOOL_CALL_END and TOOL_CALL_RESULT events when a tool execution completes.
"""

from python.helpers.extension import Extension
from python.helpers.tool import Response


class AguiToolEnd(Extension):
    """Emit AG-UI tool call end/result events after tool execution."""

    async def execute(self, response: Response | None = None, **kwargs):
        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        # Get the tool call ID from run data
        tool_call_id = run_data.current_tool_call_id
        if not tool_call_id:
            return

        try:
            # Import AG-UI event types
            try:
                from ag_ui.core import ToolCallEndEvent, ToolCallResultEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Emit TOOL_CALL_END
            if agui_available:
                end_event = ToolCallEndEvent(
                    type=EventType.TOOL_CALL_END,
                    tool_call_id=tool_call_id,
                )
            else:
                end_event = {
                    "type": "TOOL_CALL_END",
                    "toolCallId": tool_call_id,
                }
            await queue.put(end_event)

            # Emit TOOL_CALL_RESULT with the tool output
            # SDK requires message_id, tool_call_id, content
            result_content = ""
            if response:
                result_content = response.message or ""

            if agui_available:
                result_event = ToolCallResultEvent(
                    type=EventType.TOOL_CALL_RESULT,
                    message_id=run_data.message_id,
                    tool_call_id=tool_call_id,
                    content=result_content,
                    role="tool",
                )
            else:
                result_event = {
                    "type": "TOOL_CALL_RESULT",
                    "messageId": run_data.message_id,
                    "toolCallId": tool_call_id,
                    "content": result_content,
                    "role": "tool",
                }
            await queue.put(result_event)

            # Clear the current tool call ID
            run_data.current_tool_call_id = None

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Tool end error: {e}")
