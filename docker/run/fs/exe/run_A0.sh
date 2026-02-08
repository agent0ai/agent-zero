#!/bin/bash

. "/ins/setup_venv.sh" "$@"
. "/ins/copy_A0.sh" "$@"

# === Playwright Browser Setup ===
# Auto-install Playwright browsers if not present (survives container restarts)
# Only installs Chromium by default; add firefox/webkit if needed
PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}"
if command -v playwright &> /dev/null; then
    if [ ! -d "$PLAYWRIGHT_BROWSERS_PATH/chromium"* ] 2>/dev/null; then
        echo "Installing Playwright browsers..."
        playwright install chromium 2>/dev/null || echo "WARNING: Playwright browser install failed"
    else
        echo "Playwright browsers already installed"
    fi
fi

python /a0/prepare.py --dockerized=true
# python /a0/preload.py --dockerized=true # no need to run preload if it's done during container build

echo "Starting A0..."
exec python /a0/run_ui.py \
    --dockerized=true \
    --port=80 \
    --host="0.0.0.0"
    # --code_exec_ssh_enabled=true \
    # --code_exec_ssh_addr="localhost" \
    # --code_exec_ssh_port=22 \
    # --code_exec_ssh_user="root" \
    # --code_exec_ssh_pass="toor"
