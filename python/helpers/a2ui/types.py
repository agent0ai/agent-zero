"""A2UI Protocol Pydantic models - v0.8 Specification Compliant.

Implements the A2UI (Agent-to-UI) protocol as defined at:
- https://a2ui.org/specification/v0.8-a2ui/
- https://github.com/google/A2UI

A2UI enables AI agents to generate rich, interactive UIs by sending
declarative JSON payloads that client applications render using native
components (Flutter, Angular, Web Components, etc.).
"""

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# =============================================================================
# Value Types (for data binding)
# =============================================================================

class BoundValue(BaseModel):
    """A value that can be literal or data-bound.

    Per A2UI spec, values can be:
    - Literal: {"literalString": "Hello"}, {"literalNumber": 42}, {"literalBool": true}
    - Data-bound: {"path": "/user/name"}
    """
    literalString: Optional[str] = None
    literalNumber: Optional[float] = None
    literalBool: Optional[bool] = None
    path: Optional[str] = None  # JSON Pointer to data model


class TextValue(BaseModel):
    """Text value - either literal string or data-bound path."""
    literalString: Optional[str] = None
    path: Optional[str] = None


class NumberValue(BaseModel):
    """Number value - either literal number or data-bound path."""
    literalNumber: Optional[float] = None
    path: Optional[str] = None


class BoolValue(BaseModel):
    """Boolean value - either literal bool or data-bound path."""
    literalBool: Optional[bool] = None
    path: Optional[str] = None


# =============================================================================
# Children Reference Types
# =============================================================================

class ChildrenRef(BaseModel):
    """Reference to child components.

    Per A2UI spec, children are specified as:
    - {"explicitList": ["id1", "id2"]} for static lists
    - {"path": "/items"} for data-bound lists
    """
    explicitList: Optional[list[str]] = None
    path: Optional[str] = None


# =============================================================================
# Action Context Entry
# =============================================================================

class ContextEntry(BaseModel):
    """Key-value pair for action context.

    Per A2UI spec, context is an array of key-value pairs where
    value can be literal or data-bound.
    """
    key: str
    value: BoundValue


# =============================================================================
# Component Action
# =============================================================================

class ComponentAction(BaseModel):
    """Action triggered by user interaction.

    Per A2UI spec, actions have:
    - name: Action identifier sent back to server
    - context: Array of key-value pairs (resolved at trigger time)
    """
    name: str
    context: Optional[list[ContextEntry]] = None


# =============================================================================
# Usage Hints (Text Styling)
# =============================================================================

class UsageHint(str, Enum):
    """Text styling hints per A2UI standard catalog."""
    DISPLAY_LARGE = "displayLarge"
    DISPLAY_MEDIUM = "displayMedium"
    DISPLAY_SMALL = "displaySmall"
    HEADLINE_LARGE = "headlineLarge"
    HEADLINE_MEDIUM = "headlineMedium"
    HEADLINE_SMALL = "headlineSmall"
    TITLE_LARGE = "titleLarge"
    TITLE_MEDIUM = "titleMedium"
    TITLE_SMALL = "titleSmall"
    BODY_LARGE = "bodyLarge"
    BODY_MEDIUM = "bodyMedium"
    BODY_SMALL = "bodySmall"
    LABEL_LARGE = "labelLarge"
    LABEL_MEDIUM = "labelMedium"
    LABEL_SMALL = "labelSmall"
    # Shorthand aliases (these map to the above)
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    BODY = "body"
    CAPTION = "caption"


class MainAxisAlignment(str, Enum):
    """Alignment along the main axis."""
    START = "start"
    END = "end"
    CENTER = "center"
    SPACE_BETWEEN = "spaceBetween"
    SPACE_AROUND = "spaceAround"
    SPACE_EVENLY = "spaceEvenly"


class CrossAxisAlignment(str, Enum):
    """Alignment along the cross axis."""
    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"


# =============================================================================
# Standard Catalog Components (A2UI v0.8)
# =============================================================================

class TextComponent(BaseModel):
    """Display text with optional styling.

    Example:
    {"Text": {"text": {"literalString": "Hello"}, "usageHint": "h1"}}
    """
    text: TextValue
    usageHint: Optional[str] = None
    maxLines: Optional[int] = None
    softWrap: Optional[bool] = None


class ButtonComponent(BaseModel):
    """Clickable button with child content and action.

    Example:
    {"Button": {"child": "btn_label", "action": {"name": "submit"}}}
    """
    child: str  # ID reference to child component (usually Text)
    action: ComponentAction
    primary: Optional[bool] = None


