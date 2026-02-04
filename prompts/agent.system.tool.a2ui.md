### a2ui:
This tool generates rich, interactive user interfaces using the A2UI protocol.
A2UI enables agents to create native-feeling UIs that render on Flutter, Web, and other clients.

!!! A2UI protocol: https://a2ui.org/specification/v0.8-a2ui/
!!! Only works when connected via AG-UI streaming endpoint

#### Methods:

##### 1. show - Display a UI with components
Arguments:
* "surface_id" (Optional, string): Surface identifier (default: "@ui")
* "components" (string): JSON array of A2UI component definitions
* "root" (string): ID of the root component

##### 2. form - Generate a form with fields
Arguments:
* "surface_id" (Optional, string): Surface identifier (default: "@form")
* "title" (string): Form title
* "fields" (string): JSON array of field definitions [{name, label, type, path, hint}]
* "submit_action" (string): Action name for form submission
* "submit_label" (Optional, string): Submit button label (default: "Submit")

Field types: text, password, checkbox, switch, date, datetime

##### 3. message - Display a simple message
Arguments:
* "text" (string): Message text
* "hint" (Optional, string): Style hint (h1, h2, body, caption)
* "surface_id" (Optional, string): Surface identifier (default: "@message")

##### 4. progress - Show a progress indicator
Arguments:
* "message" (string): Progress message
* "progress_path" (Optional, string): Data path for progress value (omit for indeterminate)
* "surface_id" (Optional, string): Surface identifier (default: "@progress")

##### 5. confirm - Show a confirmation dialog
Arguments:
* "title" (string): Dialog title
* "message" (string): Confirmation message
* "confirm_action" (string): Action name for confirm button
* "cancel_action" (string): Action name for cancel button
* "surface_id" (Optional, string): Surface identifier (default: "@confirm")

##### 6. data - Update the data model for reactive bindings
Arguments:
* "surface_id" (string): Surface identifier
* "data" (string): JSON object with data to set
* "path" (Optional, string): Base path for the update

##### 7. delete - Remove a surface
Arguments:
* "surface_id" (string): Surface identifier to delete

#### A2UI Component Structure:
Components use an adjacency list model with ID references:
```json
{
  "id": "unique-id",
  "component": {
    "Text": {"text": {"literalString": "Hello"}, "usageHint": "h1"}
  }
}
```

Standard components: Text, Button, Card, Column, Row, TextField, DateTimeInput, CheckBox, Switch, Icon, Image

#### Usage examples:

##### 1: Simple message
```json
{
    "thoughts": ["I need to show a welcome message to the user"],
    "tool_name": "a2ui:message",
    "tool_args": {
        "text": "Welcome! How can I help you today?",
        "hint": "h1"
    }
}
```

##### 2: Contact form
```json
{
    "thoughts": ["The user wants to fill out their contact information"],
    "tool_name": "a2ui:form",
    "tool_args": {
        "title": "Contact Information",
        "fields": "[{\"name\":\"name\",\"label\":\"Full Name\",\"type\":\"text\"},{\"name\":\"email\",\"label\":\"Email\",\"type\":\"text\"},{\"name\":\"subscribe\",\"label\":\"Subscribe to newsletter\",\"type\":\"checkbox\"}]",
        "submit_action": "submit_contact"
    }
}
```

##### 3: Booking UI with custom components
```json
{
    "thoughts": ["Creating a booking interface with date picker and confirmation"],
    "tool_name": "a2ui:show",
    "tool_args": {
        "surface_id": "booking",
        "root": "root",
        "components": "[{\"id\":\"title\",\"component\":{\"Text\":{\"text\":{\"literalString\":\"Book Your Table\"},\"usageHint\":\"h1\"}}},{\"id\":\"date\",\"component\":{\"DateTimeInput\":{\"value\":{\"path\":\"/booking/date\"},\"enableDate\":true}}},{\"id\":\"submit-text\",\"component\":{\"Text\":{\"text\":{\"literalString\":\"Confirm\"}}}},{\"id\":\"submit\",\"component\":{\"Button\":{\"child\":\"submit-text\",\"action\":{\"name\":\"confirm_booking\"}}}},{\"id\":\"col\",\"component\":{\"Column\":{\"children\":{\"explicitList\":[\"title\",\"date\",\"submit\"]}}}},{\"id\":\"root\",\"component\":{\"Card\":{\"child\":\"col\"}}}]"
    }
}
```

##### 4: Confirmation dialog
```json
{
    "thoughts": ["Asking user to confirm deletion"],
    "tool_name": "a2ui:confirm",
    "tool_args": {
        "title": "Delete Item?",
        "message": "This action cannot be undone. Are you sure?",
        "confirm_action": "delete_confirmed",
        "cancel_action": "delete_cancelled"
    }
}
```

##### 5: Progress indicator
```json
{
    "thoughts": ["Showing loading state while processing"],
    "tool_name": "a2ui:progress",
    "tool_args": {
        "message": "Processing your request..."
    }
}
```
