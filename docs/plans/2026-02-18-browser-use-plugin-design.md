# Browser-Use Plugin Design

## Overview

A new plugin for Agent Zero's plugin system (PR #998) that provides browser automation capabilities alongside the existing `browser_agent.py` tool. The plugin offers two tools (step-by-step and autonomous), a shared headed browser session, and a real-time CDP screencast viewer embedded in the WebUI.

## Goals

- Give the agent both deterministic (step-by-step) and autonomous browser control
- Let the user view and interact with the same browser the agent uses
- Stream the browser view in real-time via CDP screencast in a WebUI modal
- Provide a settings tab for browser-use configuration
- Follow PR #998 plugin conventions so it works when the plugin system merges

## Non-Goals

- Does not replace or migrate the existing `browser_agent.py` tool
- Does not implement noVNC or Xvfb-based streaming
- Does not provide multi-browser/multi-tab management UI (v1)

---

## Plugin Directory Structure

```
plugins/browser_use/
├── api/
│   ├── browser_use_connect.py      # Start/stop browser session, return CDP ws URL
│   ├── browser_use_status.py       # Get browser state (url, title, alive?)
│   └── browser_use_interact.py     # Proxy user interactions (click, type, navigate)
├── tools/
│   ├── browser_step.py             # CLI-style step tool (open/click/type/state/screenshot)
│   └── browser_auto.py             # Enhanced autonomous browser-use Agent tool
├── helpers/
│   ├── session_manager.py          # Shared browser session lifecycle (create, get, destroy)
│   └── cdp_proxy.py                # WebSocket proxy for CDP (security boundary)
├── extensions/
│   ├── python/
│   │   └── agent_init/
│   │       └── _10_browser_cleanup.py  # Clean up browser sessions on agent init/reset
│   └── webui/
│       └── sidebar-quick-actions-main-start/
│           └── browser-entry.html  # Sidebar button to open browser viewer
├── webui/
│   ├── browser-viewer.html         # Modal: CDP screencast viewer + interaction overlay
│   ├── browser-viewer-store.js     # Alpine store for viewer state
│   ├── browser-settings.html       # Settings tab component
│   └── browser-settings-store.js   # Alpine store for settings
└── prompts/
    └── agent.system.tool.browser_step.md   # Tool description for the step tool
```

---

## Architecture

### Session Manager (`helpers/session_manager.py`)

Central component that manages a single browser session per agent context.

**Responsibilities:**
- Create and destroy browser sessions (Playwright via browser-use)
- Expose the CDP WebSocket URL for the screencast viewer
- Provide an asyncio.Lock for concurrency control between tools and user interactions
- Store session in agent data (`agent.get_data` / `agent.set_data`)

**Browser launch configuration:**
- Headed mode with `--remote-debugging-port=0` (OS picks free port)
- CDP WebSocket URL extracted from Chromium startup
- Falls back to headless if no display available (CDP screencast works in both modes)
- Session persists across tool calls within the same agent context
- Destroyed on context reset or explicit close

### CDP Proxy (`helpers/cdp_proxy.py`)

WebSocket relay between the WebUI viewer and Chromium's CDP endpoint. Provides a security boundary by whitelisting allowed CDP methods.

**Allowed methods:**
- `Page.startScreencast`, `Page.stopScreencast`, `Page.screencastFrameAck`
- `Page.screencastFrame` (server → client)
- `Input.dispatchMouseEvent`, `Input.dispatchKeyEvent`
- `Page.navigate`

**Denied methods:**
- `Runtime.evaluate`, `Target.*`, `Network.*`, and all others

### Concurrency Model

```
SessionManager.lock (asyncio.Lock)
    ├── browser_step.execute()     → acquires lock, does action, releases
    ├── browser_auto.execute()     → acquires lock for entire run, releases on done
    ├── user click via CDP proxy   → acquires lock briefly for dispatch
    └── screencast frames          → NO lock needed (read-only observation)
```

When `browser_auto` holds the lock during an autonomous run, user interactions through the viewer are queued. The viewer shows an overlay: "Agent is working... interactions will be applied when done."

---

## Tools

### `browser_step` — Deterministic Step-by-Step Control

The agent calls one action per invocation and receives the result. No internal LLM loop.

```python
class BrowserStep(Tool):
    async def execute(self, action="", target="", value="", **kwargs) -> Response:
```

