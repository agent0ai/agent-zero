"""A2UI Emitter - Integration with AG-UI transport layer.

Provides the A2UIEmitter class that bridges A2UI messages to the
AG-UI SSE streaming protocol used by Agent Zero.

A2UI messages are sent via AG-UI CustomEvent with:
- type: "CUSTOM"
- name: "a2ui"
- value: {"mimeType": "application/json+a2ui", "data": <a2ui_message>}
"""

import asyncio
from typing import Any, Optional, TYPE_CHECKING
from datetime import datetime

from pydantic import BaseModel

from .types import (
    SurfaceUpdateMessage,
    BeginRenderingMessage,
    DataModelUpdateMessage,
    DeleteSurfaceMessage,
    A2UIServerMessage,
)
from .components import ComponentBuilder, DataModelBuilder
from .surfaces import SurfaceManager, get_surface_manager

if TYPE_CHECKING:
    from agent import Agent


class A2UIEmitter:
    """Emits A2UI messages through AG-UI transport.

    Integrates with Agent Zero's AG-UI infrastructure to stream
    A2UI protocol messages to connected clients.
    """

    # MIME type for A2UI messages
    MIME_TYPE = "application/json+a2ui"

    def __init__(
        self,
        queue: asyncio.Queue,
        surface_manager: Optional[SurfaceManager] = None,
    ):
        """Initialize the A2UIEmitter.

        Args:
            queue: AG-UI event queue for streaming
            surface_manager: Optional SurfaceManager (uses default if not provided)
        """
        self._queue = queue
        self._surfaces = surface_manager or get_surface_manager()

    @property
    def surface_manager(self) -> SurfaceManager:
        """Get the SurfaceManager."""
        return self._surfaces

    @classmethod
    def from_agent(cls, agent: "Agent") -> Optional["A2UIEmitter"]:
        """Create an A2UIEmitter from an Agent's AG-UI context.

        Args:
            agent: Agent instance with AG-UI queue

        Returns:
            A2UIEmitter if AG-UI is active, None otherwise
        """
        queue = agent.get_data("_agui_queue")
        if not queue:
            return None

        # Get or create surface manager from agent data
        manager = agent.get_data("_a2ui_surface_manager")
        if not manager:
            manager = SurfaceManager()
            agent.set_data("_a2ui_surface_manager", manager)

        return cls(queue, manager)

    async def emit(self, message: A2UIServerMessage) -> bool:
        """Emit an A2UI message via AG-UI custom event.

        Args:
            message: A2UI message (SurfaceUpdate, BeginRendering, etc.)

        Returns:
            True if emitted successfully
        """
        try:
            # Import AG-UI SDK if available
            try:
                from ag_ui.core import CustomEvent, EventType
                agui_available = True
            except ImportError:
                agui_available = False

            # Serialize the A2UI message
            if isinstance(message, BaseModel):
                a2ui_data = message.model_dump(exclude_none=True)
            else:
                a2ui_data = message

            # Wrap as AG-UI custom event
            event_value = {
                "mimeType": self.MIME_TYPE,
                "data": a2ui_data,
            }

            if agui_available:
                event = CustomEvent(
                    type=EventType.CUSTOM,
                    name="a2ui",
                    value=event_value,
                )
            else:
                event = {
                    "type": "CUSTOM",
                    "name": "a2ui",
                    "value": event_value,
                }

            await self._queue.put(event)
            return True

        except Exception as e:
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="yellow").print(f"[A2UI] Emit error: {e}")
            return False

    async def emit_surface_update(
        self,
        builder: ComponentBuilder,
    ) -> bool:
        """Emit a surfaceUpdate message from a ComponentBuilder.

        Args:
            builder: ComponentBuilder with components to send

        Returns:
            True if emitted successfully
        """
        # Update surface state
        surface_id = builder.surface_id
        state, _ = self._surfaces.get_or_create(surface_id)

        for comp in builder.components:
            state.components[comp.id] = comp

        # Emit the message
        message = builder.build_surface_update()
        return await self.emit(message)

    async def emit_begin_rendering(
        self,
        surface_id: str,
        root: str,
    ) -> bool:
        """Emit a beginRendering message.

        Args:
            surface_id: Surface identifier
            root: ID of the root component

        Returns:
            True if emitted successfully
        """
        try:
            message = self._surfaces.begin_rendering(surface_id, root)
            return await self.emit(message)
        except ValueError:
            # Surface doesn't exist, create it first
            self._surfaces.create(surface_id)
            message = self._surfaces.begin_rendering(surface_id, root)
            return await self.emit(message)

    async def emit_surface(
        self,
        builder: ComponentBuilder,
        root_id: str,
    ) -> bool:
        """Convenience: emit surfaceUpdate + beginRendering.

        Args:
            builder: ComponentBuilder with components
            root_id: ID of the root component

        Returns:
            True if both emitted successfully
        """
        success = await self.emit_surface_update(builder)
        if success:
            success = await self.emit_begin_rendering(builder.surface_id, root_id)
        return success

    async def emit_data_update(
        self,
        surface_id: str,
        data: dict[str, Any],
        path: Optional[str] = None,
    ) -> bool:
        """Emit a dataModelUpdate message.

        Args:
            surface_id: Surface identifier
            data: Data to set
            path: Optional base path

        Returns:
            True if emitted successfully
        """
        try:
            message = self._surfaces.update_data(surface_id, data, path)
            return await self.emit(message)
        except ValueError:
            # Surface doesn't exist, create it first
            self._surfaces.create(surface_id)
            message = self._surfaces.update_data(surface_id, data, path)
            return await self.emit(message)

    async def emit_delete_surface(self, surface_id: str) -> bool:
        """Emit a deleteSurface message.

        Args:
            surface_id: Surface identifier

        Returns:
            True if emitted successfully
        """
        message = self._surfaces.delete(surface_id)
        return await self.emit(message)

    # =========================================================================
    # Convenience Methods for Common Patterns
    # =========================================================================

    async def show_message(
        self,
        text: str,
        *,
        surface_id: str = "@message",
        hint: str = "body",
    ) -> bool:
        """Show a simple text message.

        Args:
            text: Message text
            surface_id: Surface identifier
            hint: Text usage hint (h1, h2, body, etc.)

        Returns:
            True if emitted successfully
        """
        builder = ComponentBuilder(surface_id)
        root = builder.text(text, hint=hint, id="root")
        return await self.emit_surface(builder, root)

    async def show_progress(
        self,
        message: str,
        *,
        surface_id: str = "@progress",
        progress_path: Optional[str] = None,
    ) -> bool:
        """Show a progress indicator with message.

        Args:
            message: Progress message
            surface_id: Surface identifier
            progress_path: Data path for progress value (None = indeterminate)

        Returns:
            True if emitted successfully
        """
        builder = ComponentBuilder(surface_id)
        text = builder.text(message)
        progress = builder.circular_progress(path=progress_path)
        root = builder.column(progress, text, main_axis="center", id="root")
        return await self.emit_surface(builder, root)

    async def show_error(
        self,
        title: str,
        message: str,
        *,
        surface_id: str = "@error",
        action: Optional[str] = None,
        action_label: str = "Dismiss",
    ) -> bool:
        """Show an error message with optional action.

        Args:
            title: Error title
            message: Error details
            surface_id: Surface identifier
            action: Action name for dismiss button
            action_label: Label for the action button

        Returns:
            True if emitted successfully
        """
        builder = ComponentBuilder(surface_id)
        icon = builder.icon("error", color="#F44336", size=48)
        title_txt = builder.text(title, hint="h2")
        msg_txt = builder.text(message)

        children = [icon, title_txt, msg_txt]

        if action:
            btn = builder.button(action_label, action)
            children.append(btn)

        col = builder.column(*children, spacing=16)
        root = builder.card(col, id="root")
        return await self.emit_surface(builder, root)

    async def show_confirmation(
        self,
        title: str,
        message: str,
        *,
        surface_id: str = "@confirm",
        confirm_action: str = "confirm",
        confirm_label: str = "Confirm",
        cancel_action: str = "cancel",
        cancel_label: str = "Cancel",
    ) -> bool:
        """Show a confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            surface_id: Surface identifier
            confirm_action: Action name for confirm button
            confirm_label: Label for confirm button
            cancel_action: Action name for cancel button
            cancel_label: Label for cancel button

        Returns:
            True if emitted successfully
        """
        builder = ComponentBuilder(surface_id)
        title_txt = builder.text(title, hint="h2")
        msg_txt = builder.text(message)
        confirm_btn = builder.button(confirm_label, confirm_action, primary=True)
        cancel_btn = builder.button(cancel_label, cancel_action)
        buttons = builder.row(cancel_btn, confirm_btn, main_axis="end", spacing=8)
        col = builder.column(title_txt, msg_txt, buttons, spacing=16)
        root = builder.card(col, id="root")
        return await self.emit_surface(builder, root)


# =========================================================================
# Helper Functions
# =========================================================================

async def emit_a2ui(agent: "Agent", message: A2UIServerMessage) -> bool:
    """Emit an A2UI message from an agent.

    Convenience function for emitting A2UI messages without
    explicitly creating an emitter.

    Args:
        agent: Agent instance with AG-UI queue
        message: A2UI message to emit

    Returns:
        True if emitted, False if AG-UI not active
    """
    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False
    return await emitter.emit(message)


def get_emitter(agent: "Agent") -> Optional[A2UIEmitter]:
    """Get an A2UIEmitter for an agent.

    Args:
        agent: Agent instance

    Returns:
        A2UIEmitter if AG-UI is active, None otherwise
    """
    return A2UIEmitter.from_agent(agent)
