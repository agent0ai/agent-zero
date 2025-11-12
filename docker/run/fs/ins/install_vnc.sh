#!/bin/bash
# Install VNC server and noVNC for remote browser control
# This allows users to manually interact with the browser when the agent pauses

set -e

echo "Installing VNC server and noVNC..."

# Update package list
apt-get update

# Install Xvfb (X virtual framebuffer) for headless display
# Install x11vnc for VNC server
# Install websockify for WebSocket support (required by noVNC)
# Install novnc for web-based VNC client
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    xvfb \
    x11vnc \
    websockify \
    novnc \
    net-tools \
    procps

# Create VNC directory for password and configuration
mkdir -p /root/.vnc

# Set default VNC password (will be overridden by environment variable)
# Using x11vnc password format - pass password as argument
x11vnc -storepasswd "agent-zero" /root/.vnc/passwd 2>/dev/null || true

# Create symlink for noVNC to easily find it
# noVNC is typically installed in /usr/share/novnc
if [ -d "/usr/share/novnc" ]; then
    ln -sf /usr/share/novnc /opt/novnc
elif [ -d "/usr/share/noVNC" ]; then
    ln -sf /usr/share/noVNC /opt/novnc
fi

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✓ VNC server and noVNC installed"
echo "  - Xvfb for virtual display"
echo "  - x11vnc for VNC server"
echo "  - noVNC for web-based access"
echo "  - Default VNC password: agent-zero (change via VNC_PASSWORD env var)"