class IconButtonComponent(BaseModel):
    """Icon button with action."""
    icon: str  # Material icon name
    action: ComponentAction
    tooltip: Optional[TextValue] = None


class CardComponent(BaseModel):
    """Material card container.

    Example:
    {"Card": {"child": "card_content"}}
    """
    child: str  # ID reference to child component
    elevation: Optional[float] = None


class ColumnComponent(BaseModel):
    """Vertical layout container.

    Example:
    {"Column": {"children": {"explicitList": ["item1", "item2"]}}}
    """
    children: ChildrenRef
    mainAxisAlignment: Optional[str] = None
    crossAxisAlignment: Optional[str] = None
    spacing: Optional[float] = None


class RowComponent(BaseModel):
    """Horizontal layout container.

    Example:
    {"Row": {"children": {"explicitList": ["left", "right"]}}}
    """
    children: ChildrenRef
    mainAxisAlignment: Optional[str] = None
    crossAxisAlignment: Optional[str] = None
    spacing: Optional[float] = None


class ListComponent(BaseModel):
    """Scrollable list container."""
    children: ChildrenRef
    shrinkWrap: Optional[bool] = None


class ExpandedComponent(BaseModel):
    """Expanded flex container."""
    child: str  # ID reference
    flex: Optional[int] = 1


class PaddingComponent(BaseModel):
    """Padding wrapper."""
    child: str  # ID reference
    all: Optional[float] = None
    horizontal: Optional[float] = None
    vertical: Optional[float] = None
    left: Optional[float] = None
    right: Optional[float] = None
    top: Optional[float] = None
    bottom: Optional[float] = None


class SizedBoxComponent(BaseModel):
    """Fixed-size box or spacer."""
    child: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None


class ContainerComponent(BaseModel):
    """General purpose container with styling."""
    child: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    color: Optional[str] = None  # Hex color


class TextFieldComponent(BaseModel):
    """Text input field bound to data path.

    Example:
    {"TextField": {"label": {"literalString": "Name"}, "text": {"path": "/user/name"}}}
    """
    text: TextValue  # Usually data-bound via path
    label: Optional[TextValue] = None
    hint: Optional[TextValue] = None
    obscureText: Optional[bool] = None
    maxLines: Optional[int] = None
    usageHint: Optional[str] = None  # "shortText", "longText", etc.


class DateTimeInputComponent(BaseModel):
    """Date/time picker bound to data path.

    Example:
    {"DateTimeInput": {"value": {"path": "/booking/date"}, "enableDate": true}}
    """
    value: TextValue  # ISO 8601 date string, usually data-bound
    enableDate: Optional[bool] = True
    enableTime: Optional[bool] = False


class CheckBoxComponent(BaseModel):
    """Checkbox bound to boolean data path."""
    value: BoolValue
    label: Optional[TextValue] = None
    action: Optional[ComponentAction] = None


class SwitchComponent(BaseModel):
    """Toggle switch bound to boolean data path."""
    value: BoolValue
    label: Optional[TextValue] = None
    action: Optional[ComponentAction] = None


class SliderComponent(BaseModel):
    """Slider for numeric input."""
    value: NumberValue
    min: Optional[float] = 0
    max: Optional[float] = 100
    divisions: Optional[int] = None
    label: Optional[TextValue] = None


class DropdownComponent(BaseModel):
    """Dropdown selection."""
    value: TextValue
    items: ChildrenRef  # References to DropdownItem components
    label: Optional[TextValue] = None


class DropdownItemComponent(BaseModel):
    """Item in a dropdown."""
    value: str
    label: TextValue


class ListTileComponent(BaseModel):
    """Standard list tile."""
    title: str  # ID reference to title component
    subtitle: Optional[str] = None  # ID reference
    leading: Optional[str] = None  # ID reference (usually icon)
    trailing: Optional[str] = None  # ID reference
    action: Optional[ComponentAction] = None


class DividerComponent(BaseModel):
    """Horizontal divider line."""
    thickness: Optional[float] = None
    indent: Optional[float] = None
    endIndent: Optional[float] = None


class IconComponent(BaseModel):
    """Material icon.

    Example:
    {"Icon": {"name": "check_circle", "size": 24}}
    """
    name: str  # Material icon name
    size: Optional[float] = None
    color: Optional[str] = None  # Hex color


