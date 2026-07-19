---
name: host-computer-use
description: Beta desktop control through the connected A0 CLI host. Use for the user's host/local computer screenshots, screen inspection, menus, native app UI, OS-level clicking, scrolling, typing, or checking computer_use_remote status. Use instead of linux-desktop for host/local machine control. Do not use for ordinary browser navigation; host browser requests should use the browser tool.
tags: ["host", "local", "desktop", "screen", "computer-use", "wayland", "ubuntu", "macos", "windows"]
triggers:
  - "computer use"
  - "host computer"
  - "host desktop"
  - "local computer"
  - "local desktop"
  - "my computer"
  - "my screen"
  - "host screen"
  - "local screen"
  - "Ubuntu Wayland desktop"
---

# Host Computer Use

This skill unlocks the beta `computer_use_remote` tool for connected local desktop control through A0 CLI or a Launcher host gateway. Prefer native background-safe computer use when the connected backend advertises window and element-index features.

## When to Use

Load this skill before using `computer_use_remote` for local desktop and native UI tasks on the connected machine. Use it for the user's real host screen, not the internal Agent Zero Desktop.

If the task is browser-only and the user is flexible, prefer direct browser tooling because it is usually more reliable and token-efficient than screenshot-driven desktop control.

If the task needs shell execution on the CLI host, load `host-code-execution` separately rather than treating desktop control and shell execution as one affordance.

## Host vs Docker Desktop Boundary

This skill controls the user's connected host/local computer through A0 CLI. It is not the built-in Linux Desktop/Xpra skill.

Never switch to `linux-desktop`, the Agent Zero Desktop/Xpra surface, `desktopctl.sh`, `code_execution_tool`, or Docker/server shell commands as a fallback for host screen actions such as screenshots, clicking, typing, desktop state changes, or checking visible host UI. Those paths only see the internal Agent Zero runtime. If `computer_use_remote` is unavailable, disabled, or needs re-arming, stop and ask the user to run `/computer-use on` in the A0 Launcher chat when using Launcher Host access, or in A0 CLI otherwise, and approve the platform permission prompt.

## Browser Boundary

- If the user asks to use/open/control their host browser, local browser, Chrome, "my browser", or a URL in the host browser, use the `browser` tool. The Browser plugin chooses Docker or A0 CLI host-browser runtime from Browser settings and can surface Chrome remote-debugging setup.
- Do not start `computer_use_remote` for web-page navigation just because the phrase "host browser" appears. Use this skill only for desktop/browser-chrome tasks that the `browser` tool cannot express.
- If host-browser setup fails or mentions remote debugging, tell the user to open `chrome://inspect/#remote-debugging`, enable "Allow remote debugging for this browser instance", run `/browser host on`, and retry.
- Do not fall back to `code_execution_remote`, `xdg-open`, `sensible-browser`, or Python `webbrowser.open` for host-browser control. Those can launch pages without giving Agent Zero browser control or setup diagnostics.

## Tool Contract

Use:

```json
{
  "tool_name": "computer_use_remote",
  "tool_args": {
    "action": "start_session"
  }
}
```

Arguments:

- `action`: `start_session`, `status`, `capture`, `list_windows`, `get_window_state`, `element_action`, `move`, `click`, `scroll`, `key`, `type`, `stop_session`
- `session_id`: optional after `start_session`
- backend skills may document additional backend-only action values; use them only when backend metadata advertises matching support and after loading the backend-specific skill
- `list_windows`: returns native top-level window records when the backend supports them
- `get_window_state`: pass `pid` and/or `window_id`; returns a target-window accessibility tree with stable `element_index` values for the current state
- `element_action`: pass `element_index` from the latest `get_window_state`; optional `operation`, `value`/`text`, and `dispatch`
- `dispatch`: `background`, `auto`, or `foreground`; default to `background` for element actions
- `move`: `x`, `y` normalized to `[0,1]`
- `click`: optional `x`, `y`, optional `button` (`left`, `right`, `middle`), optional `count`
- `scroll`: `dx`, `dy`
- `key`: `key` or `keys`
- `type`: `text`, optional `submit` boolean

Availability, backend support, and trust mode are checked when the tool runs. If no A0 CLI or Launcher host gateway is connected, or local computer use is disabled, tell the user what to enable instead of using the server environment.

If any tool result contains `COMPUTER_USE_REARM_REQUIRED` or `status=rearm required`, stop the computer-use sequence immediately. Do not retry `start_session`, do not call `capture`, and do not use shell, vision, or screenshot fallbacks to bypass it. Tell the user that the connected host has Computer Use configured but the installed desktop-control backend is not armed; they should run `/computer-use on` in the A0 Launcher chat when using Launcher Host access, or in A0 CLI otherwise, and approve the platform permission prompt if shown.

