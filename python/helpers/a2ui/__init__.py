"""A2UI Protocol Integration for Agent Zero.

A2UI (Agent-to-UI) enables AI agents to generate rich, interactive UIs
by sending declarative JSON payloads that client applications render
using native components (Flutter, Angular, Web Components, etc.).

This module provides:
- Pydantic models for A2UI v0.8 protocol messages
- ComponentBuilder for fluent UI construction
- SurfaceManager for lifecycle management
- A2UIEmitter for AG-UI transport integration

Official specification: https://a2ui.org/specification/v0.8-a2ui/
GitHub: https://github.com/google/A2UI

Basic Usage:
    from python.helpers.a2ui import ComponentBuilder, A2UIEmitter

    # Build UI components
    builder = ComponentBuilder(surface_id="booking")
    title = builder.text("Book Your Table", hint="h1")
    submit = builder.button("Confirm", action="confirm_booking")
    root = builder.column(title, submit, id="root")

    # Emit to client via AG-UI
    emitter = A2UIEmitter.from_agent(agent)
    await emitter.emit_surface(builder, root)
"""

# Types - A2UI protocol message models
from .types import (
    # Value types
    BoundValue,
    TextValue,
    NumberValue,
    BoolValue,
    ChildrenRef,
    ContextEntry,
    ComponentAction,
    # Enums
    UsageHint,
    MainAxisAlignment,
    CrossAxisAlignment,
    # Standard Catalog Components - Content
    TextComponent,
    IconComponent,
    ImageComponent,
    VideoComponent,
    AudioPlayerComponent,
    # Standard Catalog Components - Layout
    ColumnComponent,
    RowComponent,
    ListComponent,
    CardComponent,
    TabItem,
    TabsComponent,
    DividerComponent,
    ModalComponent,
    # Standard Catalog Components - Input
    ButtonComponent,
    CheckBoxComponent,
    TextFieldComponent,
    DateTimeInputComponent,
    MultipleChoiceOption,
    MultipleChoiceComponent,
    SliderComponent,
    # Extension Components
    IconButtonComponent,
    SwitchComponent,
    ExpandedComponent,
    PaddingComponent,
    SizedBoxComponent,
    ContainerComponent,
    DropdownComponent,
    DropdownItemComponent,
    ListTileComponent,
    CircularProgressComponent,
    LinearProgressComponent,
    ChipComponent,
    COMPONENT_TYPES,
    # A2UI component node
    A2UIComponent,
    DataEntry,
    # Server-to-client message content
    BeginRenderingContent,
    CreateSurfaceContent,
    SurfaceUpdateContent,
    DeleteComponentsContent,
    DataModelUpdateContent,
    DeleteSurfaceContent,
    # Server-to-client messages
    BeginRenderingMessage,
    CreateSurfaceMessage,
    SurfaceUpdateMessage,
    DeleteComponentsMessage,
    DataModelUpdateMessage,
    DeleteSurfaceMessage,
    A2UIServerMessage,
    # Client-to-server message content
    UserActionContent,
    ErrorContent,
    # Client-to-server messages
    UserActionMessage,
    ClientErrorMessage,
    A2UIClientMessage,
    # AG-UI transport
    A2UICustomEventValue,
)

# Component builder
from .components import (
    ComponentBuilder,
    DataModelBuilder,
)

# Surface manager
from .surfaces import (
    SurfaceState,
    SurfaceManager,
    get_surface_manager,
)

# Emitter (AG-UI integration)
from .emitter import (
    A2UIEmitter,
    emit_a2ui,
    get_emitter,
)

# High-level integration helpers
from .integration import (
    show_form,
    show_message,
    show_progress,
    show_error,
    show_confirmation,
    delete_surface,
    update_data,
    get_last_action,
    is_a2ui_active,
)

__all__ = [
    # Value types
    "BoundValue",
    "TextValue",
    "NumberValue",
    "BoolValue",
    "ChildrenRef",
    "ContextEntry",
    "ComponentAction",
    # Enums
    "UsageHint",
    "MainAxisAlignment",
    "CrossAxisAlignment",
    # Standard Catalog Components - Content
    "TextComponent",
    "IconComponent",
    "ImageComponent",
    "VideoComponent",
    "AudioPlayerComponent",
    # Standard Catalog Components - Layout
    "ColumnComponent",
    "RowComponent",
    "ListComponent",
    "CardComponent",
    "TabItem",
    "TabsComponent",
    "DividerComponent",
    "ModalComponent",
    # Standard Catalog Components - Input
    "ButtonComponent",
    "CheckBoxComponent",
    "TextFieldComponent",
    "DateTimeInputComponent",
    "MultipleChoiceOption",
    "MultipleChoiceComponent",
    "SliderComponent",
    # Extension Components
    "IconButtonComponent",
    "SwitchComponent",
    "ExpandedComponent",
    "PaddingComponent",
    "SizedBoxComponent",
    "ContainerComponent",
    "DropdownComponent",
    "DropdownItemComponent",
    "ListTileComponent",
    "CircularProgressComponent",
    "LinearProgressComponent",
    "ChipComponent",
    "COMPONENT_TYPES",
    # A2UI component node
    "A2UIComponent",
    "DataEntry",
    # Message content classes
    "BeginRenderingContent",
    "CreateSurfaceContent",
    "SurfaceUpdateContent",
    "DeleteComponentsContent",
    "DataModelUpdateContent",
    "DeleteSurfaceContent",
    # Server messages
    "BeginRenderingMessage",
    "CreateSurfaceMessage",
    "SurfaceUpdateMessage",
    "DeleteComponentsMessage",
    "DataModelUpdateMessage",
    "DeleteSurfaceMessage",
    "A2UIServerMessage",
    # Client messages
    "UserActionContent",
    "ErrorContent",
    "UserActionMessage",
    "ClientErrorMessage",
    "A2UIClientMessage",
    # AG-UI integration
    "A2UICustomEventValue",
    # Builders
    "ComponentBuilder",
    "DataModelBuilder",
    # Surface management
    "SurfaceState",
    "SurfaceManager",
    "get_surface_manager",
    # Emitter
    "A2UIEmitter",
    "emit_a2ui",
    "get_emitter",
    # Integration helpers
    "show_form",
    "show_message",
    "show_progress",
    "show_error",
    "show_confirmation",
    "delete_surface",
    "update_data",
    "get_last_action",
    "is_a2ui_active",
]