class ImageComponent(BaseModel):
    """Image from URL."""
    url: str
    width: Optional[float] = None
    height: Optional[float] = None
    fit: Optional[str] = None  # "contain", "cover", "fill"


class CircularProgressComponent(BaseModel):
    """Circular progress indicator."""
    value: Optional[NumberValue] = None  # None = indeterminate


class LinearProgressComponent(BaseModel):
    """Linear progress indicator."""
    value: Optional[NumberValue] = None  # None = indeterminate


class ChipComponent(BaseModel):
    """Material chip/tag."""
    label: str  # ID reference to label text
    selected: Optional[BoolValue] = None
    action: Optional[ComponentAction] = None


# =============================================================================
# A2UI v0.8 Standard Catalog Components (Missing from initial implementation)
# =============================================================================

class VideoComponent(BaseModel):
    """Video player component.

    Per A2UI v0.8 spec: Displays video content from a URL.
    """
    url: Union[TextValue, BoundValue]  # Video URL


class AudioPlayerComponent(BaseModel):
    """Audio player component.

    Per A2UI v0.8 spec: Plays audio from a URL with optional description.
    """
    url: Union[TextValue, BoundValue]  # Audio URL
    description: Optional[Union[TextValue, BoundValue]] = None  # Title or summary


class TabItem(BaseModel):
    """Single tab item in a Tabs component."""
    title: Union[TextValue, BoundValue]  # Tab title
    child: str  # ID reference to tab content component


class TabsComponent(BaseModel):
    """Tabbed interface container.

    Per A2UI v0.8 spec: Creates a tabbed interface with multiple content panels.
    """
    tabItems: list[TabItem]  # List of tabs with titles and content


class ModalComponent(BaseModel):
    """Modal dialog container.

    Per A2UI v0.8 spec: Presents an overlay dialog triggered by entry point.
    """
    entryPointChild: str  # ID reference to trigger component
    contentChild: str  # ID reference to modal content


class MultipleChoiceOption(BaseModel):
    """Single option in a MultipleChoice component."""
    label: Union[TextValue, BoundValue]
    value: str


class MultipleChoiceComponent(BaseModel):
    """Multi-select input component.

    Per A2UI v0.8 spec: Allows selection of multiple options.
    """
    selections: Union[BoundValue, list[str]]  # Selected values
    options: list[MultipleChoiceOption]  # Available choices
    maxAllowedSelections: Optional[int] = None  # Max selections allowed


# =============================================================================
# Component Type Mapping
# =============================================================================

COMPONENT_TYPES = {
    # Content Components (Standard Catalog)
    "Text": TextComponent,
    "Icon": IconComponent,
    "Image": ImageComponent,
    "Video": VideoComponent,
    "AudioPlayer": AudioPlayerComponent,
    # Layout Components (Standard Catalog)
    "Column": ColumnComponent,
    "Row": RowComponent,
    "List": ListComponent,
    "Card": CardComponent,
    "Tabs": TabsComponent,
    "Divider": DividerComponent,
    "Modal": ModalComponent,
    # Input Components (Standard Catalog)
    "Button": ButtonComponent,
    "CheckBox": CheckBoxComponent,
    "TextField": TextFieldComponent,
    "DateTimeInput": DateTimeInputComponent,
    "MultipleChoice": MultipleChoiceComponent,
    "Slider": SliderComponent,
    # Extension Components (Beyond Standard Catalog)
    "IconButton": IconButtonComponent,
    "Switch": SwitchComponent,
    "Expanded": ExpandedComponent,
    "Padding": PaddingComponent,
    "SizedBox": SizedBoxComponent,
    "Container": ContainerComponent,
    "Dropdown": DropdownComponent,
    "DropdownItem": DropdownItemComponent,
    "ListTile": ListTileComponent,
    "CircularProgress": CircularProgressComponent,
    "LinearProgress": LinearProgressComponent,
    "Chip": ChipComponent,
}


# =============================================================================
# A2UI Component (Node in the adjacency list)
# =============================================================================

class A2UIComponent(BaseModel):
    """A single component in the A2UI adjacency list.

    Per A2UI spec, the component is an object with a single key
    (the component type) mapping to the component's properties.

    Example:
    {
        "id": "greeting",
        "component": {
            "Text": {
                "text": {"literalString": "Hello, World!"},
                "usageHint": "h1"
            }
        }
    }
    """
    id: str  # Unique identifier for this component
    weight: Optional[float] = None  # For ordering
    component: dict[str, Any]  # {"ComponentType": {...properties...}}


