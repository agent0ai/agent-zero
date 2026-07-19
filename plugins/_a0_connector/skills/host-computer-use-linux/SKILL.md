---
name: host-computer-use-linux
description: Backend-specific Linux guidance for `computer_use_remote`. Load after `status` or `start_session` reports backend_family `linux`, backend_id `wayland`, or AT-SPI features. Covers AT-SPI structural targeting, Wayland portal caveats, and screenshot verification.
---

# Host Computer Use - Linux

Use this after `host-computer-use` when the connected A0 CLI reports the Linux/Wayland computer-use backend.

Do not use this skill for macOS, Windows, Xpra, Docker, browser-only tasks, or the internal Agent Zero Desktop. If the backend is not Linux or does not advertise AT-SPI support, skip Linux structural actions and follow the generic host computer-use rules.

## Linux AT-SPI Targeting

Linux backends can advertise structural AT-SPI features:

- `atspi-tree-snapshot`
- `atspi-structural-targeting`
- `atspi-element-action`
- `atspi-set-value`

When these features are present, prefer structural targeting over pixel clicks for named buttons, menu items, text fields, dialogs, toolbar items, tab strips, and application windows.

If the backend also advertises `native-window-list`, `window-state`, `element-index-targeting`, or `background-dispatch`, prefer the generic background loop from `host-computer-use`: `list_windows` -> `get_window_state` -> `element_action`. If those features are absent, use the AT-SPI snapshot/action flow below.

Use `ax_snapshot` to inspect the Linux AT-SPI tree:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "ax_snapshot",
    "max_depth": 4,
    "max_nodes": 200
  }
}
```

The snapshot returns paths, roles, names/titles, descriptions, frames, states, actions, text previews, values, and child nodes. Use it to choose a target, not as final visual proof.

Use `ax_action` for structural actions:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "ax_action",
    "target": {
      "role": "push button",
      "title": "OK"
    },
    "operation": "press"
  }
}
```

Supported operations are:

- `press`: activate a button, menu item, tab, checkbox, or similar action-bearing node
- `focus`: focus a focusable node before typing or keyboard input
- `set_value`: set text/value on editable nodes; pass `value` or `text`

Targeting options:

- Prefer a semantic `target` when a node has a stable role plus title/name/description/text/state/action.
- Use a `path` returned by the latest `ax_snapshot` only while the UI is unchanged.
- If an action reports ambiguity, take a fresh snapshot and narrow the target with role plus title/name/description.
- If an action reports a missing target, take a fresh snapshot before trying coordinates.

## Wayland Notes

Use screenshots for proof after every state-changing action. AT-SPI actions and keyboard events are attempts, not proof, and Wayland focus can reject or redirect input when the active window changes.

True background dispatch on Linux is compositor, toolkit, and app dependent. Do not claim a Linux action was background-safe unless the tool result explicitly says `actual_dispatch=background`.

On GNOME/Wayland, useful shortcuts include:

- `Super+H`: hide the active window
- `Alt+Tab`: switch applications
- `Ctrl+L`: focus a browser address bar when the browser is already focused
- `Ctrl+T`: open a new browser tab when the browser is already focused

Treat every shortcut as an attempt. Inspect the fresh screenshot before saying it worked. If text lands in the wrong app, stop and reassess from `capture` or `ax_snapshot`; do not continue typing from assumed focus.

Some apps expose shallow AT-SPI trees unless their own accessibility support is enabled. If the AT-SPI tree is too shallow for a task, fall back in this order: app-native/browser tooling, reliable keyboard paths, then normalized coordinate clicks from a fresh screenshot.

## Permissions

If `computer_use_remote` returns `COMPUTER_USE_AX_UNAVAILABLE`, `COMPUTER_USE_REARM_REQUIRED`, `COMPUTER_USE_APPROVAL_REQUIRED`, or `status=rearm required`, stop immediately and ask the user to re-arm or fix the Linux desktop accessibility/session state.

Do not bypass a permission or host-visibility failure with server screenshots, Docker commands, the built-in Linux Desktop/Xpra skill, or `code_execution_tool`.
