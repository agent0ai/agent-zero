#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required."
  exit 1
fi

PIP_USER_FLAG=""

# Prefer a virtualenv, but fall back gracefully if venv isn't available.
if python3 -m venv .venv >/dev/null 2>&1 && [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Warning: could not create .venv (python venv module may be missing)."
  echo "Falling back to user-level installs. For a clean venv, install python3-venv and re-run."
  PIP_USER_FLAG="--user"
fi

python3 -m pip install ${PIP_USER_FLAG} --upgrade pip >/dev/null || true
#
# Install *minimal* dependencies for the Survey Helper only.
# (Installing the full Agent Zero requirements may require extra build tooling on some systems.)
#
python3 -m pip install ${PIP_USER_FLAG} "beautifulsoup4==4.12.3" "playwright==1.49.0"

# Ensure Playwright browser is installed (Chromium)
python3 -m playwright install chromium

if python3 -c "import tkinter" >/dev/null 2>&1; then
  # If there's no display server, tkinter will raise a TclError at runtime.
  if [[ -z "${DISPLAY:-}" ]]; then
    echo "Error: no DISPLAY detected (headless environment)."
    echo "To run the GUI, run this on a machine with a desktop session, or use the CLI fallback below."
    echo ""
    echo "CLI fallback:"
    echo "  SURVEY_HELPER_MODE=cli bash scripts/start_survey_helper.sh \"https://example.com\""
    if [[ "${SURVEY_HELPER_MODE:-}" == "cli" ]]; then
      if [[ "${1:-}" == "" ]]; then
        echo "Please provide a URL as the first argument in CLI mode."
        exit 1
      fi
      python3 run_survey_helper_cli.py "$1"
      exit 0
    fi
    exit 1
  fi

  # Sanity-check that tkinter can actually connect to the display.
  if python3 -c "import tkinter as tk; r=tk.Tk(); r.destroy()" >/dev/null 2>&1; then
    echo "Starting Survey Helper GUI..."
    python3 run_survey_helper_gui.py
  else
    echo "Error: tkinter is installed but cannot connect to your display (\$DISPLAY=${DISPLAY})."
    echo "If you're in a server/VM, you likely need X forwarding or to run on a desktop machine."
    echo ""
    echo "CLI fallback:"
    echo "  SURVEY_HELPER_MODE=cli bash scripts/start_survey_helper.sh \"https://example.com\""
    if [[ "${SURVEY_HELPER_MODE:-}" == "cli" ]]; then
      if [[ "${1:-}" == "" ]]; then
        echo "Please provide a URL as the first argument in CLI mode."
        exit 1
      fi
      python3 run_survey_helper_cli.py "$1"
      exit 0
    fi
    exit 1
  fi
else
  echo "Error: tkinter is not installed for your Python."
  echo "To enable the GUI, install it and re-run."
  echo "Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y python3-tk"
  echo ""
  echo "CLI fallback:"
  echo "  SURVEY_HELPER_MODE=cli bash scripts/start_survey_helper.sh \"https://example.com\""
  if [[ "${SURVEY_HELPER_MODE:-}" == "cli" ]]; then
    if [[ "${1:-}" == "" ]]; then
      echo "Please provide a URL as the first argument in CLI mode."
      exit 1
    fi
    python3 run_survey_helper_cli.py "$1"
  else
    exit 1
  fi
fi

