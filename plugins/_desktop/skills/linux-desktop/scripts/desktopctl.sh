#!/usr/bin/env bash
set -euo pipefail

SESSION="${A0_DESKTOP_SESSION:-agent-zero-desktop}"
BASE_DIR="${A0_BASE_DIR:-/a0}"
PROFILE_DIR="${A0_DESKTOP_PROFILE:-$BASE_DIR/usr/plugins/_desktop/profiles/$SESSION}"
MANIFEST="${A0_DESKTOP_MANIFEST:-$BASE_DIR/usr/plugins/_desktop/sessions/$SESSION.json}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_STATE_HELPER="$SCRIPT_DIR/../../../helpers/desktop_state.py"
DESKTOP_STATE_PYTHON="${A0_DESKTOP_STATE_PYTHON:-$(command -v /usr/bin/python3 || command -v python3 || true)}"

display_from_manifest() {
  if [ ! -f "$MANIFEST" ] || ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  python3 - "$MANIFEST" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        value = json.load(handle).get("display", "")
except Exception:
    value = ""
if value != "":
    print(value)
PY
}

DISPLAY_VALUE="${A0_DESKTOP_DISPLAY:-$(display_from_manifest || true)}"
DISPLAY_VALUE="${DISPLAY_VALUE:-120}"
case "$DISPLAY_VALUE" in
  :*) export DISPLAY="$DISPLAY_VALUE" ;;
  *) export DISPLAY=":$DISPLAY_VALUE" ;;
esac

export XAUTHORITY="${A0_DESKTOP_XAUTHORITY:-$PROFILE_DIR/.Xauthority}"
export HOME="${A0_DESKTOP_HOME:-$PROFILE_DIR}"
export A0_DESKTOP_SESSION="$SESSION"
export A0_DESKTOP_MANIFEST="$MANIFEST"
export A0_DESKTOP_PROFILE="$PROFILE_DIR"
export A0_DESKTOP_DISPLAY="$DISPLAY"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-XFCE}"

command_name="${1:-help}"
shift || true

usage() {
  cat <<'EOF'
Usage: desktopctl.sh <command> [args]

Commands:
  env                         Print the X11 environment used for the Desktop.
  check                       Verify that xdotool can reach the Desktop display.
  state --json [--screenshot] [--context-id ID]
                              Return structured Desktop state as JSON.
  observe --json [--screenshot] [--context-id ID]
                              Return structured state, optionally with a fresh screenshot.
  screenshot [PATH] [--context-id ID]
                              Capture the Desktop to PATH, or to the default screenshot directory.
  active-window               Print the active window name.
  geometry PATTERN            Print the first matching visible window geometry.
  wait-window PATTERN         Wait for a visible matching window and print its id.
  location                    Print the current X pointer location.
  windows [PATTERN]           List visible window names matching PATTERN.
  focus PATTERN               Focus the first visible window matching PATTERN.
  scroll DIRECTION [UNITS]    Scroll up, down, left, or right; UNITS defaults to 5 clicks.
  drag X1 Y1 X2 Y2            Drag from X1,Y1 to X2,Y2 in Desktop coordinates.
  right-click X Y             Move and right-click at X,Y in Desktop coordinates.
  paste-text TEXT             Put TEXT on the Desktop clipboard and paste it with an app-native shortcut.
  sequence FILE|-             Run a newline-delimited command sequence.
  key KEY...                  Send one or more xdotool key names.
  type TEXT                   Type text into the focused window.
  click X Y                   Move and click at X,Y in Desktop coordinates.
  dblclick X Y                Move and double-click at X,Y in Desktop coordinates.
  launch APP                  Launch writer, calc, impress, terminal, settings, or workdir.
  open-path [PATH]            Open PATH in Thunar, defaulting to /a0/usr/workdir.
  calc-set-cell FILE SHEET CELL VALUE
                              Open FILE in visible Calc, set SHEET!CELL, save, and verify.
  save                        Send Ctrl+S to the focused app.
EOF
}

require_xdotool() {
  if ! command -v xdotool >/dev/null 2>&1; then
    echo "xdotool is required for Desktop control." >&2
    exit 2
  fi
}

ensure_display() {
  require_xdotool
  if ! xdotool getmouselocation >/dev/null 2>&1; then
    echo "Desktop X display is not reachable. Open the Desktop surface first." >&2
    exit 2
  fi
}

desktop_state() {
  if [ ! -f "$DESKTOP_STATE_HELPER" ]; then
    echo "Desktop state helper not found: $DESKTOP_STATE_HELPER" >&2
    exit 2
  fi
  "$DESKTOP_STATE_PYTHON" "$DESKTOP_STATE_HELPER" "$@"
}

run_detached() {
  ( "$@" >/tmp/a0-desktopctl.log 2>&1 & )
}

close_blocking_dialogs() {
  require_xdotool
  for title in "Document in Use"; do
    window_ids="$(xdotool search --onlyvisible --name "$title" 2>/dev/null || true)"
    printf '%s\n' "$window_ids" | while read -r window_id; do
      [ -n "$window_id" ] && xdotool windowclose "$window_id" >/dev/null 2>&1 || true
    done
  done
}

