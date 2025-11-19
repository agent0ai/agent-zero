#!/bin/bash
set -e

# install playwright - moved to install A0
# bash /ins/install_playwright.sh "$@"

# searxng - moved to base image
# bash /ins/install_searxng.sh "$@"

# Install Node.js LTS and core Electron runtime dependencies
apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && npm install -g yarn \
    && apt-get install -y xvfb \
    && apt-get install -y \
        libgtk-3-0 \
        libnotify4 \
        libnss3 \
        libxss1 \
        libasound2t64 \
        libgbm1 \
        fonts-liberation \
        libayatana-appindicator3-1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
