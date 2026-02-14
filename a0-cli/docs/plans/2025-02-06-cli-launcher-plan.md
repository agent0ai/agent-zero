# a0 CLI Launcher - Implementation Plan

Based on: `2025-02-06-cli-launcher-design.md`

## Phase 1: Fix Existing Bugs (30 min)

These are blocking issues that prevent the current TUI from working.

### Task 1.1: Fix CSS Path
**File:** `src/a0/tui/app.py`
**Change:**
```python
# Line 22, change:
CSS_PATH = "src/a0/tui/styles/theme.tcss"
# To:
CSS_PATH = "styles/theme.tcss"
```
**Test:** Run `a0`, verify TUI renders with proper styling (not brown screen)

### Task 1.2: Fix Quit Binding
**File:** `src/a0/tui/app.py`
**Change:** Update BINDINGS to show quit in footer
```python
BINDINGS = [
    Binding("ctrl+q", "quit", "Quit", show=True),
    Binding("ctrl+d", "toggle_dark", "Theme"),
]
```
**Test:** Run TUI, verify Footer shows "Ctrl+Q Quit"

### Task 1.3: Verify Escape Works
**File:** `src/a0/tui/screens/main.py`
**Check:** `action_cancel()` exists and is bound to escape
**Test:** Run TUI, press Escape, verify it responds (currently just cancels poller)

---

## Phase 2: Create Launcher Package (1 hour)

### Task 2.1: Create Package Structure
```bash
mkdir -p src/a0/launcher
touch src/a0/launcher/__init__.py
```

### Task 2.2: Implement Menu Renderer
**File:** `src/a0/launcher/menu.py`

**Functions to implement:**
- `run_menu() -> str | None` - Main loop, returns selected action or None
- `_render_menu(selected: int)` - Draw menu with highlight
- `_get_key() -> str` - Read single keypress (raw mode)

**Dependencies:** `rich` (already installed)

**Key behaviors:**
- Arrow up/down or j/k to navigate
- Enter or 1-5 to select
- Escape to quit (return None)
- Highlight current selection with rich styling

### Task 2.3: Implement Action Handlers
**File:** `src/a0/launcher/actions.py`

**Functions to implement:**
- `launch_tui(url, api_key, project, cwd) -> bool` - Returns True to show menu again
- `launch_repl(url, api_key, project)` - Blocking, returns when done
- `show_status(url, api_key)` - Print status, wait for keypress, return
- `toggle_docker(compose_file)` - Start if stopped, stop if running
- `open_settings()` - Interactive config editor

**Helper functions:**
- `check_health(url, api_key, timeout=0.5) -> bool`
- `prompt_auto_start() -> bool` - "Start Agent Zero? [Y/n]"
- `start_docker_with_progress(compose_file)` - Show progress bar
- `wait_for_ready(url, api_key, timeout=30)` - Poll until healthy

### Task 2.4: Export from Package
**File:** `src/a0/launcher/__init__.py`
```python
from .menu import run_menu
from .actions import (
    launch_tui,
    launch_repl,
    show_status,
    toggle_docker,
    open_settings,
)
```

---

## Phase 3: Wire Up Entry Point (30 min)

### Task 3.1: Modify CLI Entry Point
**File:** `src/a0/cli.py`

**Change the `main()` callback:**
```python
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, ...):
    if ctx.invoked_subcommand is None:
        from a0.banner import show_banner
        from a0.launcher import run_menu, launch_tui, launch_repl, ...

        show_banner()

        while True:
            action = run_menu()
            if action is None:  # Escape pressed
                break
            elif action == "tui":
                if not launch_tui(...):
                    break
            elif action == "repl":
                launch_repl(...)
            # ... etc
```

### Task 3.2: Pass Config to Actions
Ensure URL, API key, project, cwd are passed from CLI options to action handlers.

---

## Phase 4: TUI Return-to-Menu (30 min)

### Task 4.1: Modify TUI Exit Behavior
**File:** `src/a0/tui/app.py`

