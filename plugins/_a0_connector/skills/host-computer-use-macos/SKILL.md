---
name: host-computer-use-macos
description: Backend-specific macOS guidance for `computer_use_remote`. Load after `status` or `start_session` reports backend_family/backend_id `macos` or Accessibility-tree features. Covers AX structural targeting, macOS window actions, and screenshot verification.
---

# Host Computer Use - macOS

Use this after `host-computer-use` when the connected A0 CLI reports the macOS computer-use backend.

Do not use this skill for Linux, Windows, Xpra, Docker, or browser-only tasks. If the backend is not macOS or does not advertise Accessibility-tree support, skip AX actions and follow the generic host computer-use rules.

## macOS AX Targeting

macOS backends can advertise structural Accessibility features:

- `accessibility-tree-snapshot`
- `accessibility-structural-targeting`
- `accessibility-element-click`

When these features are present, prefer structural targeting over pixel clicks for named controls such as buttons, menu items, text fields, sheets, alerts, toolbar items, and sidebar rows.

If the backend also advertises `native-window-list`, `window-state`, `element-index-targeting`, or `background-dispatch`, prefer the generic background loop from `host-computer-use`: `list_windows` -> `get_window_state` -> `element_action`. If those features are absent, use the AX snapshot/action flow below.

Use `ax_snapshot` to inspect the frontmost app's bounded Accessibility tree:

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

The snapshot returns element paths, roles, labels, frames, enabled/focused state, actions, and child nodes. Use it to choose an element, not as final visual proof.

Use `ax_action` for a structural action:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "ax_action",
    "target": {
      "role": "AXButton",
      "title": "OK"
    },
    "operation": "press"
  }
}
```

Supported operations are:

- `press`: activate a button, menu item, checkbox, or similar control
- `focus`: focus a text field or focusable element
- `set_value`: set a value; pass `value` or `text`

Targeting options:

- Prefer a semantic `target` when the control has a stable title, description, value, identifier, role, or subrole.
- Use a `path` returned by the latest `ax_snapshot` only while the UI is unchanged.
- If an action reports ambiguity, take a fresh snapshot and narrow the target with role plus title/description/identifier.
- If an action reports a missing target, take a fresh snapshot before trying coordinates.

AX actions are attempts, not proof. They attach a fresh screenshot after state-changing actions; inspect that image before saying the requested outcome happened.

Do not assume macOS work happened in the background unless the tool result explicitly says `actual_dispatch=background`. If the result says `background_unavailable`, use foreground dispatch only when foreground control is acceptable.

## macOS Window Actions

For active-app window tasks, macOS shortcuts are usually:

- `Command+H`: hide the active app
- `Command+M`: minimize the active window

Treat these as attempts. After any hide or minimize shortcut, inspect the fresh screenshot. If the target window is still visible, say the attempt failed or switch strategy; do not type follow-up text into the focused app unless the screenshot clearly shows the intended target.

When a visible close/minimize/full-screen button or menu item is accessible in the AX tree, prefer `ax_snapshot` plus `ax_action` over a small coordinate click.

## Permissions

macOS Screen Recording affects screenshots. Accessibility/Input Monitoring affect structural targeting and input. If `computer_use_remote` returns `COMPUTER_USE_REARM_REQUIRED`, `COMPUTER_USE_APPROVAL_REQUIRED`, or `status=rearm required`, stop immediately and ask the user to run `/computer-use on` in the A0 Launcher chat when using Launcher Host access, or in A0 CLI otherwise, and approve the macOS prompt if shown.

Do not bypass a permission failure with server screenshots, Docker commands, `linux-desktop`, or browser fallbacks.
