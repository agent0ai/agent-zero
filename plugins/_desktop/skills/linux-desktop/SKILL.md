---
name: linux-desktop
description: Use when the user asks Agent Zero to operate the built-in Linux Desktop, XFCE apps, LibreOffice GUI apps, file manager, terminal, or visual desktop workflows.
version: "0.3.0"
author: "Agent Zero Core Team"
tags: ["linux", "desktop", "xfce", "libreoffice", "gui", "files", "terminal"]
triggers:
  - "Linux desktop"
  - "Desktop GUI"
  - "XFCE"
  - "LibreOffice GUI"
  - "file manager"
  - "terminal app"
  - "use the OS"
allowed_tools:
  - document_artifact
  - code_execution_tool
---

# Linux Desktop Interface

Use the Desktop as a full Linux GUI when the user explicitly needs a visual workflow, an installed desktop app, or manual layout polish that is awkward through structured file edits alone. Agent Zero may warm the persistent Desktop runtime during initial startup, but visible Desktop surface use remains opt-in. The Desktop is opt-in at the UI level: do not open a surface just because the user asks for a document. Use structured tools first for deterministic content changes, then use the Desktop for inspection, GUI-only actions, and final visual confirmation.

## Operating Model

The Desktop is an observe-act-verify control surface. Use this decision hierarchy:

1. Prefer structured tools such as `document_artifact` for deterministic file creation, reads, and edits.
2. Prefer app-native helpers for visible live edits, such as `desktopctl.sh calc-set-cell` for Calc/UNO spreadsheet changes.
3. Prefer launcher commands, window focus, keyboard shortcuts, menus, paste, and save commands.
4. Use coordinate clicks only as a last resort, and only after a fresh Desktop observation.
5. After any GUI action, verify through Desktop state, active window titles, screenshots, saved file state, or exported output.
6. For terminal or CLI-agent work, verify against a fresh final `observe --json --screenshot` captured after the command has finished or visibly returned to an input prompt. Do not report from an earlier screenshot path.

Keep these standing rules:

1. Treat Markdown as first-class. For writing, notes, reports, and drafts with no explicit binary Office requirement, create Markdown and use the custom Markdown editor when the user opens the canvas.
2. Treat ODF as first-class for LibreOffice office work: ODT in Writer, ODS in Calc, ODP in Impress. Use DOCX/XLSX/PPTX only for explicit OOXML compatibility.
3. Use the Desktop only when the user asks for the Desktop, a GUI app, binary Office visual work, or visual confirmation.
4. Never open the Desktop surface automatically from a tool result if the user has not opened it. Offer an explicit Open in Desktop action instead.
5. Launch common apps from the Desktop icons, the header buttons, or `/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh`.
6. Use the external Agent Zero Browser for web browsing. Do not launch an operating-system browser in this version.
7. Verify GUI work by observing the desktop state, checking window titles, and saving the file before reporting success. If exact terminal text matters, load or inspect the screenshot path returned by the final observation, not a screenshot captured before the text appeared.

## Control Flow

Use the helper script when the Desktop is already open and you need reliable app launches, clicks, keystrokes, or window checks from the agent shell. In the live Agent Zero runtime, prefer the absolute path so the command works from any current directory:

```bash
DESKTOP=/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh
$DESKTOP check
$DESKTOP state --json
$DESKTOP observe --json --screenshot
$DESKTOP launch calc
$DESKTOP wait-window LibreOffice
$DESKTOP windows LibreOffice
$DESKTOP focus LibreOffice
$DESKTOP key ctrl+s
```

The script targets the persistent `agent-zero-desktop` X display, sets `DISPLAY`, `XAUTHORITY`, and `HOME` to the XFCE profile, then uses `xdotool` for input. Startup normally prepares this session. If `check` fails during explicit Desktop work, report that the Desktop runtime is not ready instead of installing packages ad hoc.

If `observe --json --screenshot` shows a reachable display, visible Desktop/window entries, and a fresh screenshot, the Desktop is usable even when `active_window` is `null`; a bare XFCE desktop can have no active application window. Treat missing screenshots, missing display, or unavailable `xdotool`/`xwd` as blockers and stop with the specific readiness message instead of repeating clicks or inventing a fallback.

For direct app launches without coordinates:

```bash
DESKTOP=/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh
$DESKTOP launch writer
$DESKTOP launch calc
$DESKTOP launch impress
$DESKTOP launch terminal
$DESKTOP launch settings
$DESKTOP open-path /a0/usr/workdir
$DESKTOP focus "LibreOffice"
$DESKTOP paste-text "Text to insert"
$DESKTOP key ctrl+s
```

For live spreadsheet coworking, use the Calc helper instead of hand-written UNO snippets:

```bash
DESKTOP=/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh
$DESKTOP calc-set-cell /a0/usr/workdir/example.xlsx Sheet1 B2 "Cowork verified live"
```

This opens the workbook in the visible Desktop Calc session if needed, changes the cell through LibreOffice, saves the workbook, and verifies the `.xlsx` on disk. Because the edit happens through the running LibreOffice session, the user can see the sheet update without refreshing the Desktop surface.

