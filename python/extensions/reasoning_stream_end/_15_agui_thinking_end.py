"""AG-UI thinking end extension.

Emits THINKING_TEXT_MESSAGE_END and THINKING_END events when
reasoning stream completes.
"""

from python.helpers.extension import Extension


class AguiThinkingEnd(Extension):
    """Emit AG-UI thinking end events when reasoning completes."""

    async def execute(self, **kwargs):
        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        # Only emit if thinking was started
        if not run_data.thinking_started:
            return

        try:
            # Import custom AG-UI thinking event types from server module
            from python.helpers.agui_server import (
                ThinkingTextMessageEndEvent,
                ThinkingEndEvent,
            )

            # Emit thinking text message end
            if run_data.thinking_message_id:
                await queue.put(
                    ThinkingTextMessageEndEvent(
                        message_id=run_data.thinking_message_id,
                    )
                )

            # Emit thinking end
            await queue.put(ThinkingEndEvent())

            # Reset thinking state for potential future thinking blocks
            run_data.thinking_started = False
            run_data.thinking_message_id = None

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Thinking end error: {e}")
