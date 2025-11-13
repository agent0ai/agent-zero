#!/bin/bash
# Automatic X11 display setup checker
# Runs on container startup to verify display forwarding
# No user interaction required - fully automatic

set -e

echo "========================================"
echo "Agent Zero - Display Setup Check"
echo "========================================"

# Detect if running on macOS host
IS_MACOS=false
if [ -f /tmp/.X11-unix ] || [ "$DISPLAY" = "host.docker.internal:0" ]; then
    IS_MACOS=true
fi

# Check if DISPLAY is set
if [ -z "$DISPLAY" ]; then
    echo "⚠️  No display configured (headless mode)"
    echo "   Browser will run in headless mode (invisible)"
    echo ""
    echo "To enable visible browser on macOS:"
    echo "  1. Install XQuartz: https://www.xquartz.org/"
    echo "  2. Start XQuartz and restart Agent Zero"
    exit 0
fi

# Display is configured - verify X11 libraries
echo "✓ Display configured: $DISPLAY"

# Check if X11 libraries are installed
if ! dpkg -l | grep -q libx11-6; then
    echo "Installing X11 libraries for browser display..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        libx11-6 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
        libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
        libxtst6 libgbm1 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libgtk-3-0 libnspr4 libnss3 \
        2>&1 | grep -v "^Reading" | grep -v "^Building" || true
fi

echo "✓ X11 libraries installed"

# Test X11 connection
if [ "$IS_MACOS" = true ]; then
    echo "Testing X11 connection to macOS host..."

    # Try to connect to X11
    timeout 2 xdpyinfo -display "$DISPLAY" > /dev/null 2>&1 && {
        echo "✓ X11 connection successful"
        echo "✓ Browser will appear on your screen"
        exit 0
    } || {
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  Cannot connect to X11 display"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "To see the browser window, you need XQuartz:"
        echo ""
        echo "  1. Download and install XQuartz:"
        echo "     https://www.xquartz.org/"
        echo ""
        echo "  2. Log out and log back in (required!)"
        echo ""
        echo "  3. Allow Docker connections:"
        echo "     xhost +localhost"
        echo ""
        echo "  4. Restart Agent Zero:"
        echo "     cd docker/run && docker-compose restart"
        echo ""
        echo "For now, browser will run in headless mode."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        exit 0
    }
fi

echo "✓ Display setup complete"
echo "========================================"