| Action | Target | Value | Returns |
|--------|--------|-------|---------|
| `open` | URL | — | Page title, URL |
| `state` | — | — | Clickable elements with indices |
| `click` | element index | — | Updated page state |
| `type` | — | text to type | Confirmation |
| `input` | element index | text | Click + type combo |
| `screenshot` | — | — | Screenshot path (img://) |
| `scroll` | `up`/`down` | pixel amount | Confirmation |
| `back` | — | — | New URL |
| `keys` | key combo | — | Confirmation |
| `select` | element index | option value | Confirmation |
| `extract` | query string | — | LLM-extracted data from page |
| `eval` | JS expression | — | JS result |
| `close` | — | — | Session closed |

### `browser_auto` — Enhanced Autonomous Agent

Wraps browser-use's `Agent` class with configurable parameters and shared session.

```python
class BrowserAuto(Tool):
    async def execute(self, task="", max_steps="25", vision="auto",
                      flash_mode="false", reset="false", **kwargs) -> Response:
```

Enhancements over existing `browser_agent.py`:
- Configurable per-call: `max_steps`, `vision`, `flash_mode`
- Shared session with `SessionManager` so user watches in viewer
- Step-by-step reasoning streamed to process group
- Lock-aware with viewer overlay during autonomous runs

Both tools share the same browser session. The agent can use `browser_step` to navigate, then `browser_auto` for complex tasks, then `browser_step` to verify.

---

## API Endpoints

### `browser_use_connect.py` — Session Lifecycle

| Input | Output | Description |
|-------|--------|-------------|
| `{ action: "start", context_id }` | `{ cdp_ws_url, status }` | Start browser, return proxy WS URL |
| `{ action: "stop", context_id }` | `{ status: "closed" }` | Close browser session |
| `{ action: "status", context_id }` | `{ alive, url, title, busy }` | Check session state |

### `browser_use_interact.py` — HTTP Interaction Fallback

| Input | Output | Description |
|-------|--------|-------------|
| `{ action: "navigate", url }` | `{ url, title }` | Navigate to URL |
| `{ action: "screenshot" }` | `{ path }` | Take screenshot |
| `{ action: "state" }` | `{ elements }` | Get clickable elements |

### `browser_use_settings.py` — Plugin Settings

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| GET | — | `{ settings }` | Get current settings |
| POST | `{ settings }` | `{ ok }` | Save settings |

### WebSocket Proxy Route

```
WS /api/plugins/browser_use/cdp_ws?context_id=<id>
```

Authenticated WebSocket relay with CDP method whitelisting.

---

## WebUI Components

### Sidebar Extension Button

`extensions/webui/sidebar-quick-actions-main-start/browser-entry.html`

Globe icon button placed via `x-move-after` directive. Opens the browser viewer modal.

### Browser Viewer Modal

`webui/browser-viewer.html` + `browser-viewer-store.js`

Three zones:
1. **URL bar** — shows current URL, allows manual navigation
2. **Canvas** — CDP screencast frames rendered on `<canvas>`, mouse/keyboard events captured and dispatched via CDP proxy
3. **Footer** — Screenshot, New Tab, Close Browser buttons

Store manages WebSocket lifecycle, screencast frame rendering, and input event translation.

**CDP Screencast flow:**
1. Modal opens → WebSocket connects to CDP proxy
2. Sends `Page.startScreencast` (JPEG, quality 80, max 1024px wide)
3. Receives `Page.screencastFrame` events with base64 JPEG data
4. Decodes frames → draws on canvas
5. Mouse/keyboard events translated to CDP coordinates and dispatched
6. When agent holds lock, semi-transparent overlay shows but screencast continues

### Settings Tab

`webui/browser-settings.html` + `browser-settings-store.js`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| Browser Mode | select | `chromium` | chromium / real / remote |
| Headless | toggle | `false` | Run without display |
| Default Max Steps | number | `25` | For `browser_auto` |
| Vision Mode | select | `auto` | auto / true / false |
| Flash Mode | toggle | `false` | Fast mode |
| Screencast Quality | slider | `80` | JPEG quality 1-100 |
| Window Size | select | `1024x768` | Browser viewport |
| Browser Use API Key | password | — | For remote/cloud mode |

---

## Extension Hooks

### `agent_init/_10_browser_cleanup.py`

Cleans up any orphaned browser sessions when an agent context initializes or resets. Prevents resource leaks from crashed sessions.

---

## Design Decisions

1. **CDP screencast over noVNC** — No external dependencies (Xvfb, VNC server). Works in headless mode. Same technology Chrome DevTools uses.

2. **WebSocket proxy with whitelisting** — Raw CDP gives full browser control. The proxy restricts to screencast + input methods only, preventing code execution or data exfiltration.

3. **Shared session via SessionManager** — Both tools and the viewer use one browser. The user watches exactly what the agent does. Lock-based concurrency prevents conflicts.

4. **Two tools, one session** — `browser_step` for precision, `browser_auto` for autonomy. The agent picks the right approach. They share state, so the agent can mix approaches within one task.

5. **Plugin structure follows PR #998** — Built to the conventions in `build_docs/A0-PLUGINS.md`. When the plugin system merges, this plugin should work with minimal integration changes.
