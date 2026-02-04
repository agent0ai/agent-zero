"""A2UI Action Handler Extension.

Handles userAction messages from A2UI clients when users interact
with UI components (buttons, form submissions, etc.).

This extension is invoked at the 'a2ui_action' hook point when
the AG-UI endpoint receives a userAction message.
"""

from python.helpers.extension import Extension
from agent import LoopData


class A2UIActionHandler(Extension):
    """Handle A2UI userAction messages from clients.

    When a user interacts with an A2UI component that has an action
    defined (e.g., clicking a button), this extension processes the
    action and can trigger agent responses.
    """

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        action_name: str = "",
        surface_id: str = "",
        source_component_id: str = "",
        timestamp: str = "",
        context: dict = None,
        **kwargs,
    ):
        """Handle an A2UI userAction.

        Args:
            loop_data: Current agent loop data
            action_name: Name of the action from the component
            surface_id: ID of the surface where action originated
            source_component_id: ID of the component that triggered action
            timestamp: ISO 8601 timestamp of the action
            context: Resolved context data from the action
        """
        from python.helpers.print_style import PrintStyle

        context = context or {}

        PrintStyle(font_color="cyan").print(
            f"[A2UI Action] {action_name} from {source_component_id} "
            f"on surface {surface_id}"
        )

        # Store action data in agent for tools/extensions to access
        self.agent.set_data("_a2ui_last_action", {
            "name": action_name,
            "surfaceId": surface_id,
            "sourceComponentId": source_component_id,
            "timestamp": timestamp,
            "context": context,
        })

        # Emit action received event
        queue = self.agent.get_data("_agui_queue")
        if queue:
            try:
                from ag_ui.core import CustomEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            event_value = {
                "type": "action_received",
                "actionName": action_name,
                "surfaceId": surface_id,
                "context": context,
            }

            if agui_available:
                event = CustomEvent(
                    type=EventType.CUSTOM,
                    name="a2ui_status",
                    value=event_value,
                )
            else:
                event = {
                    "type": "CUSTOM",
                    "name": "a2ui_status",
                    "value": event_value,
                }

            await queue.put(event)

        # The action can be processed by:
        # 1. Custom tools that check _a2ui_last_action
        # 2. Prompts that include action data
        # 3. Other extensions in the a2ui_action chain

        return {
            "action": action_name,
            "surface_id": surface_id,
            "context": context,
            "handled": True,
        }