# =============================================================================
# Data Model Entry (for dataModelUpdate)
# =============================================================================

class DataEntry(BaseModel):
    """Entry in the data model adjacency list.

    Per A2UI spec, data entries use:
    - valueString, valueNumber, valueBoolean for literals
    - valueMap for nested objects (array of DataEntry)
    - valueList for arrays
    """
    key: str
    valueString: Optional[str] = None
    valueNumber: Optional[float] = None
    valueBoolean: Optional[bool] = None
    valueMap: Optional[list["DataEntry"]] = None
    valueList: Optional[list["DataEntry"]] = None


# =============================================================================
# A2UI Protocol Messages (Server-to-Client)
# =============================================================================

class BeginRenderingContent(BaseModel):
    """Content of beginRendering message (v0.8)."""
    surfaceId: str
    root: str  # ID of the root component
    catalogId: Optional[str] = None  # Component catalog URI


class CreateSurfaceContent(BaseModel):
    """Content of createSurface message (v0.9+)."""
    surfaceId: str
    catalogId: str  # Required in v0.9


class SurfaceUpdateContent(BaseModel):
    """Content of surfaceUpdate message."""
    surfaceId: str
    components: list[A2UIComponent]


class DeleteComponentsContent(BaseModel):
    """Content of deleteComponents message."""
    surfaceId: str
    componentIds: list[str]


class DataModelUpdateContent(BaseModel):
    """Content of dataModelUpdate message."""
    surfaceId: str
    path: Optional[str] = None  # JSON Pointer path (e.g., "user" or "form/field")
    contents: list[DataEntry]


class DeleteSurfaceContent(BaseModel):
    """Content of deleteSurface message."""
    surfaceId: str


# =============================================================================
# A2UI Message Wrappers (envelope format)
# =============================================================================

class BeginRenderingMessage(BaseModel):
    """beginRendering message (v0.8).

    Signals client to begin rendering after components are sent.
    """
    beginRendering: BeginRenderingContent


class CreateSurfaceMessage(BaseModel):
    """createSurface message (v0.9+).

    Signals client to create a new surface.
    """
    createSurface: CreateSurfaceContent


class SurfaceUpdateMessage(BaseModel):
    """surfaceUpdate message.

    Adds or updates components on a surface.
    """
    surfaceUpdate: SurfaceUpdateContent


class DeleteComponentsMessage(BaseModel):
    """deleteComponents message.

    Removes components from a surface.
    """
    deleteComponents: DeleteComponentsContent


class DataModelUpdateMessage(BaseModel):
    """dataModelUpdate message.

    Updates the data model for reactive bindings.
    """
    dataModelUpdate: DataModelUpdateContent


class DeleteSurfaceMessage(BaseModel):
    """deleteSurface message.

    Removes a surface entirely.
    """
    deleteSurface: DeleteSurfaceContent


# =============================================================================
# A2UI Client-to-Server Messages
# =============================================================================

class UserActionContent(BaseModel):
    """Content of userAction message.

    Sent when user interacts with a component that has an action.
    """
    name: str  # Action name from component's action.name
    surfaceId: str
    sourceComponentId: str  # ID of component that triggered action
    timestamp: str  # ISO 8601 timestamp
    context: dict[str, Any]  # Resolved context from action.context


class ErrorContent(BaseModel):
    """Content of error message from client."""
    message: str
    code: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class UserActionMessage(BaseModel):
    """userAction message from client."""
    userAction: UserActionContent


class ClientErrorMessage(BaseModel):
    """error message from client."""
    error: ErrorContent


# =============================================================================
# Union Types
# =============================================================================

# Server-to-Client messages
A2UIServerMessage = Union[
    BeginRenderingMessage,
    CreateSurfaceMessage,
    SurfaceUpdateMessage,
    DeleteComponentsMessage,
    DataModelUpdateMessage,
    DeleteSurfaceMessage,
]

# Client-to-Server messages
A2UIClientMessage = Union[
    UserActionMessage,
    ClientErrorMessage,
]


# =============================================================================
# AG-UI Transport Integration
# =============================================================================

class A2UICustomEventValue(BaseModel):
    """A2UI message wrapped as AG-UI custom event value.

    A2UI messages are sent via AG-UI CustomEvent with:
    - name: "a2ui"
    - value: {"mimeType": "application/json+a2ui", "data": <a2ui_message>}
    """
    mimeType: Literal["application/json+a2ui"] = "application/json+a2ui"
    data: dict[str, Any]  # The A2UI message as dict
