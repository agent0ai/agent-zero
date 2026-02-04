"""AG-UI text streaming extension.

Captures parsed response text and emits TEXT_MESSAGE_CONTENT events
to the AG-UI SSE stream.
"""

from python.helpers.extension import Extension
from agent import LoopData


class AguiTextStream(Extension):
    """Emit AG-UI text message events from parsed response stream."""

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):
        from python.helpers.print_style import PrintStyle

        # Debug: log what we receive
        tool_name = parsed.get("tool_name", "N/A") if isinstance(parsed, dict) else "not-dict"
        PrintStyle(font_color="cyan").print(f"[AG-UI Text] tool_name={tool_name}, parsed keys={list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}")

        # Check if this is a response tool with text
        if (
            "tool_name" not in parsed
            or parsed["tool_name"] != "response"
            or "tool_args" not in parsed
            or "text" not in parsed["tool_args"]
            or not parsed["tool_args"]["text"]
        ):
            return  # not a response with text

        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        response_text = parsed["tool_args"]["text"]

        # Track what we've already sent to avoid duplicates
        last_sent = run_data.state.get("_agui_last_text_len", 0)
        if len(response_text) <= last_sent:
            return  # nothing new to send

        # Get the new chunk to send
        new_chunk = response_text[last_sent:]
        run_data.state["_agui_last_text_len"] = len(response_text)

        PrintStyle(font_color="green").print(f"[AG-UI Text] Sending chunk ({len(new_chunk)} chars): {new_chunk[:50]}...")

        try:
            # Import AG-UI event types
            try:
                from ag_ui.core import TextMessageStartEvent, TextMessageContentEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Emit TEXT_MESSAGE_START if not yet started
            if not run_data.text_started:
                run_data.text_started = True
                if agui_available:
                    start_event = TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=run_data.message_id,
                        role="assistant",
                    )
                else:
                    start_event = {
                        "type": "TEXT_MESSAGE_START",
                        "messageId": run_data.message_id,
                        "role": "assistant",
                    }
                await queue.put(start_event)

            # Emit TEXT_MESSAGE_CONTENT for the new chunk
            if agui_available:
                content_event = TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=run_data.message_id,
                    delta=new_chunk,
                )
            else:
                content_event = {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": run_data.message_id,
                    "delta": new_chunk,
                }
            await queue.put(content_event)

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Text stream error: {e}")