**Change:** App should return a result indicating whether to show menu
```python
class AgentZeroTUI(App[str | None]):
    # Return type is now str | None

    def action_quit(self) -> None:
        self.exit(result=None)  # Full quit
```

### Task 4.2: Modify MainScreen Escape
**File:** `src/a0/tui/screens/main.py`

**Change:**
```python
def action_cancel(self) -> None:
    self.app.exit(result="menu")  # Return to menu
```

### Task 4.3: Handle in Launcher
**File:** `src/a0/launcher/actions.py`

```python
def launch_tui(url, api_key, project, cwd) -> bool:
    tui = AgentZeroTUI(agent_url=url, ...)
    result = tui.run()
    return result == "menu"  # True = show menu again
```

---

## Phase 5: Settings Screen (45 min)

### Task 5.1: Create Settings Editor
**File:** `src/a0/launcher/settings.py`

**Functions:**
- `run_settings() -> None` - Interactive config editor
- `_render_settings(config, selected)` - Draw fields
- `_edit_field(field_name, current_value) -> str` - Inline edit

**Fields to edit:**
- `agent_url` - Text input
- `api_key` - Text input (masked display)
- `theme` - Cycle: dark/light
- `docker_compose` - Text input (file path)

### Task 5.2: Wire to Menu
**File:** `src/a0/launcher/actions.py`
```python
def open_settings():
    from .settings import run_settings
    run_settings()
```

---

## Phase 6: Installer Script (1 hour)

### Task 6.1: Create Installer
**File:** `install.sh`

**Structure:**
```bash
#!/bin/bash
set -e

# Colors and formatting
# Dependency checks (python, docker)
# Install uv if missing
# Install a0-cli via uv
# Pull docker image
# Create default config
# Success message
```

### Task 6.2: Add Uninstall Flag
```bash
if [ "$1" = "--uninstall" ]; then
    uv tool uninstall a0-cli
    # Remove config
    exit 0
fi
```

### Task 6.3: Add Offline Flag
```bash
if [ "$1" = "--offline" ]; then
    SKIP_DOCKER_PULL=1
fi
```

---

## Phase 7: Testing (30 min)

### Task 7.1: Manual Test Script
Create a checklist for manual testing:
- [ ] `a0` shows banner then menu
- [ ] Arrow keys navigate menu
- [ ] Number keys select directly
- [ ] Escape quits from menu
- [ ] TUI launches and renders correctly
- [ ] Escape in TUI returns to menu
- [ ] Ctrl+Q quits from anywhere
- [ ] REPL works and returns to menu on /exit
- [ ] Status shows connection state
- [ ] Start/Stop toggles Docker
- [ ] Settings edits persist

### Task 7.2: Add Unit Tests
**File:** `tests/test_launcher.py`
- Test menu key handling
- Test action routing
- Test health check logic

---

## Implementation Order

```
Phase 1 (bugs)     ████████░░░░░░░░░░░░  30 min
Phase 2 (launcher) ████████████████░░░░  1 hour
Phase 3 (wire up)  ██████░░░░░░░░░░░░░░  30 min
Phase 4 (TUI exit) ██████░░░░░░░░░░░░░░  30 min
Phase 5 (settings) █████████░░░░░░░░░░░  45 min
Phase 6 (install)  ████████████░░░░░░░░  1 hour
Phase 7 (testing)  ██████░░░░░░░░░░░░░░  30 min
                                        ─────────
                                        ~5 hours
```

## Dependencies Between Tasks

```
1.1 ─┬─► 3.1 (need working TUI before wiring)
1.2 ─┤
1.3 ─┘

2.1 ─► 2.2 ─► 2.3 ─► 2.4 ─► 3.1

3.1 ─► 4.1 ─► 4.2 ─► 4.3

5.1 ─► 5.2 (independent of phases 3-4)

6.1 ─► 6.2 ─► 6.3 (independent, can do anytime)

7.1 ─► 7.2 (after all features done)
```

## Quick Wins (Can Do Now)

These are independent and can be done immediately:
1. Task 1.1: Fix CSS path (1 line change)
2. Task 1.2: Fix quit binding (1 line change)
3. Task 2.1: Create package structure (mkdir + touch)
