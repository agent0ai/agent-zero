# Plugin WebUI

Sources: `/a0/webui/AGENTS.md`, `/a0/webui/js/AGENTS.md`, `/a0/webui/components/AGENTS.md`, `/a0/plugins/AGENTS.md`. Match existing component geometry and use framework UI surfaces.

## Mandatory Frontend Patterns

### 1. The "Store Gate" Template
To avoid race conditions and undefined errors, every component must use this wrapper:
```html
<div x-data>
  <template x-if="$store.myPluginStore">
    <div x-init="$store.myPluginStore.onOpen()" x-destroy="$store.myPluginStore.cleanup()">
       <!-- Content goes here -->
    </div>
  </template>
</div>
```

### 2. Separate Store Module
Place store logic in a separate .js file. Do NOT use alpine:init listeners inside HTML.
```javascript
// webui/my-store.js
import { createStore } from "/js/AlpineStore.js";
export const store = createStore("myPluginStore", {
    status: 'idle',
    init() {},
    onOpen() {},
    cleanup() {}
});
```
Import it in the HTML <head>:
```html
<head>
  <script type="module" src="/plugins/<plugin_name>/webui/my-store.js"></script>
</head>
```

### 3. User Feedback: A0 Notifications Only
Do **not** show errors or success via inline boxes (e.g. a red `<div>` bound to `store.error`). Use the project notification system so toasts and history stay consistent.

- **Errors**: `toastFrontendError(message, "My Plugin")` (or `$store.notificationStore.frontendError(...)`)
- **Success**: `toastFrontendSuccess(message, "My Plugin")`
- **Warnings/Info**: `toastFrontendWarning`, `toastFrontendInfo` from `/components/notifications/notification-store.js`

Import and call from your store; do not render a dedicated error/success block in the template. See [Notifications](/a0/docs/developer/notifications.md) for the full API.

---

## Plugin Settings

If your plugin needs user-configurable settings, add `webui/config.html`. The system detects it automatically and shows a Settings button in the relevant tabs (per `settings_sections` in `plugin.yaml`).

### Settings modal contract

The modal provides Project + Agent profile context selectors. The plugin settings wrapper instantiates a local modal context from `$store.pluginSettingsPrototype`. Inside `config.html`, bind plugin fields to `config.*` and use `context.*` for modal-level state and actions:

```html
<html>
<head>
  <title>My Plugin Settings</title>
  <script type="module">
    import { store } from "/components/plugins/plugin-settings-store.js";
  </script>
</head>
<body>
  <div x-data>
    <input x-model="config.my_key" />
    <input type="checkbox" x-model="config.feature_enabled" />
  </div>
</body>
</html>
```

The modal's Save button persists `config` to `config.json` in the correct scope (project/agent/global).

### Sidebar Button (sidebar entry point)
- Extension point: `sidebar-quick-actions-main-start`
- Class: `class="config-button"`
- Placement: `x-move-after=".config-button#dashboard"`
- Action: `@click="openModal('/plugins/<plugin_name>/webui/my-modal.html')"`

---


## Verification

Check the browser console, store loading, settings persistence in the intended scope, and the rendered feature in the target instance. Verify desktop and narrow layouts for UI changes. Close only test surfaces you opened.
