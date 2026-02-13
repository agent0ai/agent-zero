"""AG-UI step start extension.

Emits STEP_STARTED and STATE_SNAPSHOT/MESSAGES_SNAPSHOT events at the start of each message loop iteration.
"""

import uuid
from python.helpers.extension import Extension


class AguiStepStart(Extension):
    """Emit AG-UI step started and state snapshot events."""

    async def execute(self, **kwargs):
        # Check if AG-UI is active for this agent
        queue = self.agent.get_data("_agui_queue")
        run_data = self.agent.get_data("_agui_run_data")

        if not queue or not run_data:
            # AG-UI not active, skip
            return

        try:
            # Import AG-UI event types
            try:
                from ag_ui.core import (
                    StepStartedEvent,
                    StateSnapshotEvent,
                    MessagesSnapshotEvent,
                    EventType,
                    Message,
                    Role,
                )
                agui_available = True
            except ImportError:
                agui_available = False

            # Increment step counter and generate step ID
            run_data.step_counter += 1
            step_id = f"step-{uuid.uuid4().hex[:8]}"
            run_data.current_step_id = step_id

            # Emit STEP_STARTED (SDK uses stepName only, no step_id)
            step_name = f"loop-{run_data.step_counter}"
            if agui_available:
                step_event = StepStartedEvent(
                    type=EventType.STEP_STARTED,
                    step_name=step_name,
                )
            else:
                step_event = {
                    "type": "STEP_STARTED",
                    "stepName": step_name,
                }
            await queue.put(step_event)

            # Emit STATE_SNAPSHOT on first step
            if run_data.step_counter == 1:
                state = {
                    "thread_id": run_data.thread_id,
                    "run_id": run_data.run_id,
                    "step_count": run_data.step_counter,
                    "agent_name": self.agent.config.name if hasattr(self.agent.config, "name") else "agent0",
                }
                run_data.state = state

                if agui_available:
                    state_event = StateSnapshotEvent(
                        type=EventType.STATE_SNAPSHOT,
                        snapshot=state,
                    )
                else:
                    state_event = {
                        "type": "STATE_SNAPSHOT",
                        "snapshot": state,
                    }
                await queue.put(state_event)

                # Emit MESSAGES_SNAPSHOT with conversation history
                messages = self._build_messages_snapshot()
                if messages and agui_available:
                    # Convert to Message objects
                    msg_objects = []
                    for msg in messages:
                        role_map = {"user": Role.user, "assistant": Role.assistant, "system": Role.system}
                        role = role_map.get(msg.get("role", "user"), Role.user)
                        msg_objects.append(Message(
                            id=msg.get("id", str(uuid.uuid4())),
                            role=role,
                            content=msg.get("content", ""),
                        ))
                    messages_event = MessagesSnapshotEvent(
                        type=EventType.MESSAGES_SNAPSHOT,
                        messages=msg_objects,
                    )
                    await queue.put(messages_event)
                elif messages:
                    messages_event = {
                        "type": "MESSAGES_SNAPSHOT",
                        "messages": messages,
                    }
                    await queue.put(messages_event)

        except Exception as e:
            # Don't let AG-UI errors affect the main agent loop
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[AG-UI] Step start error: {e}")

    def _build_messages_snapshot(self):
        """Build messages snapshot from agent's conversation history."""
        try:
            messages = []
            # Get history from agent
            history = getattr(self.agent, "history", None)
            if history:
                for idx, msg in enumerate(history):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        # Handle multimodal content
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif isinstance(part, str):
                                text_parts.append(part)
                        content = "\n".join(text_parts)
                    messages.append({
                        "id": f"msg-{idx}",
                        "role": role,
                        "content": content,
                    })
            return messages
        except Exception:
            return []
