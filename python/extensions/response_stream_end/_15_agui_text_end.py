"""AG-UI text message end extension.

Emits TEXT_MESSAGE_END event when response stream completes.
"""

from python.helpers.extension import Extension


class AguiTextEnd(Extension):
    """Emit AG-UI text message end event when response stream completes."""

    async def execute(self, **kwargs):
        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        # Only emit if text message was started
        if not run_data.text_started:
            return

        try:
            # Import AG-UI event types
            try:
                from ag_ui.core import TextMessageEndEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Emit TEXT_MESSAGE_END
            if agui_available:
                end_event = TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END,
                    message_id=run_data.message_id,
                )
            else:
                end_event = {
                    "type": "TEXT_MESSAGE_END",
                    "messageId": run_data.message_id,
                }
            await queue.put(end_event)

            # Reset text state
            run_data.text_started = False

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Text end error: {e}")