## Core Loop

1. Call `start_session` first.
2. Read the returned `backend_id`, `backend_family`, `features`, `contract_version`, and `capabilities`; load a backend-specific Computer Use skill when the task needs backend-only affordances.
3. Prefer the structured `capabilities` object over guessing from OS names. Use `capabilities.identity.pid`, `capabilities.identity.window_id`, `capabilities.identity.element_index`, and `capabilities.dispatch.background` as the portable contract for the native background loop.
4. If the backend advertises native window listing through capabilities or `native-window-list`, call `list_windows` before using coordinates.
5. If the backend advertises window state and element-index targeting through capabilities or features, call `get_window_state` for the target `pid`/`window_id`, then use `element_action` with `dispatch: "background"` by default.
6. If `element_action` reports `background_unavailable`, use `dispatch: "auto"` or `dispatch: "foreground"` only when foreground control is acceptable for the user/task.
7. Decide final success from the latest screenshot or a definitive structural result, not from memory.
8. Interactive actions already attach a fresh screenshot after they run; inspect it before claiming the requested outcome succeeded.
9. Use `status` for state without starting a session.
10. Use `capture` only when you need another screenshot without taking an action.

## Backend Skills

- If the backend is Linux/Wayland or features include `atspi-tree-snapshot` / `atspi-structural-targeting`, load `host-computer-use-linux` before using Linux AT-SPI structural actions.
- If the backend is macOS or features include `accessibility-tree-snapshot` / `accessibility-structural-targeting`, load `host-computer-use-macos` before using macOS structural Accessibility actions.
- If the backend is Windows or features include `uia-tree-snapshot` / `uia-structural-targeting`, load `host-computer-use-windows` before using Windows UI Automation structural actions.
- Do not use backend-specific actions just because their argument names exist in the generic contract. Treat them as unavailable unless the connected CLI advertises the matching feature.

## Operating Rules

- Only the latest screenshot or a definitive tool result counts as evidence.
- If a tool result says a screenshot was attached but you cannot actually see the image, stop and report that visual verification is unavailable. Do not continue with another action from an assumed host state.
- Prefer the background-safe native loop when advertised: `list_windows` -> `get_window_state` -> `element_action`.
- Outside advertised structural accessibility support, use normalized global screen coordinates; do not assume window ids, element indexes, background-safe input, or semantic click targets unless the runtime explicitly advertises them.
- Treat `dispatch: "foreground"` as intentional control of the user's visible desktop. Use it only after deciding that a background action is unavailable or unsuitable.
- On Linux, AT-SPI structural targeting uses backend-specific actions documented in `host-computer-use-linux`; do not apply macOS AX-specific assumptions unless the backend is macOS.
- Prefer accessibility and semantic UI paths first: shortcuts, command palettes, menu accelerators, address/search bars, focus traversal, and other keyboard-accessible controls.
- Prefer `key` and `type` over pointer actions whenever a reliable keyboard path exists.
- When a menu or popup is open, treat it as the active UI and prefer keyboard navigation over clicking small transient rows by coordinate.
- If a click dismisses a menu or popup without producing the expected next UI, treat that attempt as failed.
- If the same approach has already failed twice without visible progress, switch strategy instead of repeating it.
- Do not infer focus or task completion from chat logs, sidebars, tool summaries, or status text.
- Never claim a state-changing action succeeded until the latest screenshot visibly confirms it.
- A `type` tool result only confirms keystrokes were sent. It is not evidence that the text landed in the intended application.
- For browser-navigation tasks done through this tool, only claim success if the browser content area visibly shows the destination page or result.
- If the attached screenshot appears unchanged after a state-changing action, use one explicit `capture` to verify before repeating the same action.
- Use `type(..., submit=true)` only for URL or navigation-style entry where Enter should fire immediately after typing.
- Do not use `submit=true` for ordinary text fields. Type first, then send `enter` separately if needed.

## Pointer And Scrolling

- Try keyboard scrolling first: `page_down`, `page_up`, `space`, `shift+space`, arrows, `home`, or `end`.
- Use `scroll` when the desired pane is already active or keyboard scrolling cannot target it.
- Treat `move` and `click` as last-resort actions for controls that cannot be reached through backend-specific structural targeting, keyboard, browser, or app-native tooling.
- Before clicking, make sure the latest screenshot makes the target unambiguous. Use one deliberate click, then reassess from the fresh screenshot.

## Control Signals

- Treat user interventions as high-priority control signals.
- If the user says `stop`, `pause`, `abort`, `hold`, `don't continue`, or equivalent, halt immediately and do not use computer-use tools again until the user explicitly resumes.
