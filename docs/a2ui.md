# A2UI Protocol Integration

Agent Zero supports the [A2UI Protocol](https://a2ui.org) (Agent-to-UI) for generating rich, interactive user interfaces directly from agent responses.

## Overview

A2UI (formerly Google A2UI) is a protocol specification that allows AI agents to generate declarative UI components that can be rendered by any compatible client (Flutter, Web, React Native, etc.).

Instead of just returning text, agents can now send structured UI components:

```
Agent: "Here's the data you requested"
       [Card with Table of results]
       [Button: "Export to CSV"] [Button: "Filter Results"]
```

## The A2UI Tool

The A2UI tool (`a2ui`) allows the agent to generate UIs through simple method calls:

### Available Methods

| Method | Description |
|--------|-------------|
| `show` | Display a UI surface with components |
| `update` | Update components on an existing surface |
| `data` | Update the data model (for bound values) |
| `delete` | Remove a surface |
| `form` | Show a form and wait for user input |
| `message` | Display a simple message |
| `progress` | Show a progress indicator |
| `confirm` | Show a confirmation dialog |

### Example Usage (in Agent)

```
# Show a simple message
~~~json
{"a2ui": {"method": "message", "text": "Processing your request..."}}
~~~

# Show a form
~~~json
{"a2ui": {
  "method": "form",
  "fields": [
    {"type": "text", "name": "email", "label": "Email Address"},
    {"type": "select", "name": "plan", "label": "Plan", "options": ["Basic", "Pro", "Enterprise"]}
  ]
}}
~~~

# Display custom UI
~~~json
{"a2ui": {
  "method": "show",
  "surface_id": "@results",
  "components": [
    {"type": "card", "title": "Results", "children": [
      {"type": "text", "value": "Found 42 items"},
      {"type": "button", "label": "Export", "action": "export_data"}
    ]}
  ]
}}
~~~
```

## Components

A2UI supports a rich set of components from the [Standard Catalog](https://a2ui.org/specification/v0.8-a2ui/):

### Layout Components
- `Column` - Vertical layout
- `Row` - Horizontal layout
- `Card` - Material design card
- `Divider` - Visual separator

### Content Components
- `Text` - Text display
- `Icon` - Material icons
- `Image` - Image display

### Input Components
- `Button` - Action buttons
- `TextField` - Text input
- `TextArea` - Multi-line input
- `CheckBox` - Boolean toggle
- `Switch` - On/off toggle
- `DateTimeInput` - Date/time picker
- `Slider` - Range input
- `Dropdown` - Selection list

### Data Binding

Components can bind to a data model using JSON Pointer paths:

```json
{
  "type": "text",
  "value": {"$ref": "/user/name"}
}
```

When the data model is updated via `a2ui:data`, bound components automatically refresh.

## Surfaces

A2UI uses "surfaces" to organize UI areas:

- `@ui` - Main UI surface (default)
- `@modal` - Modal dialog surface
- `@toast` - Toast/notification surface
- Custom surface IDs for specific areas

## User Actions

When users interact with components (button clicks, form submissions), the client sends a `userAction` message back to the agent:

```json
{
  "userAction": {
    "name": "export_data",
    "surfaceId": "@results",
    "sourceComponentId": "btn-export",
    "timestamp": "2025-01-01T12:00:00Z",
    "context": {"format": "csv"}
  }
}
```

The agent can handle these through the `a2ui_action` extension hook.

## Client Support

A2UI is transport-agnostic. In Agent Zero, A2UI messages are transmitted via the AG-UI protocol as `CustomEvent` with:

```json
{
  "type": "CUSTOM",
  "name": "a2ui",
  "value": {
    "mimeType": "application/json+a2ui",
    "data": { /* A2UI message */ }
  }
}
```

Compatible clients can parse these events and render the UI.

## Configuration

A2UI is enabled by default when AG-UI is enabled. No additional configuration required.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Agent Zero                          │
├─────────────────────────────────────────────────┤
│                                                  │
│  Agent calls:                                    │
│  a2ui:show components=[...]                     │
│                    │                            │
│                    ▼                            │
│  ┌────────────────────────────────┐             │
│  │    A2UI Tool                   │             │
│  │    python/tools/a2ui.py        │             │
│  └────────────────────────────────┘             │
│                    │                            │
│                    ▼                            │
│  ┌────────────────────────────────┐             │
│  │    A2UI Emitter                │             │
│  │    Creates A2UI messages       │             │
│  └────────────────────────────────┘             │
│                    │                            │
│                    ▼                            │
│  ┌────────────────────────────────┐             │
│  │    AG-UI Queue                 │             │
│  │    Wraps as CustomEvent        │             │
│  └────────────────────────────────┘             │
│                    │                            │
└────────────────────┼────────────────────────────┘
                     │
                     ▼ SSE
┌─────────────────────────────────────────────────┐
│              Client                              │
│  (Flutter, Web, React, etc.)                    │
│                                                  │
│  Parses CustomEvent, renders UI                 │
│  Sends userAction back to /agui/a2ui/action    │
└─────────────────────────────────────────────────┘
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agui` | POST | Main AG-UI endpoint (streams A2UI events) |
| `/agui/a2ui/action` | POST | Receive user action callbacks |
| `/agui/a2ui/info` | GET | A2UI capability information |

## See Also

- [AG-UI Protocol Integration](agui.md) - SSE streaming protocol
- [A2UI Specification](https://a2ui.org/specification/v0.8-a2ui/)
- [A2UI Standard Catalog](https://a2ui.dev/specification/0.8/standard_catalog.json)