For coordinate actions, clicks are explicitly last resort. First try `launch`, `open-path`, `wait-window`, `focus`, `key`, `paste-text`, `save`, or an app-native helper. If a coordinate action is still necessary, base it on a fresh screenshot observation and verify immediately afterward:

```bash
DESKTOP=/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh
$DESKTOP observe --json --screenshot
$DESKTOP click 120 180
$DESKTOP dblclick 120 180
$DESKTOP right-click 120 180
$DESKTOP drag 120 180 400 180
$DESKTOP scroll down 3
$DESKTOP type "Text to enter"
$DESKTOP observe --json
```

When browser automation is available, the higher-level QA flow is:

1. Open `http://127.0.0.1:32080`.
2. Open the Desktop surface from the UI or with `Alpine.store("rightCanvas").open("desktop")`.
3. Use browser mouse events into the Xpra iframe for real user-path testing.
4. Cross-check with `desktopctl.sh location` and `desktopctl.sh windows PATTERN`.
5. Capture the browser screenshot as visual evidence.

## Terminal And CLI Agent Verification

Terminal apps are visual state, not structured logs. When the task depends on exact terminal output, follow this stricter loop:

1. Run `desktopctl.sh observe --json --screenshot` immediately before acting to record the starting window and screenshot path.
2. Use `focus`, `paste-text` or `type`, and `key Return` to drive the terminal. Prefer CLI-native commands and keyboard input over clicks.
3. Wait until the CLI has visibly produced a response or returned to an input prompt.
4. Run a new final `desktopctl.sh observe --json --screenshot`.
5. Verify exact text only from the screenshot path returned by that final observation, or from a newer screenshot. Never use an earlier screenshot path as final evidence.
6. If the final screenshot is cropped, stale, or unreadable, capture another screenshot or report the result as unverified with that specific reason.

For nested CLI agents, a successful proof requires both the input prompt and the nested agent's visible response in the final screenshot, or another deterministic saved transcript produced by the CLI itself.

Guard the boundary between the shell and the target CLI carefully:

- A shell prompt such as `root@...#` means the target CLI is not currently receiving chat input. Never paste natural-language text into that shell prompt unless it is deliberately quoted as an argument to a shell command.
- If launching a CLI by name can fail, use a shell-safe fallback command and wait for the CLI's own prompt before sending the user's natural-language message.
- After a launch failure such as `command not found`, do not continue by sending the chat message. Start the fallback CLI command or report the blocker.
- A prompt like `>`, `Implement {feature}`, or a CLI-specific input box inside the terminal is different from a shell prompt. Only then should `paste-text "natural language"` followed by `key Return` be used as chat input.

Example for a nested CLI-agent smoke test:

```bash
DESKTOP=/a0/plugins/_desktop/skills/linux-desktop/scripts/desktopctl.sh
$DESKTOP focus "Terminal"
$DESKTOP paste-text 'TARGET_CLI="example-cli-agent"; FALLBACK_CMD=""; if command -v "$TARGET_CLI" >/dev/null 2>&1; then "$TARGET_CLI"; elif [ -n "$FALLBACK_CMD" ]; then sh -lc "$FALLBACK_CMD"; else echo "CLI agent not found: $TARGET_CLI"; fi'
$DESKTOP key Return
$DESKTOP observe --json --screenshot
# Verify the screenshot shows the target CLI prompt, not a shell prompt, before sending natural language:
$DESKTOP paste-text 'Reply with exactly the requested smoke-test token.'
$DESKTOP key Return
$DESKTOP observe --json --screenshot
```

## Desktop Locations

The Desktop exposes stable folders for common user work:

- `Workdir` -> configured Agent Zero workdir (default `/a0/usr/workdir`)
- `Projects` -> `/a0/usr/projects`
- `Skills` -> `/a0/usr/skills`
- `Agents` -> `/a0/usr/agents`
- `Downloads` -> `/a0/usr/downloads`

Use these folders when the user asks to inspect or manipulate project files, skills, agent profiles, or downloaded artifacts from the GUI.

## App Map

- `LibreOffice Writer`: ODT word processing and DOCX compatibility layout.
- `LibreOffice Calc`: ODS spreadsheets, formulas, tables, charts, and XLSX compatibility.
- `LibreOffice Impress`: ODP presentations, slide polish, and PPTX compatibility.
- `Workdir`: graphical file management with Thunar at the configured Agent Zero workdir (default `/a0/usr/workdir`).
- `Terminal`: shell work inside the Agent Zero runtime.
- `Settings`: XFCE system settings.

## Practical Rules

- Keep installs inside normal plugin hook or image install flows; do not install packages ad hoc just to complete one desktop action.
- The persistent Desktop can be running in the background while the canvas stays closed; that is expected and still respects user ownership of the visible UI.
- Do not treat closing a document tab as closing the whole Desktop. The Desktop is persistent while Agent Zero is running.
- Save before sync or final verification when the GUI app has edited a file.
- If a GUI action is flaky, switch to structured file editing for content and return to the Desktop only for visual confirmation.
- For live Calc edits that the user should see immediately, prefer `desktopctl.sh calc-set-cell FILE SHEET CELL VALUE`.
- For enterprise workflows, leave printing available.
