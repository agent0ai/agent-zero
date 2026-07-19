---
name: browser-automation
description: Use for complex Agent Zero browser automation, including multi-tab browsing, screenshots, forms, uploads, raw pointer/keyboard actions, host-vs-container browser mode, and visual verification workflows.
---

# Browser Tool

Use the `browser` tool for rendered pages, forms, logins, downloads, JavaScript-heavy sites, screenshots, and visual inspection. Prefer `search_engine` or `document_query` for plain text research.

## Core Workflow

1. `open` creates a browser tab and returns a `browser_id`.
2. `content` returns readable markdown plus typed refs like `[link 3]`, `[button 6]`, `[input text 8]`.
3. Interact with refs using `click`, `type`, `submit`, `scroll`, etc.
4. Use `navigate` on an existing `browser_id` for serial browsing.
5. Keep only a small working tab set; close pages when finished.

## Modes

The same tool may run in Docker container mode or A0 CLI host-browser mode, depending on project/plugin settings.

- Container mode: browser and upload paths resolve inside the Agent Zero container.
- Host mode: browser and upload paths resolve on the connected A0 CLI host machine.

In host mode, page content and screenshots may be blocked by host-content policy when remote models are active.

## Screenshots And Vision

Screenshots are explicit only; the browser does not automatically load images into model context.

1. Call `browser` with `action: "screenshot"`.
2. Call `vision_load` with the returned path.
3. Reason from the latest loaded screenshot.

Screenshot args include `quality`, `full_page`, and optional `path`. PNG is used when `path` ends with `.png`; otherwise JPEG is used.

## Forms And Files

- `select_option` works for native selects and detectable ARIA listbox/combobox controls.
- `set_checked` works for checkbox, radio, switch, and toggle-like refs.
- `upload_file` works for file input refs or associated labels; verify the file exists in the active browser environment.
- For fragile forms, load skill `browser-form-workflows`.

## Pointer And Keyboard

- `hover`, `double_click`, `right_click`, and `drag` accept refs or viewport coordinates.
- Coordinates are Chromium viewport CSS pixels and match screenshots.
- `key_chord` presses keys in order and releases in reverse.
- `clipboard` actions are copy, cut, or paste.
- `set_viewport` resizes the page viewport.

## Tabs And Popups

- Popups and target-blank tabs are auto-registered.
- `list` shows open tabs; pass `include_content: true` sparingly.
- `set_active` deliberately changes focus.
- Operations on a non-active tab do not steal focus unless browser rules require it.

## Browser Action Multi

`multi` is only a browser action, never a top-level tool. Use:

```json
{
  "tool_name": "browser",
  "tool_args": {
    "action": "multi",
    "calls": [
      {"action": "content", "browser_id": 1},
      {"action": "screenshot", "browser_id": 2}
    ]
  }
}
```

Use browser action `multi` for parallel reads across tabs. Avoid mutating the same tab twice in one batch unless serial order is intended.
