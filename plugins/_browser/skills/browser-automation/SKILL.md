---
name: browser-automation
description: "Control web pages: tabs, clicks, forms, downloads, screenshots; host or Docker browser."
triggers:
  - "browser automation"
  - "web automation"
  - "open website"
  - "open URL"
  - "navigate browser"
  - "interact with web page"
  - "JavaScript page"
  - "browser screenshot"
  - "screenshot webpage"
  - "visual verification"
  - "multi-tab browsing"
  - "download file from website"
  - "upload file in browser"
  - "host browser"
  - "local browser"
  - "my browser"
---

# Browser Tool

Use this skill after the compact `browser` tool prompt points you here. It is the progressive-disclosure workflow guide for rendered pages, multi-step browser work, logins, downloads, JavaScript-heavy sites, screenshots, host/container browser mode, and visual inspection. Prefer `search_engine` or `document_query` for plain text research.

For fragile forms, load `browser-form-workflows` with `skills_tool:load` before acting when selects, checkboxes, radios, file uploads, contenteditable fields, validation, or final submission state are central to the task.

## Core Workflow

1. `open` creates a browser tab and returns a `browser_id`.
2. `content` returns readable markdown plus typed refs like `[link 3]`, `[button 6]`, `[input text 8]`.
3. Interact with refs using `click`, `type`, `submit`, `scroll`, etc.; iframe/shadow targets may return frame-chain metadata in action results.
4. Use `navigate` on an existing `browser_id` for serial browsing.
5. Keep only a small working tab set; close pages when finished.
6. If the user asks for an existing tab, page title, or already-open URL, call `list` first, match by `title` or `currentUrl`, then use `set_active` or `navigate` on that `browser_id` instead of opening a new tab.

## Modes

When the user asks for "my browser", "host browser", "local browser", a local Chromium browser, or opening a URL in their host browser, use this `browser` tool. Do not substitute `computer_use_remote`, `code_execution_remote`, `xdg-open`, `sensible-browser`, or Python `webbrowser.open`. If setup fails and mentions remote debugging, tell the user to open the browser inspect page, such as `chrome://inspect/#remote-debugging` or `opera://inspect/#remote-debugging`, enable "Allow remote debugging for this browser instance", run `/browser host on`, and retry.

The same tool may run in Docker container mode or A0 CLI host-browser mode, depending on project/plugin settings.

- Container mode: browser and upload paths resolve inside the Agent Zero container.
- Host mode: browser and upload paths resolve on the connected A0 CLI host machine.

In host mode, page content and screenshots may be blocked by host-content policy when remote models are active.

## Screenshots And Vision

Screenshots are explicit only; the browser does not automatically load images into model context.

1. Call `browser` with `action: "screenshot"`.
2. Call `vision_load` with the returned `vision_load.tool_args.paths` value.
3. Reason from the latest loaded screenshot.

Screenshot args include `quality`, `full_page`, and optional `path`. Without `path`, the screenshot is saved as a chat-scoped artifact and returned through `vision_load.tool_args.paths`; with `path`, PNG is used when `path` ends with `.png`, otherwise JPEG is used.

## Forms And Files

- `select_option` works for native selects and detectable ARIA listbox/combobox controls.
- `set_checked` works for checkbox, radio, switch, and toggle-like refs.
- `upload_file` works for file input refs or associated labels; verify the file exists in the active browser environment.
- For fragile forms, call `skills_tool` with `action: "load"` and `skill_name: "browser-form-workflows"`, then follow that form-specific workflow before filling or submitting.

## Pointer And Keyboard

- Prefer refs/selectors and DOM/CDP actions over viewport coordinates.
- `hover`, `double_click`, `right_click`, and `drag` accept refs or viewport coordinates when no reliable ref exists.
- Coordinates are Chromium viewport CSS pixels and match screenshots; treat them as visual fallback, not the default interaction path.
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
