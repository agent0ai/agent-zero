"""A2UI Tool - Generate rich, interactive UIs via A2UI protocol.

This tool allows the LLM to generate A2UI-compliant UI components
that are rendered by connected clients (Flutter, Web Components, etc.).

Per A2UI specification: https://a2ui.org/specification/v0.8-a2ui/
"""

import json
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle


class A2UITool(Tool):
    """Tool for generating A2UI interfaces.

    Supports multiple methods:
    - show: Display a simple UI with components
    - update: Update an existing surface
    - data: Update the data model
    - delete: Remove a surface
    - form: Generate a form with fields
    - message: Display a message
    - progress: Show a progress indicator
    - confirm: Show a confirmation dialog
    """

    async def execute(self, **kwargs):
        method = self.method or "show"

        try:
            if method == "show":
                return await self._show()
            elif method == "update":
                return await self._update()
            elif method == "data":
                return await self._update_data()
            elif method == "delete":
                return await self._delete()
            elif method == "form":
                return await self._form()
            elif method == "message":
                return await self._message()
            elif method == "progress":
                return await self._progress()
            elif method == "confirm":
                return await self._confirm()
            else:
                return Response(
                    message=f"Unknown A2UI method: {method}",
                    break_loop=False,
                )
        except Exception as e:
            PrintStyle(font_color="red").print(f"[A2UI Tool] Error: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                message=f"A2UI error: {e}",
                break_loop=False,
            )

    async def _get_emitter(self):
        """Get the A2UIEmitter for the current agent."""
        from python.helpers.a2ui import A2UIEmitter

        emitter = A2UIEmitter.from_agent(self.agent)
        if not emitter:
            raise RuntimeError(
                "A2UI requires AG-UI connection. "
                "No AG-UI queue available for this agent."
            )
        return emitter

    async def _show(self):
        """Show a UI with components defined in JSON format.

        Args (from self.args):
            surface_id: Surface identifier (default: "@ui")
            components: JSON array of component definitions
            root: ID of the root component
        """
        emitter = await self._get_emitter()
        surface_id = self.args.get("surface_id", "@ui")
        components_json = self.args.get("components", "[]")
        root_id = self.args.get("root", "root")

        # Parse components JSON
        try:
            if isinstance(components_json, str):
                components = json.loads(components_json)
            else:
                components = components_json
        except json.JSONDecodeError as e:
            return Response(
                message=f"Invalid components JSON: {e}",
                break_loop=False,
            )

        # Build A2UI messages
        from python.helpers.a2ui import (
            SurfaceUpdateMessage,
            SurfaceUpdateContent,
            BeginRenderingMessage,
            BeginRenderingContent,
            A2UIComponent,
        )

        # Convert component dicts to A2UIComponent objects
        a2ui_components = []
        for comp in components:
            a2ui_components.append(A2UIComponent(
                id=comp.get("id", f"c_{len(a2ui_components)}"),
                component=comp.get("component", {}),
            ))

        # Emit surface update
        surface_msg = SurfaceUpdateMessage(
            surfaceUpdate=SurfaceUpdateContent(
                surfaceId=surface_id,
                components=a2ui_components,
            )
        )
        await emitter.emit(surface_msg)

        # Emit begin rendering
        render_msg = BeginRenderingMessage(
            beginRendering=BeginRenderingContent(
                surfaceId=surface_id,
                root=root_id,
            )
        )
        await emitter.emit(render_msg)

        return Response(
            message=f"UI displayed on surface '{surface_id}' with {len(a2ui_components)} components",
            break_loop=False,
        )

    async def _update(self):
        """Update components on an existing surface.

        Args (from self.args):
            surface_id: Surface identifier
            components: JSON array of component definitions
        """
        emitter = await self._get_emitter()
        surface_id = self.args.get("surface_id", "@ui")
        components_json = self.args.get("components", "[]")

        try:
            if isinstance(components_json, str):
                components = json.loads(components_json)
            else:
                components = components_json
        except json.JSONDecodeError as e:
            return Response(
                message=f"Invalid components JSON: {e}",
                break_loop=False,
            )

        from python.helpers.a2ui import (
            SurfaceUpdateMessage,
            SurfaceUpdateContent,
            A2UIComponent,
        )

        a2ui_components = [
            A2UIComponent(
                id=comp.get("id", f"c_{i}"),
                component=comp.get("component", {}),
            )
            for i, comp in enumerate(components)
        ]

        msg = SurfaceUpdateMessage(
            surfaceUpdate=SurfaceUpdateContent(
                surfaceId=surface_id,
                components=a2ui_components,
            )
        )
        await emitter.emit(msg)

        return Response(
            message=f"Updated {len(a2ui_components)} components on surface '{surface_id}'",
            break_loop=False,
        )

    async def _update_data(self):
        """Update the data model for reactive bindings.

        Args (from self.args):
            surface_id: Surface identifier
            data: JSON object with data to set
            path: Optional base path for the update
        """
        emitter = await self._get_emitter()
        surface_id = self.args.get("surface_id", "@ui")
        data_json = self.args.get("data", "{}")
        path = self.args.get("path")

        try:
            if isinstance(data_json, str):
                data = json.loads(data_json)
            else:
                data = data_json
        except json.JSONDecodeError as e:
            return Response(
                message=f"Invalid data JSON: {e}",
                break_loop=False,
            )

        await emitter.emit_data_update(surface_id, data, path)

        return Response(
            message=f"Updated data model on surface '{surface_id}'",
            break_loop=False,
        )

    async def _delete(self):
        """Delete a surface.

        Args (from self.args):
            surface_id: Surface identifier to delete
        """
        emitter = await self._get_emitter()
        surface_id = self.args.get("surface_id", "@ui")

        await emitter.emit_delete_surface(surface_id)

        return Response(
            message=f"Deleted surface '{surface_id}'",
            break_loop=False,
        )

    async def _form(self):
        """Generate a form with fields.

        Args (from self.args):
            surface_id: Surface identifier (default: "@form")
            title: Form title
            fields: JSON array of field definitions
            submit_action: Action name for form submission
            submit_label: Label for submit button (default: "Submit")
        """
        emitter = await self._get_emitter()
        surface_id = self.args.get("surface_id", "@form")
        title = self.args.get("title", "Form")
        fields_json = self.args.get("fields", "[]")
        submit_action = self.args.get("submit_action", "submit_form")
        submit_label = self.args.get("submit_label", "Submit")

        try:
            if isinstance(fields_json, str):
                fields = json.loads(fields_json)
            else:
                fields = fields_json
        except json.JSONDecodeError as e:
            return Response(
                message=f"Invalid fields JSON: {e}",
                break_loop=False,
            )

        from python.helpers.a2ui import ComponentBuilder

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

        # Add submit button with form data context
        context = {f"/form/{f.get('name', 'field')}": f"/form/{f.get('name', 'field')}" for f in fields}
        submit_id = builder.button(submit_label, submit_action, context=context, primary=True)
        field_ids.append(submit_id)

        # Layout
        col = builder.column(title_id, *field_ids, spacing=16)
        root = builder.card(col, id="root")

        # Emit
        await emitter.emit_surface(builder, "root")

        return Response(
            message=f"Form '{title}' displayed on surface '{surface_id}' with {len(fields)} fields",
            break_loop=False,
        )

    async def _message(self):
        """Display a message to the user.

        Args (from self.args):
            text: Message text
            hint: Text style hint (h1, h2, body, caption)
            surface_id: Surface identifier (default: "@message")
        """
        emitter = await self._get_emitter()
        text = self.args.get("text", "")
        hint = self.args.get("hint", "body")
        surface_id = self.args.get("surface_id", "@message")

        if not text:
            return Response(
                message="Message text is required",
                break_loop=False,
            )

        await emitter.show_message(text, surface_id=surface_id, hint=hint)

        return Response(
            message=f"Message displayed on surface '{surface_id}'",
            break_loop=False,
        )

    async def _progress(self):
        """Show a progress indicator with message.

        Args (from self.args):
            message: Progress message
            progress_path: Data path for progress value (optional, None=indeterminate)
            surface_id: Surface identifier (default: "@progress")
        """
        emitter = await self._get_emitter()
        message = self.args.get("message", "Loading...")
        progress_path = self.args.get("progress_path")
        surface_id = self.args.get("surface_id", "@progress")

        await emitter.show_progress(message, surface_id=surface_id, progress_path=progress_path)

        return Response(
            message=f"Progress indicator displayed on surface '{surface_id}'",
            break_loop=False,
        )

    async def _confirm(self):
        """Show a confirmation dialog.

        Args (from self.args):
            title: Dialog title
            message: Confirmation message
            confirm_action: Action name for confirm button
            confirm_label: Label for confirm button (default: "Confirm")
            cancel_action: Action name for cancel button
            cancel_label: Label for cancel button (default: "Cancel")
            surface_id: Surface identifier (default: "@confirm")
        """
        emitter = await self._get_emitter()
        title = self.args.get("title", "Confirm")
        message = self.args.get("message", "Are you sure?")
        confirm_action = self.args.get("confirm_action", "confirm")
        confirm_label = self.args.get("confirm_label", "Confirm")
        cancel_action = self.args.get("cancel_action", "cancel")
        cancel_label = self.args.get("cancel_label", "Cancel")
        surface_id = self.args.get("surface_id", "@confirm")

        await emitter.show_confirmation(
            title=title,
            message=message,
            surface_id=surface_id,
            confirm_action=confirm_action,
            confirm_label=confirm_label,
            cancel_action=cancel_action,
            cancel_label=cancel_label,
        )

        return Response(
            message=f"Confirmation dialog displayed on surface '{surface_id}'",
            break_loop=False,
        )
