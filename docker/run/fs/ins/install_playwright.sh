#!/bin/bash
set -e

# The pinned Python package is already materialized by the main requirements
# install. Keep only Chromium and its operating-system runtime dependencies here.
export PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

# install chromium with dependencies
apt-get update
apt-get install -y --no-install-recommends \
    fonts-unifont libnss3 libnspr4 libatk1.0-0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libatk-bridge2.0-0 libcups2
rm -rf /var/lib/apt/lists/*
depfix run -m patchright install chromium --no-shell
