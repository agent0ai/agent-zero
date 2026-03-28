# a0 CLI Launcher Design

## Overview

Replace the current direct-to-TUI launch with an interactive launcher that shows an animated banner followed by a menu. This provides a clear entry point for users without requiring memorization of subcommands.

## User Flow

```
User types: a0
      │
      ▼
Animated banner plays (~0.5s)
      │
      ▼
Menu appears:
  [1] Chat (TUI)      Full terminal interface
  [2] Chat (REPL)     Simple text chat
  [3] Status          Check Agent Zero
  [4] Start/Stop      Docker container
  [5] Settings        Configure a0

  ↑↓ Navigate  •  Enter/Number Select  •  Esc Quit
      │
      ▼
If Chat selected + Agent Zero not running:
  "Agent Zero is not running. Start it now? [Y/n]"
  Y → Start Docker, wait for ready, launch chat
  N → Return to menu
```

## Navigation Model

| Context | Escape | Ctrl+C / Ctrl+Q |
|---------|--------|-----------------|
| Menu (top level) | Quit app | Quit app |
| TUI main screen | Back to menu | Quit app |
| TUI modal/overlay | Close modal | Quit app |
| REPL mode | Back to menu | Quit app |
| Settings screen | Back to menu | Quit app |

Key principle: Escape goes "up one level." Ctrl+C/Q always exits entirely.

When returning from TUI to menu, the session stays alive. Selecting TUI again resumes where you left off.

## Auto-Start Flow

When user selects a Chat mode:

1. Quick health check: `GET /health` (500ms timeout)
2. If running: Launch chat mode normally
3. If not running: Prompt "Agent Zero is not running. Start it now? [Y/n]"
4. If Y: Run `docker compose up -d`, show progress, poll `/health` until ready
5. Launch chat mode

Timeouts:
- Docker start: 60 seconds
- Health poll: Every 2s for 30s max
- On failure: Show error, return to menu

## Settings Screen

```
┌─────────────────────────────────────────────────────────┐
│  Settings                                               │
├─────────────────────────────────────────────────────────┤
│  Agent Zero URL     http://localhost:55080              │
│  API Key            ••••••••••••                        │
│  Theme              dark                                │
│  Docker Compose     ~/agent-zero/docker-compose.yml     │
├─────────────────────────────────────────────────────────┤
│  ↑↓ Navigate  •  Enter Edit  •  Esc Back                │
└─────────────────────────────────────────────────────────┘
```

- Arrow keys to navigate fields
- Enter to edit (inline text input)
- Escape saves and returns to menu
- Persists to `~/.config/a0/config.toml`

## Bug Fixes (Existing TUI)

### CSS Path
```python
# Current (broken):
CSS_PATH = "src/a0/tui/styles/theme.tcss"

# Fixed (relative to app.py):
CSS_PATH = "styles/theme.tcss"
```

### Quit Binding Visibility
```python
BINDINGS = [
    Binding("ctrl+q", "quit", "Quit", show=True),
    Binding("ctrl+d", "toggle_dark", "Theme"),
]
```

### Escape Returns to Menu
```python
def action_cancel(self) -> None:
    self.app.exit(result="menu")  # Signal to re-show menu
```

### TUI Exit Handling
```python
# In launcher/actions.py:
def launch_tui():
    tui = AgentZeroTUI(...)
    result = tui.run()
    if result == "menu":
        return True  # Show menu again
    return False  # Quit entirely
```

## One-Line Installation

```bash
curl -sSL https://get.agentzero.dev | sh
```

### Installer Steps

1. Check dependencies (Python 3.11+, Docker)
2. Install `uv` if missing
3. Install a0 CLI: `uv tool install a0-cli`
4. Pull Docker image: `docker pull frdel/agent-zero:latest`
5. Create default config: `~/.config/a0/config.toml`

### Installer Features

| Feature | Description |
|---------|-------------|
| Dependency detection | Checks Python, Docker; installs uv if missing |
| Idempotent | Safe to run multiple times (upgrades) |
| Platform support | macOS (Intel/ARM), Linux (x86_64/ARM64) |
| Offline mode | `--offline` skips Docker pull |
| Uninstall | `--uninstall` removes everything |

## Implementation Architecture

```
a0-cli/src/a0/
├── cli.py                    # Entry point calls launcher
├── banner.py                 # Animated A-logo (exists)
├── launcher/                 # NEW
│   ├── __init__.py
│   ├── menu.py               # Menu renderer (~100 lines)
│   └── actions.py            # Menu action handlers (~150 lines)
├── tui/
│   ├── app.py                # Fix CSS path, bindings
│   └── screens/main.py       # Fix escape behavior
└── client/
    └── ...
```

### Why Separate Launcher from Textual

The menu uses plain `rich` (no Textual) for instant startup. Textual has ~200ms overhead. This way, banner flows immediately into menu. Textual only loads when user selects TUI mode.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/a0/launcher/__init__.py` | Create | Package init |
| `src/a0/launcher/menu.py` | Create | Menu renderer |
| `src/a0/launcher/actions.py` | Create | Menu action handlers |
| `src/a0/cli.py` | Modify | Entry point calls launcher |
| `src/a0/tui/app.py` | Fix | CSS path, quit bindings |
| `src/a0/tui/screens/main.py` | Fix | Escape returns to menu |
| `install.sh` | Create | One-liner installer script |

## Out of Scope (Future Work)

- File attachments via CLI
- Session history browsing
- Notification display in terminal
- WebSocket streaming (currently uses polling)

These can be added incrementally after the launcher ships.
