---
name: host-computer-use-windows
description: Backend-specific Windows guidance for `computer_use_remote`. Load after `status` or `start_session` reports backend_family/backend_id `windows` or Windows UI Automation features. Covers UIA structural targeting, Windows session caveats, and screenshot verification.
---

# Host Computer Use - Windows

Use this after `host-computer-use` when the connected A0 CLI reports the Windows computer-use backend.

Do not use this skill for Linux, macOS, Xpra, Docker, or browser-only tasks. If the backend is not Windows or does not advertise UI Automation support, skip UIA actions and follow the generic host computer-use rules.

## Windows UIA Targeting

Windows backends can advertise structural UI Automation features:

- `uia-tree-snapshot`
- `uia-structural-targeting`
- `uia-element-action`
- `uia-window-management`
- `native-window-list`
- `window-state`
- `element-index-targeting`
- `background-dispatch`
- `foreground-dispatch-fallback`

When these features are present, prefer background structural targeting over pixel clicks for named controls such as buttons, menu items, text fields, dialogs, toolbar items, browser address bars, composer fields, and list rows.

Preferred loop:

1. Use `list_windows` to find the target native window.
2. Use `get_window_state` with the target `pid` and/or `window_id`.
3. Use `element_action` with the returned `element_index` and `dispatch: "background"`.
4. If the backend reports `background_unavailable`, switch to `dispatch: "auto"` or `dispatch: "foreground"` only when foreground control is acceptable.

Example:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "element_action",
    "window_id": "uia-hwnd:123456",
    "element_index": 7,
    "operation": "invoke",
    "dispatch": "background"
  }
}
```

Use `uia_snapshot` to inspect the bounded Windows UI Automation tree when the newer window-state loop is not available:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "uia_snapshot",
    "max_depth": 4,
    "max_nodes": 200
  }
}
```

The snapshot returns element paths, roles, names/titles, automation IDs, class names, optional Terminator-style selectors, frames, enabled/focused state, actions, and child nodes. Use it to choose an element, not as final visual proof.

Use `uia_action` for a structural action:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "uia_action",
    "target": {
      "role": "Button",
      "title": "OK"
    },
    "operation": "invoke"
  }
}
```

Supported operations are:

- `invoke`: activate a button, menu item, checkbox, or similar control
- `focus_window`: restore and bring the owning top-level window to the foreground
- `minimize`, `restore`, `maximize`: change the owning top-level window state without clicking titlebar buttons
- `focus`: focus a text field or focusable element after activating its window
- `set_value`: set text/value; pass `value` or `text`
- `click`: click the element through the Windows UIA wrapper only when the snapshot says click is the available action and no structural operation fits
- `close`: close the owning top-level window only when the user explicitly asked to close that app/window

Targeting options:

- Prefer a semantic `target` when the control has a stable role plus title/name, automation ID, class name, handle, process ID, framework ID, or selector.
- Use a `path` returned by the latest `uia_snapshot` only while the UI is unchanged.
- You may pass a `selector` or `target.selector` from the snapshot, such as `role:Button && name:OK`.
- If an action reports ambiguity, take a fresh snapshot and narrow the target with role plus title/name/automation ID/class name.
- If an action reports a missing target, take a fresh snapshot before trying coordinates.

Action selection:

- Prefer the actions listed on the target node. If a node offers `invoke`, use `invoke`, not `click`.
- Prefer `element_action` over `uia_action` when the backend advertises `element-index-targeting`; it preserves the background-first dispatch contract.
- For window focus, hiding, restoring, or maximizing, use `focus_window`, `minimize`, `restore`, or `maximize`; do not click titlebar buttons.
- For typing into an app, first structurally focus the app/window if needed, then `set_value` on the target field. A global `type` result only proves keys were sent, not that they landed in the intended control.
- After a window operation, navigation, menu open/close, dialog transition, or other layout change, take a fresh `uia_snapshot` before reusing a path.
- Use pixel `click` only after structural UIA, keyboard, browser, and app-native options do not fit, and only from a fresh screenshot with an unambiguous target.

UIA actions are attempts, not proof. They attach a fresh screenshot after state-changing actions; inspect that image before saying the requested outcome happened.

## Windows Session Caveats

Windows desktop capture and UI Automation depend on the interactive desktop session where A0 CLI is running. Remote Desktop, VM consoles, UAC prompts, elevated apps, locked screens, minimized/disconnected RDP sessions, and services can prevent capture or UIA access.

If `computer_use_remote` returns `COMPUTER_USE_REARM_REQUIRED`, `COMPUTER_USE_APPROVAL_REQUIRED`, `COMPUTER_USE_CAPTURE_UNAVAILABLE`, `COMPUTER_USE_UIA_UNAVAILABLE`, or `status=rearm required`, stop immediately and ask the user to re-arm or fix the Windows desktop session. Do not bypass a permission/session failure with server screenshots, Docker commands, `linux-desktop`, or browser fallbacks.

## Geometry

Windows captures can use a virtual desktop that includes multiple monitors and negative origins. Use the capture/session `origin_x`, `origin_y`, `width`, and `height` as the coordinate space, and use normalized `[0,1]` coordinates only relative to that virtual screen.
