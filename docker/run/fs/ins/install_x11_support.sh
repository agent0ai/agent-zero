#!/bin/bash
# Install X11 and GUI support for browser display
# This allows Chromium to display on the host machine via X11 forwarding

set -e

echo "Installing X11 and GUI support for browser display..."

# Update package list
apt-get update

# Install X11 libraries and dependencies for GUI applications
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libxcb-dri3-0 \
    libxcb-shm0 \
    libxshmfence1 \
    libgbm1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libdbus-1-3 \
    fonts-liberation \
    xdg-utils

# Install additional fonts for better browser rendering
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✓ X11 and GUI support installed"
