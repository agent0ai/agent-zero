"""AG-UI thinking/reasoning streaming extension.

Captures LLM reasoning chunks (Claude extended thinking) and emits
THINKING_TEXT_MESSAGE_CONTENT events to the AG-UI SSE stream.
"""

import uuid
from python.helpers.extension import Extension


class AguiThinkingStream(Extension):
    """Emit AG-UI thinking message events from reasoning stream chunks."""

    async def execute(self, **kwargs):
        # Get stream data from kwargs
        stream_data = kwargs.get("stream_data")
        if not stream_data:
            return

        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        chunk = stream_data.get("chunk", "")
        if not chunk:
            return

        try:
            # Import custom AG-UI thinking event types from server module
            from python.helpers.agui_server import (
                ThinkingStartEvent,
                ThinkingTextMessageStartEvent,
                ThinkingTextMessageContentEvent,
            )

            # Emit THINKING_START if not yet started
            if not run_data.thinking_started:
                run_data.thinking_started = True
                run_data.thinking_message_id = str(uuid.uuid4())

                # Emit thinking start
                await queue.put(ThinkingStartEvent())

                # Emit thinking text message start
                await queue.put(
                    ThinkingTextMessageStartEvent(
                        message_id=run_data.thinking_message_id,
                    )
                )

            # Emit THINKING_TEXT_MESSAGE_CONTENT for the chunk
            await queue.put(
                ThinkingTextMessageContentEvent(
                    message_id=run_data.thinking_message_id,
                    delta=chunk,
                )
            )

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Thinking stream error: {e}")
