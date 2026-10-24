# Connector composer controls

Agent Zero advertises `composer_controls` when the generic composer-control API is available. Compatible connectors render controls supplied by enabled plugins beside the provider/model bar. No optional plugin names or domain rules belong in the connector.

## Plugin extension

Add an `Extension` under `extensions/python/connector_controls/`. Core invokes it with the active chat's `agent`, `action`, request `input`, a mutable `controls` list, and a mutable `result` dictionary. Existing project/profile activation and extension precedence apply. Do not register controls globally or patch framework methods.

For `action == "list"`, append choice descriptors:

```json
{
  "id": "my_plugin.mode",
  "type": "choice",
  "label": "Mode: Auto",
  "title": "Processing mode",
  "value": "",
  "revision": "opaque-current-revision",
  "options": [
    {"value": "", "label": "Use default"},
    {"value": "fast", "label": "Fast"}
  ],
  "custom": true,
  "description": "Optional explanatory text"
}
```

IDs must be unique across the active chat's controls. Labels, values, default/reset semantics, and optional descriptive text belong to the plugin. Values are strings, including the empty string when appropriate. Connectors ignore unsupported types. `custom: true` enables a text field limited to 64 characters; omit it or use `false` for choices only. The connector renders text, never HTML or executable plugin UI.

For `action == "set"`, ignore requests for other control IDs. Validate the value and opaque revision against current plugin state, persist through the existing domain owner, and assign a response to `result["response"]`. Return `{"ok": true}` on success or a `helpers.api.Response` with an appropriate status: 400 for invalid values, 409 for stale revisions. Core returns 404 if no enabled extension handles the control. Reuse the plugin's existing validation and persistence rather than implementing a second path.

## HTTP contract

`POST /api/plugins/_a0_connector/v1/composer_controls` requires the existing authenticated session and CSRF token. Listing requires:

```json
{"action": "list", "context_id": "chat-id"}
```

It returns `{"ok": true, "controls": [...]}`; no controls is a normal empty list. Setting requires:

```json
{
  "action": "set",
  "context_id": "chat-id",
  "control_id": "my_plugin.mode",
  "value": "fast",
  "custom": false,
  "revision": "opaque-current-revision"
}
```

The connector forwards the revision without interpreting it, refreshes descriptors after success, and must discard work after host/chat changes. Server-side revision validation prevents a menu opened against old plugin state from changing a new target. Escape or outside clicks cancel locally; validation failures retain custom input for correction. Plugin disablement/removal hides its controls on refresh. Older Core builds without the capability receive no optional requests.