first_window() {
  pattern="$1"
  xdotool search --onlyvisible --name "$pattern" 2>/dev/null | head -n 1 || true
}

active_window_id() {
  xdotool getactivewindow 2>/dev/null || true
}

active_window_class() {
  window_id="$(active_window_id)"
  if [ -z "$window_id" ]; then
    return 0
  fi
  if command -v xprop >/dev/null 2>&1; then
    xprop -id "$window_id" WM_CLASS 2>/dev/null | awk -F'"' '/WM_CLASS/ { print $(NF - 1); exit }'
  fi
}

active_window_class_lower() {
  active_window_class | tr '[:upper:]' '[:lower:]'
}

active_window_is_terminal() {
  window_class="$(active_window_class_lower)"
  case "$window_class" in
    *terminal*|xterm|uxterm|rxvt|urxvt|kitty|alacritty|wezterm|konsole)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

paste_key_for_active_window() {
  printf '%s\n' "${A0_DESKTOP_PASTE_KEY:-ctrl+v}"
}

window_geometry() {
  window_id="$1"
  if command -v xwininfo >/dev/null 2>&1; then
    xwininfo -id "$window_id" 2>/dev/null | awk '
      /Absolute upper-left X:/ { x=$4 }
      /Absolute upper-left Y:/ { y=$4 }
      /Width:/ { w=$2 }
      /Height:/ { h=$2 }
      END { if (w != "") printf "X=%s\nY=%s\nWIDTH=%s\nHEIGHT=%s\n", x, y, w, h }
    '
  else
    xdotool getwindowgeometry --shell "$window_id"
  fi
}

wait_window() {
  pattern="$1"
  timeout="${2:-15}"
  end=$((SECONDS + timeout))
  while [ "$SECONDS" -le "$end" ]; do
    window_id="$(first_window "$pattern")"
    if [ -n "$window_id" ]; then
      printf '%s\n' "$window_id"
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for visible window: $pattern" >&2
  return 1
}

scroll_desktop() {
  direction="$1"
  units="${2:-5}"
  case "$direction" in
    up) button=4 ;;
    down) button=5 ;;
    left) button=6 ;;
    right) button=7 ;;
    *)
      echo "scroll direction must be up, down, left, or right." >&2
      exit 2
      ;;
  esac
  xdotool click --repeat "$units" "$button"
}

paste_text() {
  text="$*"
  if active_window_is_terminal; then
    xdotool type --delay "${A0_DESKTOP_PASTE_TYPE_DELAY_MS:-${A0_DESKTOP_TYPE_DELAY_MS:-4}}" -- "$text"
    return
  fi
  if command -v xclip >/dev/null 2>&1; then
    printf '%s' "$text" | xclip -selection clipboard
    xdotool key --clearmodifiers "$(paste_key_for_active_window)"
    return
  fi
  xdotool type --delay "${A0_DESKTOP_TYPE_DELAY_MS:-1}" -- "$text"
}

run_sequence_line() {
  line="$1"
  [ -z "$line" ] && return 0
  case "$line" in
    \#*) return 0 ;;
  esac
  # shellcheck disable=SC2086
  "$0" $line
}

run_sequence() {
  source_file="$1"
  if [ "$source_file" = "-" ]; then
    while IFS= read -r line; do
      run_sequence_line "$line"
    done
    return
  fi
  if [ ! -f "$source_file" ]; then
    echo "sequence requires an existing FILE or - for stdin." >&2
    exit 2
  fi
  while IFS= read -r line || [ -n "$line" ]; do
    run_sequence_line "$line"
  done < "$source_file"
}

launch_app() {
  app="${1:-}"
  soffice="${SOFFICE:-$(command -v soffice || true)}"
  soffice="${soffice:-soffice}"
  case "$app" in
    writer)
      run_detached "$soffice" --norestore --nofirststartwizard --nolockcheck "-env:UserInstallation=file://$HOME" --writer
      ;;
    calc|spreadsheet)
      run_detached "$soffice" --norestore --nofirststartwizard --nolockcheck "-env:UserInstallation=file://$HOME" --calc
      ;;
    impress|presentation)
      run_detached "$soffice" --norestore --nofirststartwizard --nolockcheck "-env:UserInstallation=file://$HOME" --impress
      ;;
    terminal)
      run_detached xfce4-terminal --working-directory=/a0/usr/workdir
      ;;
    settings)
      run_detached xfce4-settings-manager
      ;;
    workdir|files|file-manager)
      run_detached thunar /a0/usr/workdir
      ;;
    *)
      echo "Unknown app: ${app:-<empty>}" >&2
      echo "Expected: writer, calc, impress, terminal, settings, or workdir." >&2
      exit 2
      ;;
  esac
}

