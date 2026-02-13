"""A2UI Component Builder - Fluent API for building A2UI components.

Provides a developer-friendly interface for constructing A2UI component
trees that comply with the A2UI v0.8 specification.

Example usage:
    builder = ComponentBuilder(surface_id="booking")

    # Build form with fluent API
    title = builder.text("Book Your Table", hint="h1")
    date_input = builder.text_field("Date", path="/booking/date")
    submit = builder.button("Confirm", action="confirm_booking")

    # Layout
    form = builder.column(title, date_input, submit)
    root = builder.card(form, id="root")

    # Get messages
    surface_update = builder.build_surface_update()
    begin_rendering = builder.build_begin_rendering(root="root")
"""

from typing import Any, Optional
from datetime import datetime

from .types import (
    A2UIComponent,
    TextValue,
    NumberValue,
    BoolValue,
    ChildrenRef,
    ComponentAction,
    ContextEntry,
    BoundValue,
    SurfaceUpdateContent,
    SurfaceUpdateMessage,
    BeginRenderingContent,
    BeginRenderingMessage,
    DataModelUpdateContent,
    DataModelUpdateMessage,
    DataEntry,
    UsageHint,
)


class ComponentBuilder:
    """Fluent API for building A2UI components.

    Creates A2UI-compliant component definitions using a developer-friendly
    interface. Components are stored in an adjacency list and can be
    serialized to A2UI protocol messages.
    """

    def __init__(self, surface_id: str = "@default"):
        """Initialize a new ComponentBuilder.

        Args:
            surface_id: Identifier for the rendering surface
        """
        self._surface_id = surface_id
        self._components: list[A2UIComponent] = []
        self._id_counter = 0

    @property
    def surface_id(self) -> str:
        """Get the surface ID."""
        return self._surface_id

    @property
    def components(self) -> list[A2UIComponent]:
        """Get the list of components."""
        return self._components

    def _next_id(self, prefix: str = "c") -> str:
        """Generate a unique component ID."""
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def _add(self, component: A2UIComponent) -> str:
        """Add a component and return its ID."""
        self._components.append(component)
        return component.id

    # =========================================================================
    # Text Components
    # =========================================================================

    def text(
        self,
        content: str,
        *,
        hint: Optional[str] = None,
        path: Optional[str] = None,
        max_lines: Optional[int] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Text component.

        Args:
            content: The text to display (ignored if path is provided)
            hint: Usage hint for styling (h1, h2, body, caption, etc.)
            path: Data binding path (e.g., "/user/name")
            max_lines: Maximum lines before truncation
            id: Custom component ID (auto-generated if not provided)

        Returns:
            Component ID for referencing in layouts
        """
        cid = id or self._next_id("txt")
        text_value = {"path": path} if path else {"literalString": content}

        props: dict[str, Any] = {"text": text_value}
        if hint:
            props["usageHint"] = hint
        if max_lines is not None:
            props["maxLines"] = max_lines

        return self._add(A2UIComponent(
            id=cid,
            component={"Text": props}
        ))

    # =========================================================================
    # Button Components
    # =========================================================================

    def button(
        self,
        label: str,
        action: str,
        *,
        context: Optional[dict[str, Any]] = None,
        primary: Optional[bool] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Button with a text label.

        Args:
            label: Button text
            action: Action name sent to server on click
            context: Key-value pairs to include in action context
            primary: Whether this is a primary/emphasized button
            id: Custom component ID

        Returns:
            Component ID for the button
        """
        # Create label text component
        label_id = self.text(label)

        cid = id or self._next_id("btn")

        # Build action with context
        action_obj: dict[str, Any] = {"name": action}
        if context:
            action_obj["context"] = [
                {"key": k, "value": self._make_bound_value(v)}
                for k, v in context.items()
            ]

        props: dict[str, Any] = {
            "child": label_id,
            "action": action_obj,
        }
        if primary is not None:
            props["primary"] = primary

        return self._add(A2UIComponent(
            id=cid,
            component={"Button": props}
        ))

    def button_with_child(
        self,
        child_id: str,
        action: str,
        *,
        context: Optional[dict[str, Any]] = None,
        primary: Optional[bool] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Button with a custom child component.

        Args:
            child_id: ID of the child component
            action: Action name sent to server on click
            context: Key-value pairs to include in action context
            primary: Whether this is a primary/emphasized button
            id: Custom component ID

        Returns:
            Component ID for the button
        """
        cid = id or self._next_id("btn")

        action_obj: dict[str, Any] = {"name": action}
        if context:
            action_obj["context"] = [
                {"key": k, "value": self._make_bound_value(v)}
                for k, v in context.items()
            ]

        props: dict[str, Any] = {
            "child": child_id,
            "action": action_obj,
        }
        if primary is not None:
            props["primary"] = primary

        return self._add(A2UIComponent(
            id=cid,
            component={"Button": props}
        ))

    def icon_button(
        self,
        icon: str,
        action: str,
        *,
        context: Optional[dict[str, Any]] = None,
        tooltip: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add an IconButton.

        Args:
            icon: Material icon name (e.g., "add", "close", "menu")
            action: Action name sent to server on click
            context: Key-value pairs to include in action context
            tooltip: Optional tooltip text
            id: Custom component ID

        Returns:
            Component ID for the button
        """
        cid = id or self._next_id("ibtn")

        action_obj: dict[str, Any] = {"name": action}
        if context:
            action_obj["context"] = [
                {"key": k, "value": self._make_bound_value(v)}
                for k, v in context.items()
            ]

        props: dict[str, Any] = {
            "icon": icon,
            "action": action_obj,
        }
        if tooltip:
            props["tooltip"] = {"literalString": tooltip}

        return self._add(A2UIComponent(
            id=cid,
            component={"IconButton": props}
        ))

    # =========================================================================
    # Layout Components
    # =========================================================================

    def column(
        self,
        *children: str,
        spacing: Optional[float] = None,
        main_axis: Optional[str] = None,
        cross_axis: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Stack children vertically.

        Args:
            *children: Component IDs to arrange vertically
            spacing: Gap between children
            main_axis: Alignment along vertical axis
            cross_axis: Alignment along horizontal axis
            id: Custom component ID

        Returns:
            Component ID for the column
        """
        cid = id or self._next_id("col")

        props: dict[str, Any] = {
            "children": {"explicitList": list(children)}
        }
        if spacing is not None:
            props["spacing"] = spacing
        if main_axis:
            props["mainAxisAlignment"] = main_axis
        if cross_axis:
            props["crossAxisAlignment"] = cross_axis

        return self._add(A2UIComponent(
            id=cid,
            component={"Column": props}
        ))

    def row(
        self,
        *children: str,
        spacing: Optional[float] = None,
        main_axis: Optional[str] = None,
        cross_axis: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Arrange children horizontally.

        Args:
            *children: Component IDs to arrange horizontally
            spacing: Gap between children
            main_axis: Alignment along horizontal axis
            cross_axis: Alignment along vertical axis
            id: Custom component ID

        Returns:
            Component ID for the row
        """
        cid = id or self._next_id("row")

        props: dict[str, Any] = {
            "children": {"explicitList": list(children)}
        }
        if spacing is not None:
            props["spacing"] = spacing
        if main_axis:
            props["mainAxisAlignment"] = main_axis
        if cross_axis:
            props["crossAxisAlignment"] = cross_axis

        return self._add(A2UIComponent(
            id=cid,
            component={"Row": props}
        ))

    def list(
        self,
        *children: str,
        shrink_wrap: Optional[bool] = None,
        id: Optional[str] = None,
    ) -> str:
        """Create a scrollable list.

        Args:
            *children: Component IDs for list items
            shrink_wrap: Whether list shrinks to content size
            id: Custom component ID

        Returns:
            Component ID for the list
        """
        cid = id or self._next_id("list")

        props: dict[str, Any] = {
            "children": {"explicitList": list(children)}
        }
        if shrink_wrap is not None:
            props["shrinkWrap"] = shrink_wrap

        return self._add(A2UIComponent(
            id=cid,
            component={"List": props}
        ))

    def card(
        self,
        child: str,
        *,
        elevation: Optional[float] = None,
        id: Optional[str] = None,
    ) -> str:
        """Wrap content in a Material card.

        Args:
            child: Component ID to wrap
            elevation: Card shadow elevation
            id: Custom component ID

        Returns:
            Component ID for the card
        """
        cid = id or self._next_id("card")

        props: dict[str, Any] = {"child": child}
        if elevation is not None:
            props["elevation"] = elevation

        return self._add(A2UIComponent(
            id=cid,
            component={"Card": props}
        ))

    def expanded(
        self,
        child: str,
        *,
        flex: int = 1,
        id: Optional[str] = None,
    ) -> str:
        """Expand a child to fill available space.

        Args:
            child: Component ID to expand
            flex: Flex factor for space distribution
            id: Custom component ID

        Returns:
            Component ID for the expanded wrapper
        """
        cid = id or self._next_id("exp")

        return self._add(A2UIComponent(
            id=cid,
            component={"Expanded": {"child": child, "flex": flex}}
        ))

    def padding(
        self,
        child: str,
        *,
        all: Optional[float] = None,
        horizontal: Optional[float] = None,
        vertical: Optional[float] = None,
        left: Optional[float] = None,
        right: Optional[float] = None,
        top: Optional[float] = None,
        bottom: Optional[float] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add padding around a component.

        Args:
            child: Component ID to pad
            all: Padding on all sides
            horizontal: Left and right padding
            vertical: Top and bottom padding
            left, right, top, bottom: Individual side padding
            id: Custom component ID

        Returns:
            Component ID for the padding wrapper
        """
        cid = id or self._next_id("pad")

        props: dict[str, Any] = {"child": child}
        if all is not None:
            props["all"] = all
        if horizontal is not None:
            props["horizontal"] = horizontal
        if vertical is not None:
            props["vertical"] = vertical
        if left is not None:
            props["left"] = left
        if right is not None:
            props["right"] = right
        if top is not None:
            props["top"] = top
        if bottom is not None:
            props["bottom"] = bottom

        return self._add(A2UIComponent(
            id=cid,
            component={"Padding": props}
        ))

    def sized_box(
        self,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        child: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Create a fixed-size box or spacer.

        Args:
            width: Fixed width
            height: Fixed height
            child: Optional child component ID
            id: Custom component ID

        Returns:
            Component ID for the sized box
        """
        cid = id or self._next_id("box")

        props: dict[str, Any] = {}
        if width is not None:
            props["width"] = width
        if height is not None:
            props["height"] = height
        if child:
            props["child"] = child

        return self._add(A2UIComponent(
            id=cid,
            component={"SizedBox": props}
        ))

    def spacer(self, size: float = 16, *, vertical: bool = True) -> str:
        """Create a spacer (convenience for sized_box).

        Args:
            size: Spacer size in pixels
            vertical: If True, creates vertical space; else horizontal

        Returns:
            Component ID for the spacer
        """
        if vertical:
            return self.sized_box(height=size)
        return self.sized_box(width=size)

    def divider(
        self,
        *,
        thickness: Optional[float] = None,
        indent: Optional[float] = None,
        end_indent: Optional[float] = None,
        id: Optional[str] = None,
    ) -> str:
        """Create a horizontal divider line.

        Args:
            thickness: Line thickness
            indent: Left indentation
            end_indent: Right indentation
            id: Custom component ID

        Returns:
            Component ID for the divider
        """
        cid = id or self._next_id("div")

        props: dict[str, Any] = {}
        if thickness is not None:
            props["thickness"] = thickness
        if indent is not None:
            props["indent"] = indent
        if end_indent is not None:
            props["endIndent"] = end_indent

        return self._add(A2UIComponent(
            id=cid,
            component={"Divider": props}
        ))

    # =========================================================================
    # Input Components
    # =========================================================================

    def text_field(
        self,
        label: str,
        path: str,
        *,
        hint: Optional[str] = None,
        obscure: bool = False,
        max_lines: Optional[int] = None,
        usage_hint: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a TextField bound to a data path.

        Args:
            label: Field label
            path: Data binding path (e.g., "/form/username")
            hint: Placeholder hint text
            obscure: Hide input (for passwords)
            max_lines: Maximum lines (1 for single-line)
            usage_hint: Input hint ("shortText", "longText", etc.)
            id: Custom component ID

        Returns:
            Component ID for the text field
        """
        cid = id or self._next_id("input")

        props: dict[str, Any] = {
            "text": {"path": path},
            "label": {"literalString": label},
        }
        if hint:
            props["hint"] = {"literalString": hint}
        if obscure:
            props["obscureText"] = True
        if max_lines is not None:
            props["maxLines"] = max_lines
        if usage_hint:
            props["usageHint"] = usage_hint

        return self._add(A2UIComponent(
            id=cid,
            component={"TextField": props}
        ))

    def date_time_input(
        self,
        path: str,
        *,
        enable_date: bool = True,
        enable_time: bool = False,
        id: Optional[str] = None,
    ) -> str:
        """Add a DateTimeInput bound to a data path.

        Args:
            path: Data binding path for ISO 8601 date string
            enable_date: Show date picker
            enable_time: Show time picker
            id: Custom component ID

        Returns:
            Component ID for the date/time input
        """
        cid = id or self._next_id("dt")

        props: dict[str, Any] = {
            "value": {"path": path},
        }
        if enable_date:
            props["enableDate"] = True
        if enable_time:
            props["enableTime"] = True

        return self._add(A2UIComponent(
            id=cid,
            component={"DateTimeInput": props}
        ))

    def checkbox(
        self,
        label: str,
        path: str,
        *,
        action: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a CheckBox bound to a data path.

        Args:
            label: Checkbox label
            path: Data binding path for boolean value
            action: Optional action on change
            id: Custom component ID

        Returns:
            Component ID for the checkbox
        """
        cid = id or self._next_id("chk")

        props: dict[str, Any] = {
            "value": {"path": path},
            "label": {"literalString": label},
        }
        if action:
            props["action"] = {"name": action}

        return self._add(A2UIComponent(
            id=cid,
            component={"CheckBox": props}
        ))

    def switch(
        self,
        label: str,
        path: str,
        *,
        action: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Switch bound to a data path.

        Args:
            label: Switch label
            path: Data binding path for boolean value
            action: Optional action on change
            id: Custom component ID

        Returns:
            Component ID for the switch
        """
        cid = id or self._next_id("sw")

        props: dict[str, Any] = {
            "value": {"path": path},
            "label": {"literalString": label},
        }
        if action:
            props["action"] = {"name": action}

        return self._add(A2UIComponent(
            id=cid,
            component={"Switch": props}
        ))

    def slider(
        self,
        path: str,
        *,
        min_val: float = 0,
        max_val: float = 100,
        divisions: Optional[int] = None,
        label: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Slider bound to a data path.

        Args:
            path: Data binding path for numeric value
            min_val: Minimum value
            max_val: Maximum value
            divisions: Number of discrete divisions
            label: Optional label
            id: Custom component ID

        Returns:
            Component ID for the slider
        """
        cid = id or self._next_id("slider")

        props: dict[str, Any] = {
            "value": {"path": path},
            "min": min_val,
            "max": max_val,
        }
        if divisions is not None:
            props["divisions"] = divisions
        if label:
            props["label"] = {"literalString": label}

        return self._add(A2UIComponent(
            id=cid,
            component={"Slider": props}
        ))

    # =========================================================================
    # Display Components
    # =========================================================================

    def icon(
        self,
        name: str,
        *,
        size: Optional[float] = None,
        color: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Material icon.

        Args:
            name: Material icon name (e.g., "check_circle", "error")
            size: Icon size in pixels
            color: Hex color (e.g., "#FF0000")
            id: Custom component ID

        Returns:
            Component ID for the icon
        """
        cid = id or self._next_id("icon")

        props: dict[str, Any] = {"name": name}
        if size is not None:
            props["size"] = size
        if color:
            props["color"] = color

        return self._add(A2UIComponent(
            id=cid,
            component={"Icon": props}
        ))

    def image(
        self,
        url: str,
        *,
        width: Optional[float] = None,
        height: Optional[float] = None,
        fit: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add an Image from URL.

        Args:
            url: Image URL
            width: Image width
            height: Image height
            fit: Fit mode ("contain", "cover", "fill")
            id: Custom component ID

        Returns:
            Component ID for the image
        """
        cid = id or self._next_id("img")

        props: dict[str, Any] = {"url": url}
        if width is not None:
            props["width"] = width
        if height is not None:
            props["height"] = height
        if fit:
            props["fit"] = fit

        return self._add(A2UIComponent(
            id=cid,
            component={"Image": props}
        ))

    def circular_progress(
        self,
        *,
        path: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a circular progress indicator.

        Args:
            path: Data binding path for progress value (None = indeterminate)
            id: Custom component ID

        Returns:
            Component ID for the progress indicator
        """
        cid = id or self._next_id("prog")

        props: dict[str, Any] = {}
        if path:
            props["value"] = {"path": path}

        return self._add(A2UIComponent(
            id=cid,
            component={"CircularProgress": props}
        ))

    def linear_progress(
        self,
        *,
        path: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a linear progress indicator.

        Args:
            path: Data binding path for progress value (None = indeterminate)
            id: Custom component ID

        Returns:
            Component ID for the progress indicator
        """
        cid = id or self._next_id("prog")

        props: dict[str, Any] = {}
        if path:
            props["value"] = {"path": path}

        return self._add(A2UIComponent(
            id=cid,
            component={"LinearProgress": props}
        ))

    def chip(
        self,
        label: str,
        *,
        selected_path: Optional[str] = None,
        action: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a Material chip/tag.

        Args:
            label: Chip label text
            selected_path: Data binding path for selected state
            action: Action name on tap
            id: Custom component ID

        Returns:
            Component ID for the chip
        """
        label_id = self.text(label)
        cid = id or self._next_id("chip")

        props: dict[str, Any] = {"label": label_id}
        if selected_path:
            props["selected"] = {"path": selected_path}
        if action:
            props["action"] = {"name": action}

        return self._add(A2UIComponent(
            id=cid,
            component={"Chip": props}
        ))

    def list_tile(
        self,
        title: str,
        *,
        subtitle: Optional[str] = None,
        leading_icon: Optional[str] = None,
        trailing_icon: Optional[str] = None,
        action: Optional[str] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a ListTile.

        Args:
            title: Title text
            subtitle: Optional subtitle text
            leading_icon: Optional leading Material icon name
            trailing_icon: Optional trailing Material icon name
            action: Action name on tap
            id: Custom component ID

        Returns:
            Component ID for the list tile
        """
        title_id = self.text(title)

        cid = id or self._next_id("tile")
        props: dict[str, Any] = {"title": title_id}

        if subtitle:
            props["subtitle"] = self.text(subtitle, hint="caption")
        if leading_icon:
            props["leading"] = self.icon(leading_icon)
        if trailing_icon:
            props["trailing"] = self.icon(trailing_icon)
        if action:
            props["action"] = {"name": action}

        return self._add(A2UIComponent(
            id=cid,
            component={"ListTile": props}
        ))

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _make_bound_value(self, value: Any) -> dict[str, Any]:
        """Convert a Python value to A2UI BoundValue format.

        If value is a string starting with '/', treat as data path.
        Otherwise, use appropriate literal type.
        """
        if isinstance(value, str):
            if value.startswith("/"):
                return {"path": value}
            return {"literalString": value}
        elif isinstance(value, bool):
            return {"literalBool": value}
        elif isinstance(value, (int, float)):
            return {"literalNumber": value}
        else:
            return {"literalString": str(value)}

    # =========================================================================
    # Build Methods
    # =========================================================================

    def build_surface_update(self) -> SurfaceUpdateMessage:
        """Build a surfaceUpdate message with all components.

        Returns:
            SurfaceUpdateMessage ready for serialization
        """
        return SurfaceUpdateMessage(
            surfaceUpdate=SurfaceUpdateContent(
                surfaceId=self._surface_id,
                components=self._components
            )
        )

    def build_begin_rendering(
        self,
        root: str,
        catalog_id: Optional[str] = None,
    ) -> BeginRenderingMessage:
        """Build a beginRendering message.

        Args:
            root: ID of the root component
            catalog_id: Optional component catalog URI

        Returns:
            BeginRenderingMessage ready for serialization
        """
        content = BeginRenderingContent(
            surfaceId=self._surface_id,
            root=root,
        )
        if catalog_id:
            content.catalogId = catalog_id

        return BeginRenderingMessage(beginRendering=content)

    def to_dict(self) -> dict[str, Any]:
        """Get all components as a dictionary.

        Returns:
            Dict with surfaceId and components list
        """
        return {
            "surfaceId": self._surface_id,
            "components": [c.model_dump(exclude_none=True) for c in self._components]
        }

    def reset(self) -> "ComponentBuilder":
        """Clear all components and reset ID counter.

        Returns:
            Self for chaining
        """
        self._components = []
        self._id_counter = 0
        return self


class DataModelBuilder:
    """Builder for A2UI data model updates."""

    def __init__(self, surface_id: str = "@default"):
        """Initialize a new DataModelBuilder.

        Args:
            surface_id: Identifier for the rendering surface
        """
        self._surface_id = surface_id
        self._entries: list[DataEntry] = []
        self._path: Optional[str] = None

    def at_path(self, path: str) -> "DataModelBuilder":
        """Set the base path for the update.

        Args:
            path: JSON Pointer path (e.g., "user" or "form/field")

        Returns:
            Self for chaining
        """
        self._path = path
        return self

    def set(self, key: str, value: Any) -> "DataModelBuilder":
        """Set a value in the data model.

        Args:
            key: Key name
            value: Value (string, number, bool, or nested dict)

        Returns:
            Self for chaining
        """
        entry = self._make_entry(key, value)
        self._entries.append(entry)
        return self

    def _make_entry(self, key: str, value: Any) -> DataEntry:
        """Create a DataEntry from a Python value."""
        if isinstance(value, str):
            return DataEntry(key=key, valueString=value)
        elif isinstance(value, bool):
            return DataEntry(key=key, valueBoolean=value)
        elif isinstance(value, (int, float)):
            return DataEntry(key=key, valueNumber=float(value))
        elif isinstance(value, dict):
            nested = [self._make_entry(k, v) for k, v in value.items()]
            return DataEntry(key=key, valueMap=nested)
        elif isinstance(value, list):
            nested = [self._make_entry(str(i), v) for i, v in enumerate(value)]
            return DataEntry(key=key, valueList=nested)
        else:
            return DataEntry(key=key, valueString=str(value))

    def build(self) -> DataModelUpdateMessage:
        """Build a dataModelUpdate message.

        Returns:
            DataModelUpdateMessage ready for serialization
        """
        return DataModelUpdateMessage(
            dataModelUpdate=DataModelUpdateContent(
                surfaceId=self._surface_id,
                path=self._path,
                contents=self._entries
            )
        )

    def reset(self) -> "DataModelBuilder":
        """Clear all entries and path.

        Returns:
            Self for chaining
        """
        self._entries = []
        self._path = None
        return self
