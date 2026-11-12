---
name: host-computer-use-linux
description: Host Linux guidance for `computer_use_remote` when results report Linux, Wayland, X11, or AT-SPI features. Covers verified focus, AT-SPI targeting, XWayland app limitations, remote desktop viewers, and screenshot verification; excludes the internal Docker/Xpra desktop.
---

# Host Computer Use - Linux

Use this after `host-computer-use` when the connected A0 CLI or Launcher gateway reports a Linux computer-use backend. Start with the needed `list_windows` or `capture` observation; the shared tool starts a missing chat session automatically. Use `status` only when you need to inspect authorization or capabilities.

Do not use this skill for macOS, Windows, Xpra, Docker, browser-only tasks, or the internal Agent Zero Desktop. If the backend is not Linux or does not advertise AT-SPI support, skip Linux structural actions and follow the generic host computer-use rules.

For an X11/XWayland app or remote desktop viewer with an incomplete accessibility tree, read [X11 and viewer workflows](references/x11-viewers.md). Use its host-shell techniques only while Computer Use is enabled and authorized and host code execution is independently enabled. A backend limitation is not a permission denial.

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
    "window_id": "<window_id from list_windows>",
    "max_depth": 4,
    "max_nodes": 200
  }
}
```

Pass `window_id` whenever one is known so unrelated applications cannot consume the node budget. The snapshot returns paths, roles, names/titles, descriptions, frames, states, actions, text previews, values, and child nodes. Use it to choose a target, not as final visual proof.

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

- `press`: activate a button, menu item, tab, checkbox, or similar action-bearing node; never use it on an application/frame/window
- `focus`: focus a focusable node before typing or keyboard input
- `set_value`: set text/value on editable nodes; pass `value` or `text`

Targeting options:

- Prefer a semantic `target` when a node has a stable role plus title/name/description/text/state/action.
- Use a `path` returned by the latest `ax_snapshot` only while the UI is unchanged.
- If an action reports ambiguity, take a fresh snapshot and narrow the target with role plus title/name/description.
- If an action reports a missing target, take a fresh snapshot before trying coordinates.

## Focus and Observation

Use screenshots for proof after every state-changing action. AT-SPI actions and keyboard events are attempts, not proof, and Wayland focus can reject or redirect input when the active window changes.

True background dispatch on Linux is compositor, toolkit, and app dependent. Do not claim a Linux action was background-safe unless the tool result explicitly says `actual_dispatch=background`.

To bring a Linux window forward, target its frame/window element from `get_window_state` with `element_action`, operation `focus`, and `dispatch: "foreground"` or `"auto"`. Continue only when the result says `focus_verified=true`; an accepted AT-SPI call without active/focused state is not activation proof.

Linux text injection is target-guarded. Pass the same verified active `window_id` to `type`. If the tool reports `COMPUTER_USE_WINDOW_REQUIRED` or `COMPUTER_USE_TARGET_NOT_FOCUSED`, do not type globally and do not substitute another application target.

On GNOME/Wayland, useful shortcuts include:

- `Super+H`: hide the active window
- `Alt+Tab`: switch applications
- `Ctrl+L`: focus a browser address bar when the browser is already focused
- `Ctrl+T`: open a new browser tab when the browser is already focused

Treat every shortcut as an attempt. Inspect the fresh screenshot before saying it worked. If text lands in the wrong app, stop and reassess from `capture` or `ax_snapshot`; do not continue typing from assumed focus.

A remote desktop viewer exposes the local viewer's controls, not necessarily the remote application's accessibility tree. Keep local window identity, viewer scaling, and the remote desktop separate. Use remote pixels only after inspecting the rendered viewer. Recalculate coordinates after resizing or changing scaling; local tool coordinates remain normalized to the host screen.

When a popup is already open, do not refocus its parent window; this may dismiss the popup. Inspect a fresh frame and select the actual control, such as a scaling radio button, rather than assuming a click on nearby text selected it.

Slow VNC viewers may drop fast typing and clicks. Wait for the resulting frame, verify field focus and masked character count, and use slower input if needed. Click confirmation fields explicitly when Tab does not move focus. A partial redraw or unchanged screenshot warrants one fresh capture before another action, not repeated credential submission.

Some apps expose shallow AT-SPI trees unless their own accessibility support is enabled. If the AT-SPI tree is too shallow for a task, fall back in this order: app-native/browser tooling, reliable keyboard paths, then normalized coordinate clicks from a fresh screenshot.

## Permissions

If `computer_use_remote` returns `COMPUTER_USE_REARM_REQUIRED`, `COMPUTER_USE_APPROVAL_REQUIRED`, or `status=rearm required`, stop immediately and ask the user to re-arm or fix the Linux desktop session. If only `COMPUTER_USE_AX_UNAVAILABLE` is returned, stop structural actions and check the reported cause: use an already-authorized capture/input capability only for an accessibility availability limitation, never to evade an access denial.

Do not bypass a permission or host-visibility failure with server screenshots, Docker commands, the built-in Linux Desktop/Xpra skill, or `code_execution_tool`.