case "$command_name" in
  help|-h|--help)
    usage
    ;;
  env)
    printf 'export DISPLAY=%q\n' "$DISPLAY"
    printf 'export XAUTHORITY=%q\n' "$XAUTHORITY"
    printf 'export HOME=%q\n' "$HOME"
    ;;
  check)
    ensure_display
    xdotool getmouselocation --shell
    ;;
  state)
    if [ "${1:-}" != "--json" ]; then
      echo "state currently requires --json." >&2
      exit 2
    fi
    shift
    desktop_state state --json "$@"
    ;;
  observe)
    if [ "${1:-}" != "--json" ]; then
      echo "observe currently requires --json." >&2
      exit 2
    fi
    shift
    desktop_state observe --json "$@"
    ;;
  screenshot)
    if [ "${1:-}" = "--json" ]; then
      shift
      desktop_state screenshot --json "$@"
    elif [ "$#" -gt 0 ]; then
      desktop_state screenshot "$@"
    else
      desktop_state screenshot
    fi
    ;;
  active-window)
    ensure_display
    window_id="$(active_window_id)"
    if [ -z "$window_id" ]; then
      echo "No active window." >&2
      exit 1
    fi
    xdotool getwindowname "$window_id"
    ;;
  geometry)
    ensure_display
    pattern="${1:?geometry requires a window name pattern}"
    window_id="$(first_window "$pattern")"
    if [ -z "$window_id" ]; then
      echo "No visible window matched: $pattern" >&2
      exit 1
    fi
    window_geometry "$window_id"
    ;;
  wait-window)
    ensure_display
    pattern="${1:?wait-window requires a window name pattern}"
    wait_window "$pattern" "${2:-15}"
    ;;
  location)
    ensure_display
    xdotool getmouselocation --shell
    ;;
  windows)
    ensure_display
    pattern="${1:-.}"
    xdotool search --onlyvisible --name "$pattern" getwindowname %@ 2>/dev/null || true
    ;;
  focus)
    ensure_display
    pattern="${1:?focus requires a window name pattern}"
    window_id="$(first_window "$pattern")"
    if [ -z "$window_id" ]; then
      echo "No visible window matched: $pattern" >&2
      exit 1
    fi
    xdotool windowactivate --sync "$window_id"
    ;;
  scroll)
    ensure_display
    scroll_desktop "${1:?scroll requires DIRECTION}" "${2:-5}"
    ;;
  drag)
    ensure_display
    x1="${1:?drag requires X1}"
    y1="${2:?drag requires Y1}"
    x2="${3:?drag requires X2}"
    y2="${4:?drag requires Y2}"
    xdotool mousemove --sync "$x1" "$y1" mousedown 1 mousemove --sync "$x2" "$y2" mouseup 1
    ;;
  right-click)
    ensure_display
    x="${1:?right-click requires X}"
    y="${2:?right-click requires Y}"
    xdotool mousemove --sync "$x" "$y" click 3
    ;;
  paste-text)
    ensure_display
    if [ "$#" -eq 0 ]; then
      echo "paste-text requires TEXT." >&2
      exit 2
    fi
    paste_text "$@"
    ;;
  sequence)
    source_file="${1:?sequence requires FILE or -}"
    run_sequence "$source_file"
    ;;
  key)
    ensure_display
    if [ "$#" -eq 0 ]; then
      echo "key requires at least one xdotool key name." >&2
      exit 2
    fi
    xdotool key --clearmodifiers "$@"
    ;;
  type)
    ensure_display
    text="$*"
    xdotool type --delay "${A0_DESKTOP_TYPE_DELAY_MS:-1}" -- "$text"
    ;;
  click)
    ensure_display
    x="${1:?click requires X}"
    y="${2:?click requires Y}"
    xdotool mousemove --sync "$x" "$y" click 1
    ;;
  dblclick)
    ensure_display
    x="${1:?dblclick requires X}"
    y="${2:?dblclick requires Y}"
    xdotool mousemove --sync "$x" "$y" click --repeat 2 --delay "${A0_DESKTOP_DBLCLICK_DELAY_MS:-150}" 1
    ;;
  launch)
    ensure_display
    launch_app "${1:-}"
    ;;
  open-path)
    ensure_display
    path="${1:-/a0/usr/workdir}"
    run_detached thunar "$path"
    ;;
  calc-set-cell)
    ensure_display
    file="${1:?calc-set-cell requires FILE}"
    sheet="${2:?calc-set-cell requires SHEET}"
    cell="${3:?calc-set-cell requires CELL}"
    shift 3
    if [ "$#" -eq 0 ]; then
      echo "calc-set-cell requires VALUE." >&2
      exit 2
    fi
    close_blocking_dialogs
    export PYTHONPATH="${PYTHONPATH:-/usr/lib/python3/dist-packages:/usr/lib/libreoffice/program:}"
    python3 "$SCRIPT_DIR/calc_set_cell.py" "$file" "$sheet" "$cell" "$@"
    ;;
  save)
    ensure_display
    xdotool key --clearmodifiers ctrl+s
    ;;
  *)
    echo "Unknown command: $command_name" >&2
    usage >&2
    exit 2
    ;;
esac
