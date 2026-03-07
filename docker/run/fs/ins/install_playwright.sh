#!/bin/bash
set -e

# activate venv
. "/ins/setup_venv.sh" "$@"

# install playwright if not installed (should be from requirements.txt)
uv pip install playwright

# set PW installation path to /a0/tmp/playwright
export PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright

# install chromium with dependencies
apt-get update
for attempt in 1 2 3; do
    if apt-get install -y --fix-missing fonts-unifont libnss3 libnspr4 libatk1.0-0 libatspi2.0-0 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libcups2; then
        break
    fi
    if [ "$attempt" -eq 3 ]; then
        echo "Failed to install Playwright apt dependencies after $attempt attempts"
        exit 1
    fi
    echo "Apt dependency install failed (attempt $attempt/3), refreshing package indexes and retrying..."
    apt-get update
    sleep 2
done
playwright install chromium --only-shell
