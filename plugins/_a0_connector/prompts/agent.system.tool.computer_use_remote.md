### computer_use_remote

Shown when a connected A0 CLI or Launcher host gateway advertises enabled Computer Use (`/computer-use on`) and does not need re-arming. Runtime-gated beta desktop control through that host bridge on the user's machine. Availability, backend support, and trust mode are checked when the tool runs, together with host-bridge presence, local enablement, and re-arm state. Computer Use enablement is scoped to the current CLI session or Launcher Host access lease, not scoped to a single chat context.

Use this for native host desktop UI inspection, screenshots, background-safe window/element actions when supported, clicking, scrolling, typing, key presses, and status checks. Do not use it for ordinary web-page navigation or host-browser control; use the browser tool for web pages unless browser automation cannot express the task. For complex desktop workflows, load and follow skill `host-computer-use` before proceeding.

This is the only desktop-control path for the user's connected host/local computer. Do not substitute the `linux-desktop` skill, the Agent Zero Desktop/Xpra surface, `desktopctl.sh`, `code_execution_tool`, or Docker/server shell commands for host screen actions; those target the internal Agent Zero runtime and cannot see or control the user's host screen.

If the tool reports no CLI/Launcher host bridge, disabled computer use, or `COMPUTER_USE_REARM_REQUIRED`, stop and tell the user to run `/computer-use on` in the A0 Launcher chat when using Launcher Host access, or in A0 CLI otherwise, and approve any host permission prompt.

Call `start_session` before screen-driven tasks. Use `status` for state only, `capture` for screenshots without an action, and `stop_session` when the desktop task is complete. Read `backend_id`, `backend_family`, `features`, and the structured `capabilities` object in status/session results. When capabilities report native windows, window state, element indexes, and background dispatch, prefer `list_windows` -> `get_window_state` -> `element_action` with `dispatch: "background"` before using global coordinates. Interactive coordinate actions should use normalized global-screen coordinates from the most recent capture.

Some actions are backend-specific and intentionally documented only in backend skills. If `status` or `start_session` reports backend-specific features or tells you to load a backend skill, load and follow that skill before using those backend-only actions. For structural targeting details, load and follow the backend-specific skill such as `host-computer-use-macos` or `host-computer-use-windows`; do not apply one backend's guidance to another backend.

State-changing actions automatically attach a fresh screen after they run unless the backend returns a definitive structural background result. Treat key presses, clicks, scrolling, and typing as attempts, not success; treat foreground fallbacks the same way. Inspect the latest attached screen, or one explicit `capture` if it is unclear or unchanged, before saying the requested outcome happened. If the tool says a screen was attached but you cannot actually inspect the image, stop and report that visual verification is unavailable; do not continue by assuming the host state. A `type` result only proves keystrokes were sent; it does not prove that text landed in the intended place.

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "status"
  }
}
```

Required argument:
- `action`: one of `start_session`, `status`, `capture`, `list_windows`, `get_window_state`, `element_action`, `move`, `click`, `scroll`, `key`, `type`, `stop_session`; backend skills may document additional backend-only action values

Optional arguments by action:
- `session_id`: session returned by `start_session`
- `pid`, `window_id`: target a native app/window for `get_window_state` and `element_action`
- `element_index`: target an element from the latest `get_window_state`
- `operation`: action such as `invoke`, `press`, `set_value`, `focus`, or backend-specific operations
- `dispatch`: `background`, `auto`, or `foreground`; prefer `background` for `element_action`
- `x`, `y`: normalized `[0,1]` global-screen coordinates for `move` and `click`
- `button`: `left`, `right`, or `middle` for `click`
- `count`: click count for `click`
- `dx`, `dy`: scroll amounts for `scroll`
- `key` or `keys`: key press value for `key`
- `text`: text to type for `type`
- `submit`: boolean Enter-after-type flag for `type`

Status/session results may include `contract_version` and `capabilities`. Treat `capabilities.identity.pid`, `capabilities.identity.window_id`, `capabilities.identity.element_index`, and `capabilities.dispatch.background` as the authoritative cross-platform contract for whether the native background loop is available. Use `features` for backend-specific refinements and skill selection.
