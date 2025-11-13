#!/bin/bash
# VNC Server Startup Script
# Starts Xvfb, x11vnc, and noVNC for remote browser control
# Can be safely run multiple times (idempotent)

set -e

echo "========================================"
echo "Agent Zero - VNC Server Setup"
echo "========================================"

# Configuration from environment variables with defaults
VNC_DISPLAY="${VNC_DISPLAY:-:99}"
VNC_RESOLUTION="${VNC_RESOLUTION:-1920x1080x24}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
VNC_PASSWORD="${VNC_PASSWORD:-agent-zero}"

# Extract display number (e.g., :99 -> 99)
DISPLAY_NUM=$(echo $VNC_DISPLAY | tr -d ':')

echo "Configuration:"
echo "  Display: $VNC_DISPLAY"
echo "  Resolution: $VNC_RESOLUTION"
echo "  VNC Port: $VNC_PORT"
echo "  noVNC Port: $NOVNC_PORT"
echo "========================================"

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to kill existing VNC processes
cleanup_vnc() {
    echo "Cleaning up existing VNC processes..."
    pkill -f "Xvfb $VNC_DISPLAY" || true
    pkill -f "x11vnc.*$VNC_DISPLAY" || true
    pkill -f "websockify.*$NOVNC_PORT" || true
    # Remove stale lock file (socket file removal may fail, but that's OK)
    rm -f /tmp/.X${DISPLAY_NUM}-lock 2>/dev/null || true
    rm -f /tmp/.X11-unix/X${DISPLAY_NUM} 2>/dev/null || true
    sleep 1
}

# Check if already running - if so, skip to monitoring
if is_running "Xvfb $VNC_DISPLAY" && is_running "x11vnc.*$VNC_DISPLAY" && is_running "websockify.*$NOVNC_PORT"; then
    echo "✓ VNC server already running"
    echo "  - Xvfb on display $VNC_DISPLAY"
    echo "  - x11vnc on port $VNC_PORT"
    echo "  - noVNC web client on port $NOVNC_PORT"
    echo "========================================"

    # Skip to monitoring instead of exiting
    # Find PIDs of running processes
    XVFB_PID=$(pgrep -f "Xvfb $VNC_DISPLAY" | head -1)
    X11VNC_PID=$(pgrep -f "x11vnc.*$VNC_DISPLAY" | head -1)
    WEBSOCKIFY_PID=$(pgrep -f "websockify.*$NOVNC_PORT" | head -1)

    # Create status file
    mkdir -p /tmp/vnc
    echo "DISPLAY=$VNC_DISPLAY" > /tmp/vnc/status
    echo "VNC_PORT=$VNC_PORT" >> /tmp/vnc/status
    echo "NOVNC_PORT=$NOVNC_PORT" >> /tmp/vnc/status
    echo "XVFB_PID=$XVFB_PID" >> /tmp/vnc/status
    echo "X11VNC_PID=$X11VNC_PID" >> /tmp/vnc/status
    echo "WEBSOCKIFY_PID=$WEBSOCKIFY_PID" >> /tmp/vnc/status
    echo "READY=true" >> /tmp/vnc/status

    # Jump to monitoring loop
    # Use a label/goto simulation by setting a flag
    SKIP_STARTUP=true
else
    SKIP_STARTUP=false
fi

# Only run startup if not skipping
if [ "$SKIP_STARTUP" = "false" ]; then

# Clean up any partial VNC processes
cleanup_vnc

# Create VNC password file
mkdir -p /root/.vnc
echo "Setting VNC password..."
x11vnc -storepasswd "$VNC_PASSWORD" /root/.vnc/passwd 2>/dev/null || {
    echo "⚠️  Failed to set VNC password, trying alternative method..."
    # Alternative method using printf and stdin
    printf "%s\n%s\n" "$VNC_PASSWORD" "$VNC_PASSWORD" | x11vnc -storepasswd /root/.vnc/passwd 2>/dev/null || {
        echo "⚠️  Password setup failed, VNC may not be accessible"
    }
}

