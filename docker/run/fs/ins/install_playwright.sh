#!/bin/bash
set -e

# activate venv
. "/ins/setup_venv.sh" "$@"

# set PW installation path to temporary Browser runtime storage
export PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

# preinstall Chromium for fresh images; the Browser hook also reconciles self-updated installs
apt-get install -y fonts-unifont libnss3 libnspr4 libatk1.0-0 libatspi2.0-0 libxcomposite1 libxdamage1 libatk-bridge2.0-0 libcups2
patchright install chromium --no-shell
