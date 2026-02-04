"""A2UI Integration Helpers for Agent Zero.

Provides high-level integration utilities for using A2UI within
Agent Zero tools, extensions, and custom code.

Example usage in a tool:

    from python.helpers.a2ui.integration import (
        show_form,
        show_message,
        show_confirmation,
        get_last_action,
    )

    # In your tool's execute method:
    async def execute(self, **kwargs):
        await show_form(
            self.agent,
            title="User Details",
            fields=[
                {"name": "email", "label": "Email", "type": "text"},
                {"name": "subscribe", "label": "Newsletter", "type": "checkbox"},
            ],
            submit_action="save_user",
        )
        return Response(message="Form displayed", break_loop=False)
"""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent


async def show_form(
    agent: "Agent",
    title: str,
    fields: list[dict[str, Any]],
    submit_action: str = "submit_form",
    *,
    submit_label: str = "Submit",
    surface_id: str = "@form",
) -> bool:
    """Display a form UI to the user.

    Args:
        agent: Agent instance
        title: Form title
        fields: List of field definitions:
            - name: Field name (used in data path)
            - label: Display label
            - type: Field type (text, password, checkbox, switch, date, datetime)
            - hint: Optional placeholder hint
        submit_action: Action name for form submission
        submit_label: Submit button label
        surface_id: Surface identifier

    Returns:
        True if form was displayed, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter, ComponentBuilder

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    builder = ComponentBuilder(surface_id)

    # Add title
    title_id = builder.text(title, hint="h1")

    # Add fields
    field_ids = []
    for field in fields:
        field_name = field.get("name", "field")
        field_label = field.get("label", field_name)
        field_type = field.get("type", "text")
        field_path = field.get("path", f"/form/{field_name}")

        if field_type == "text":
            field_id = builder.text_field(
                label=field_label,
                path=field_path,
                hint=field.get("hint"),
            )
        elif field_type == "password":
            field_id = builder.text_field(
                label=field_label,
                path=field_path,
                obscure=True,
            )
        elif field_type == "checkbox":
            field_id = builder.checkbox(
                label=field_label,
                path=field_path,
            )
        elif field_type == "switch":
            field_id = builder.switch(
                label=field_label,
                path=field_path,
            )
        elif field_type == "date":
            field_id = builder.date_time_input(
                path=field_path,
                enable_date=True,
                enable_time=False,
            )
        elif field_type == "datetime":
            field_id = builder.date_time_input(
                path=field_path,
                enable_date=True,
                enable_time=True,
            )
        else:
            field_id = builder.text_field(
                label=field_label,
                path=field_path,
            )

        field_ids.append(field_id)

    # Add submit button
    context = {f.get("name", "field"): f"/form/{f.get('name', 'field')}" for f in fields}
    submit_id = builder.button(submit_label, submit_action, context=context, primary=True)
    field_ids.append(submit_id)

    # Layout
    col = builder.column(title_id, *field_ids, spacing=16)
    root = builder.card(col, id="root")

    # Emit
    return await emitter.emit_surface(builder, "root")


async def show_message(
    agent: "Agent",
    text: str,
    *,
    hint: str = "body",
    surface_id: str = "@message",
) -> bool:
    """Display a simple message to the user.

    Args:
        agent: Agent instance
        text: Message text
        hint: Text style hint (h1, h2, body, caption)
        surface_id: Surface identifier

    Returns:
        True if displayed, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.show_message(text, surface_id=surface_id, hint=hint)


async def show_progress(
    agent: "Agent",
    message: str,
    *,
    progress_path: Optional[str] = None,
    surface_id: str = "@progress",
) -> bool:
    """Display a progress indicator.

    Args:
        agent: Agent instance
        message: Progress message
        progress_path: Data path for progress value (None = indeterminate)
        surface_id: Surface identifier

    Returns:
        True if displayed, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.show_progress(message, surface_id=surface_id, progress_path=progress_path)


async def show_error(
    agent: "Agent",
    title: str,
    message: str,
    *,
    action: Optional[str] = None,
    action_label: str = "Dismiss",
    surface_id: str = "@error",
) -> bool:
    """Display an error message.

    Args:
        agent: Agent instance
        title: Error title
        message: Error details
        action: Optional action name for dismiss button
        action_label: Label for the action button
        surface_id: Surface identifier

    Returns:
        True if displayed, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.show_error(
        title=title,
        message=message,
        surface_id=surface_id,
        action=action,
        action_label=action_label,
    )


async def show_confirmation(
    agent: "Agent",
    title: str,
    message: str,
    *,
    confirm_action: str = "confirm",
    confirm_label: str = "Confirm",
    cancel_action: str = "cancel",
    cancel_label: str = "Cancel",
    surface_id: str = "@confirm",
) -> bool:
    """Display a confirmation dialog.

    Args:
        agent: Agent instance
        title: Dialog title
        message: Confirmation message
        confirm_action: Action name for confirm button
        confirm_label: Label for confirm button
        cancel_action: Action name for cancel button
        cancel_label: Label for cancel button
        surface_id: Surface identifier

    Returns:
        True if displayed, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.show_confirmation(
        title=title,
        message=message,
        surface_id=surface_id,
        confirm_action=confirm_action,
        confirm_label=confirm_label,
        cancel_action=cancel_action,
        cancel_label=cancel_label,
    )


async def delete_surface(
    agent: "Agent",
    surface_id: str,
) -> bool:
    """Delete a surface.

    Args:
        agent: Agent instance
        surface_id: Surface identifier

    Returns:
        True if deleted, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.emit_delete_surface(surface_id)


async def update_data(
    agent: "Agent",
    surface_id: str,
    data: dict[str, Any],
    *,
    path: Optional[str] = None,
) -> bool:
    """Update the data model for a surface.

    Args:
        agent: Agent instance
        surface_id: Surface identifier
        data: Data to set
        path: Optional base path

    Returns:
        True if updated, False if AG-UI not active
    """
    from python.helpers.a2ui import A2UIEmitter

    emitter = A2UIEmitter.from_agent(agent)
    if not emitter:
        return False

    return await emitter.emit_data_update(surface_id, data, path)


def get_last_action(agent: "Agent") -> Optional[dict[str, Any]]:
    """Get the last A2UI user action received.

    Args:
        agent: Agent instance

    Returns:
        Dict with action data or None if no action received:
        {
            "name": "action_name",
            "surfaceId": "surface_id",
            "sourceComponentId": "component_id",
            "timestamp": "2025-01-01T12:00:00Z",
            "context": {...}
        }
    """
    return agent.get_data("_a2ui_last_action")


def is_a2ui_active(agent: "Agent") -> bool:
    """Check if A2UI is available for an agent.

    Args:
        agent: Agent instance

    Returns:
        True if AG-UI queue is available
    """
    return agent.get_data("_agui_queue") is not None