# Start Xvfb (X virtual framebuffer)
echo "Starting Xvfb on display $VNC_DISPLAY..."
Xvfb $VNC_DISPLAY -screen 0 $VNC_RESOLUTION -ac +extension GLX +render -noreset > /tmp/xvfb.log 2>&1 &
XVFB_PID=$!

# Wait for Xvfb to be ready
sleep 2

if ! is_running "Xvfb $VNC_DISPLAY"; then
    echo "❌ Failed to start Xvfb"
    cat /tmp/xvfb.log
    exit 1
fi

echo "✓ Xvfb started successfully (PID: $XVFB_PID)"

# Start x11vnc (VNC server)
echo "Starting x11vnc on port $VNC_PORT..."
x11vnc \
    -display $VNC_DISPLAY \
    -rfbport $VNC_PORT \
    -rfbauth /root/.vnc/passwd \
    -forever \
    -shared \
    -noxdamage \
    -ncache 10 \
    -ncache_cr \
    -localhost \
    -quiet \
    > /tmp/x11vnc.log 2>&1 &
X11VNC_PID=$!

# Wait for x11vnc to be ready
sleep 2

if ! is_running "x11vnc.*$VNC_DISPLAY"; then
    echo "❌ Failed to start x11vnc"
    cat /tmp/x11vnc.log
    exit 1
fi

echo "✓ x11vnc started successfully (PID: $X11VNC_PID)"

# Find noVNC installation
NOVNC_PATH=""
if [ -d "/opt/novnc" ]; then
    NOVNC_PATH="/opt/novnc"
elif [ -d "/usr/share/novnc" ]; then
    NOVNC_PATH="/usr/share/novnc"
elif [ -d "/usr/share/noVNC" ]; then
    NOVNC_PATH="/usr/share/noVNC"
fi

if [ -z "$NOVNC_PATH" ]; then
    echo "⚠️  noVNC not found, VNC server running but no web access"
    echo "   You can still connect with a VNC client on port $VNC_PORT"
    echo "========================================"
    exit 0
fi

# Start websockify for noVNC
echo "Starting noVNC web client on port $NOVNC_PORT..."
websockify \
    --web=$NOVNC_PATH \
    $NOVNC_PORT \
    localhost:$VNC_PORT \
    > /tmp/websockify.log 2>&1 &
WEBSOCKIFY_PID=$!

# Wait for websockify to be ready
sleep 2

if ! is_running "websockify.*$NOVNC_PORT"; then
    echo "⚠️  Failed to start websockify/noVNC"
    cat /tmp/websockify.log
    echo "   VNC server is running, but web access unavailable"
else
    echo "✓ noVNC started successfully (PID: $WEBSOCKIFY_PID)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 VNC Server Ready!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Web Access: http://localhost:$NOVNC_PORT/vnc.html"
    echo "  VNC Client: localhost:$DISPLAY_NUM (port $VNC_PORT)"
    echo "  Password: $VNC_PASSWORD"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo "========================================"

# Create status file for other scripts to check (only if we started VNC)
if [ "$SKIP_STARTUP" = "false" ]; then
    mkdir -p /tmp/vnc
    echo "DISPLAY=$VNC_DISPLAY" > /tmp/vnc/status
    echo "VNC_PORT=$VNC_PORT" >> /tmp/vnc/status
    echo "NOVNC_PORT=$NOVNC_PORT" >> /tmp/vnc/status
    echo "XVFB_PID=$XVFB_PID" >> /tmp/vnc/status
    echo "X11VNC_PID=$X11VNC_PID" >> /tmp/vnc/status
    echo "WEBSOCKIFY_PID=$WEBSOCKIFY_PID" >> /tmp/vnc/status
    echo "READY=true" >> /tmp/vnc/status
fi

# Close the startup section
fi

# VNC is now running in the background
# Exit the script so initialize.sh can continue
exit 0
